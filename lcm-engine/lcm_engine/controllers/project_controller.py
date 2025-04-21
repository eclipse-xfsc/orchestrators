import binascii
import logging
from base64 import b64decode
from io import StringIO
from pathlib import Path
from traceback import print_exc

import connexion
from flask import current_app, send_file
from lcm_engine.controllers.helper import AuthError, authorize_everything
from lcm_engine.db_models.models import db
from lcm_engine.db_models.project import Project as DBProject
from lcm_engine.db_models.user_workspace import \
    UserWorkspace as DBUserWorkspace
from lcm_engine.db_models.workspace import Workspace as DBWorkspace
from lcm_engine.k8sops.lcm_service import (
    LCMServiceDeployer,
    can_ping_lcm_service,
    get_lcm_service_status_phase,
    construct_namespace_name,
    undeploy_lcm_service,
    create_debug_zip
)
from lcm_engine.models.connectivity_health import ConnectivityHealth
from lcm_engine.models.container_health import ContainerHealth
from lcm_engine.models.entity_creation_status import \
    EntityCreationStatus  # noqa: E501
from lcm_engine.models.entity_reference import EntityReference  # noqa: E501
from lcm_engine.models.project import Project  # noqa: E501
from lcm_engine.models.project_health import ProjectHealth  # noqa: E501

# FIXME: read from config
KNOWN_PROJECT_KINDS = [
    "si.xlab.lcm-service.tosca",
    "si.xlab.lcm-service.terraform"
]


def create_workspace_project(workspace_id, project=None):  # noqa: E501
    """Create a new project in the workspace (async)

    Secrets applied to the workspace the project is in are only applied on creation. To modify secrets, create a new project.  # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project: Project specification object
    :type project: dict | bytes

    :rtype: Union[EntityReference, Tuple[EntityReference, int], Tuple[EntityReference, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        project = Project.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers, workspace_id=workspace_id
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    if project.kind not in KNOWN_PROJECT_KINDS:
        supported_project_kinds = ", ".join(KNOWN_PROJECT_KINDS)
        msg = (
            f"Project kind {project.kind} is not one of supported kinds: "
            f"{supported_project_kinds}."
        )
        logging.error(msg)
        return dict(msg=msg), 400

    project_with_same_name = db.session.execute(
        db.select(DBProject).filter_by(name=project.name)
        .join(DBWorkspace)
        .join(DBUserWorkspace)
        .filter(DBUserWorkspace.is_owner is True)
        .filter(DBUserWorkspace.user_id == user.id)
        .filter(DBWorkspace.id == workspace_id)
    ).first()

    if project_with_same_name is not None:
        msg = (
            f"Project with name {project.name} already exists "
            f"for the current owner in workspace ID {workspace_id}."
        )
        logging.error(msg)
        return dict(msg=msg), 400

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id} exists."
    )

    try:
        binary_csar = b64decode(project.csar)
    except binascii.Error as err:
        logging.error(err)
        return dict(msg=err.msg), 400

    logging.info(f"Creating project {project.name}.")
    db_project = DBProject(
        name=project.name,
        container_id="unknown",
        available=False,
        csar=binary_csar,
        workspace=db_workspace,
        kind=project.kind,
    )

    try:
        db.session.add(db_project)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    api_secrets = []
    for sw in db_workspace.secrets:
        api_secrets.append(sw.secret.to_api_model(disclose_contents=True))

    if project.kind == "si.xlab.lcm-service.tosca":
        image = "ghcr.io/xlab-si/xopera-api:0.5.4"
    elif project.kind == "si.xlab.lcm-service.terraform":
        image = "registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api:v0.2.1"

    project_kind_short = project.kind.split(".")[-1]

    cert_secret_name = current_app.config["LCM_ENGINE_CERTIFICATE_SECRET_NAME"]

    if project_kind_short == "tosca":
        work_dir = Path("/opera/csar")
    else:
        work_dir = Path("/terraform-api")

    # TODO: make this configurable
    image_pull_secret_name = "docker-registry" if project_kind_short == "terraform" else None

    deployer = LCMServiceDeployer(
        workspace_id,
        db_project.id,
        project_kind_short,

        image,
        8080,

        work_dir,
        dict(PYTHONPATH="/app") if project_kind_short == "tosca" else dict(),

        project.csar,

        secrets=api_secrets,

        hostname=current_app.config["LCM_ENGINE_HOSTNAME"],
        certificate_secret_name=cert_secret_name,

        image_pull_secret_name=image_pull_secret_name,
    )

    # TODO: run in transaction and asynchronously
    try:
        db_project.container_id = deployer.namespace_name
        deployer.deploy()

        # TODO: restrict ingress routes to specific users

        db_project.available = True
        db.session.commit()
    except Exception as err:
        logging.error(err)
        with StringIO() as stream:
            print_exc(file=stream)
            logging.debug(stream.getvalue())
        db.session.rollback()
        return dict(msg=str(err)), 500

    return EntityReference(id=db_project.id), 202


def create_workspace_project_debug_package(workspace_id, project_id):  # noqa: E501
    """Get a package for local debugging

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int

    :rtype: Union[file, Tuple[file, int], Tuple[file, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), err.status_code

    namespace_name = construct_namespace_name(workspace_id, project_id)

    try:
        zip_stream = create_debug_zip(namespace_name)
    except ValueError as err:
        return dict(msg=str(err)), 500

    try:
        return send_file(
            zip_stream,
            mimetype="application/zip",
            download_name="debug.zip"
        )
    except Exception as err:
        logging.error(err)
        return dict(msg=str(err)), 500


def delete_workspace_project(workspace_id, project_id):  # noqa: E501
    """Delete the project

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_project = db.first_or_404(
        db.select(DBProject).filter_by(id=project_id),
        description=f"No project with ID {project_id}"
    )

    try:
        undeploy_lcm_service(workspace_id, project_id)
        db.session.delete(db_project)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    return None, 200


def describe_workspace_project(workspace_id, project_id):  # noqa: E501
    """Describe the project

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int

    :rtype: Union[Project, Tuple[Project, int], Tuple[Project, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_project = db.first_or_404(
        db.select(DBProject).filter_by(id=project_id),
        description=f"No project with ID {project_id}"
    )

    return db_project.to_api_model(), 200


def describe_workspace_project_status(workspace_id, project_id):  # noqa: E501
    """Get the project creation status

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int

    :rtype: Union[EntityCreationStatus, Tuple[EntityCreationStatus, int], Tuple[EntityCreationStatus, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db.first_or_404(
        db.select(DBProject).filter_by(id=project_id),
        description=f"No project with ID {project_id}"
    )

    try:
        status = get_lcm_service_status_phase(workspace_id, project_id)
    except Exception as ex:
        msg = f"Could not obtain Pod status: {ex}"
        logging.error(str(ex))
        return dict(msg=msg), 404
    return (
        EntityCreationStatus(
            finished=(status.lower() == "running"),
            status=status,
        ),
        200,
    )


def list_workspace_projects(workspace_id):  # noqa: E501
    """List projects in a workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int

    :rtype: Union[List[Project], Tuple[List[Project], int], Tuple[List[Project], int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id}"
    )

    api_projects = [p.to_api_model() for p in db_workspace.projects]

    return api_projects, 200


def replace_workspace_project(workspace_id, project_id, project):  # noqa: E501
    """Replace the project

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int
    :param project: Project specification object
    :type project: dict | bytes

    :rtype: Union[Project, Tuple[Project, int], Tuple[Project, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        project = Project.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_project = DBProject(id=project_id, name=project.name)

    try:
        db.session.add(db_project)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    return db_project.to_api_model(), 200


def update_workspace_project(workspace_id, project_id, project):  # noqa: E501
    """Update the project

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int
    :param project: Project specification object
    :type project: dict | bytes

    :rtype: Union[Project, Tuple[Project, int], Tuple[Project, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        project = Project.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_project = DBProject(id=project_id, name=project.name)

    try:
        db.session.add(db_project)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    return db_project.to_api_model(), 200


def workspace_project_health(workspace_id, project_id):  # noqa: E501
    """Check the status of a project

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param project_id:
    :type project_id: int

    :rtype: Union[ProjectHealth, Tuple[ProjectHealth, int], Tuple[ProjectHealth, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    result = ProjectHealth(
        connectivity=ConnectivityHealth.NONE,
        container=ContainerHealth.UNKNOWN
    )

    namespace_name = construct_namespace_name(workspace_id, project_id)

    try:
        pod_phase = get_lcm_service_status_phase(workspace_id, project_id)
    except Exception as err:
        logging.error(f"Cannot obtain pod state: {err}")
        return result, 200

    if pod_phase:
        pod_phase = pod_phase.lower()
        if pod_phase == "running":
            result.container = ContainerHealth.RUNNING
            # implicitly set by the LCM Service's liveness probe
            result.connectivity = ConnectivityHealth.LAYER5
        elif pod_phase != "unknown":
            result.container = ContainerHealth.STOPPED
        else:  # unknown
            can_ping = can_ping_lcm_service(namespace_name)
            if can_ping:
                result.connectivity = ConnectivityHealth.LAYER3

    return result, 200
