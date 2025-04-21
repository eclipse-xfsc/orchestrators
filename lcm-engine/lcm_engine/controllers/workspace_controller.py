import logging

import connexion

from lcm_engine.models.error import Error as LCMError  # noqa: E501
from lcm_engine.models.workspace import Workspace  # noqa: E501

from lcm_engine.controllers.helper import (
    AuthError,
    authorize_everything,
    generate_workspace_owner_map,
)

from lcm_engine.db_models.models import db
from lcm_engine.db_models.workspace import Workspace as DBWorkspace
from lcm_engine.db_models.user_workspace import (
    UserWorkspace as DBUserWorkspace
)


def create_workspace(workspace=None):  # noqa: E501
    """Create a new workspace

     # noqa: E501

    :param workspace: Workspace specification object
    :type workspace: dict | bytes

    :rtype: Union[Workspace, Tuple[Workspace, int], Tuple[Workspace, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        workspace = Workspace.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        user, _, status_code = authorize_everything(connexion.request.headers)
    except AuthError as err:
        logging.error(err.msg)
        return None, err.status_code

    db_workspace = DBWorkspace(name=workspace.name)

    binding = DBUserWorkspace(
        user=user,
        workspace=db_workspace,
        is_owner=True,
    )
    user.workspaces.append(binding)
    db_workspace.users.append(binding)

    try:
        db.session.add_all((db_workspace, binding))
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()

    return db_workspace.to_api_model(True), 201


def delete_workspace(workspace_id):  # noqa: E501
    """Delete a workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return None, err.status_code

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id} exists."
    )

    try:
        db.session.delete(db_workspace)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return None, 500

    return None, 200


def describe_workspace(workspace_id):  # noqa: E501
    """Describe a workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int

    :rtype: Union[Workspace, Tuple[Workspace, int], Tuple[Workspace, int, Dict[str, str]]
    """

    try:
        _, is_owner, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id}."
    )

    return db_workspace.to_api_model(is_owner), 200


def get_workspaces():  # noqa: E501
    """List available workspaces

     # noqa: E501

    :rtype: Union[List[Workspace], Tuple[List[Workspace], int], Tuple[List[Workspace], int, Dict[str, str]]
    """

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    workspace_ids, wo_map = generate_workspace_owner_map(user.id)

    db_workspaces = db.session.execute(
        db.select(DBWorkspace).where(DBWorkspace.id.in_(workspace_ids))
    ).all()

    if not db_workspaces:
        msg = f"No workspaces owned by user ID {user.id}"
        logging.error(msg)
        return dict(msg=msg), 404

    api_workspaces = [
        dbw.Workspace.to_api_model(wo_map[dbw.Workspace.id] == user.id)
        for dbw in db_workspaces
    ]

    return api_workspaces, 200


def replace_workspace(workspace_id, workspace):  # noqa: E501
    """Replace a workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param workspace: Workspace specification object
    :type workspace: dict | bytes

    :rtype: Union[Workspace, Tuple[Workspace, int], Tuple[Workspace, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        workspace = Workspace.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        _, is_owner, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=str(err)), 401

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"Workspace ID {workspace_id} does not exist"
    )

    try:
        db_workspace.name = workspace.name
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return LCMError(msg=err.msg), 500

    return db_workspace.to_api_model(is_owner), 200


def update_workspace(workspace_id, workspace):  # noqa: E501
    """Update a workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param workspace: Workspace specification object
    :type workspace: dict | bytes

    :rtype: Union[Workspace, Tuple[Workspace, int], Tuple[Workspace, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        workspace = Workspace.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        _, is_owner, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=str(err)), 401

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"Workspace ID {workspace_id} does not exist"
    )

    try:
        db_workspace.name = workspace.name
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return LCMError(msg=err.msg), 500

    return db_workspace.to_api_model(is_owner), 200
