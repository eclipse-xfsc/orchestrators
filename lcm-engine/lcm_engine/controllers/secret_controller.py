import binascii
import hashlib
import logging
from base64 import b64decode

import connexion

from lcm_engine.controllers.helper import AuthError, authorize_everything
from lcm_engine.db_models.env_secret import EnvSecret as DBEnvSecret
from lcm_engine.db_models.file_secret import FileSecret as DBFileSecret
from lcm_engine.db_models.models import db
from lcm_engine.db_models.secret import Secret as DBSecret
from lcm_engine.db_models.secret_workspace import \
    SecretWorkspace as DBSecretWorkspace
from lcm_engine.db_models.workspace import Workspace as DBWorkspace
from lcm_engine.k8sops import k8sclient
from lcm_engine.models.error import Error as LCMError  # noqa: E501
from lcm_engine.models.secret import Secret  # noqa: E501


def assign_secret(workspace_id, secret_id):  # noqa: E501
    """Assign a new secret to the workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param secret_id:
    :type secret_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            secret_id=secret_id
        )
    except AuthError as err:
        return dict(msg=err.msg), err.status_code

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=f"No secret ID {secret_id}"
    )

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace ID {workspace_id}"
    )

    same_secret_associated = db.session.execute(
        db.select(DBSecret)
        .join(DBSecretWorkspace, DBSecret.id == DBSecretWorkspace.secret_id)
        .filter(DBSecretWorkspace.workspace_id == workspace_id)
        .filter(DBSecretWorkspace.secret_id == secret_id)
    ).all()

    if same_secret_associated:
        msg = f"Secret ID {secret_id} is already associated "
        f"with workspace ID {workspace_id}"
        return dict(msg=msg), 400

    existing_secrets = db.session.execute(
        db.select(DBSecret)
        .join(DBSecretWorkspace, DBSecret.id == DBSecretWorkspace.secret_id)
        .filter(DBSecretWorkspace.workspace_id == workspace_id)
    ).scalars().all()

    clean_db_secret_paths = [fs.path for fs in db_secret.file_secrets]
    for existing_secret in existing_secrets:
        for file_secret in existing_secret.file_secrets:
            if file_secret.path in clean_db_secret_paths:
                msg = (
                    "Another secret has matching path: "
                    f"ID: {existing_secret.id} Path: {file_secret.path}"
                )
                logging.error(msg)
                return dict(msg=msg), 400

    association = DBSecretWorkspace(secret=db_secret, workspace=db_workspace)
    db_secret.workspaces.append(association)
    db_workspace.secrets.append(association)

    try:
        db.session.add(association)
        db.session.commit()
    except Exception as err:
        msg = (
            f"Error associating secret ID {secret_id} "
            f"with workspace ID {workspace_id}: {err}"
        )
        logging.error(msg)
        db.session.rollback()
        return dict(msg=msg), 500

    return None, 200


def create_secret(secret=None):  # noqa: E501
    """Create a new secret

     # noqa: E501

    :param x_forwarded_user: An authorization header
    :type x_forwarded_user: str
    :param secret: Secret specification object
    :type secret: dict | bytes

    :rtype: Union[Secret, Tuple[Secret, int], Tuple[Secret, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        secret = Secret.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        user, _, status_code = authorize_everything(connexion.request.headers)
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    logging.info(f"Creating secret from {secret}")

    db_secret = DBSecret(name=secret.name, user_id=user.id)

    try:
        db.session.add(db_secret)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    db_secrets_to_add = []

    if secret.file:
        try:
            binary_contents = b64decode(secret.file.contents)
        except binascii.Error as err:
            return dict(msg=str(err)), 400

        file_secret = DBFileSecret(
            path=secret.file.path,
            contents=binary_contents,
            contents_hash=hashlib.sha512(binary_contents).hexdigest(),
            secret_id=db_secret.id,
        )

        db_secrets_to_add.append(file_secret)

    if secret.env:
        for name, value in secret.env.items():
            env_secret = DBEnvSecret(
                name=name,
                value=value,
                secret_id=db_secret.id
            )
            db_secrets_to_add.append(env_secret)

    if not secret.file and not secret.env:
        return dict(msg="Empty secret"), 400

    try:
        db.session.add_all(db_secrets_to_add)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return dict(msg=str(err)), 500

    return db_secret.to_api_model(), 201


def delete_secret(secret_id):  # noqa: E501
    """Delete a secret

     # noqa: E501

    :param secret_id:
    :type secret_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            secret_id=secret_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return None, err.status_code

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=f"No secret with ID {secret_id} exists."
    )

    for ws in db_secret.workspaces:
        logging.info(f"Deleting secrets in workspace {ws.id}")

        db_workspace = ws.workspace

        for project in db_workspace.projects:
            msg = f"Deleting secret {secret_id} from project {project.id}"
            logging.info(msg)

            namespace_name = project.container_id
            pod = k8sclient.get_pod(namespace_name, namespace)

            k8sclient.delete_secret_files(pod, [db_secret])

    try:
        db.session.delete(db_secret)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return None, 500

    return None, 200


def describe_secret(secret_id):  # noqa: E501
    """Describe a secret

     # noqa: E501

    :param secret_id:
    :type secret_id: int

    :rtype: Union[Secret, Tuple[Secret, int], Tuple[Secret, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            secret_id=secret_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return LCMError(msg=err.msg), err.status_code

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=f"No secret with ID {secret_id}"
    )

    return db_secret.to_api_model(), 200


def get_secrets():  # noqa: E501
    """List available secrets

     # noqa: E501

    :rtype: Union[List[Secret], Tuple[List[Secret], int], Tuple[List[Secret], int, Dict[str, str]]
    """

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_secrets = db.session.execute(
        db.select(DBSecret).filter_by(user_id=user.id)
    ).all()

    if not db_secrets:
        msg = f"User ID {user.id} has no secrets"
        logging.error(msg)
        return dict(msg=msg), 404

    api_secrets = [dbs.Secret.to_api_model() for dbs in db_secrets]

    return api_secrets, 200


def list_workspace_secrets(workspace_id):  # noqa: E501
    """List secrets assigned to the workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int

    :rtype: Union[List[Secret], Tuple[List[Secret], int], Tuple[List[Secret], int, Dict[str, str]]
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

    api_secrets = [sw.secret.to_api_model() for sw in db_workspace.secrets]

    return api_secrets, 200


def remove_workspace_secret(workspace_id, secret_id):  # noqa: E501
    """Remove the secret from the workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param secret_id:
    :type secret_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
            secret_id=secret_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=f"No secret with ID {secret_id} exists"
    )

    db_workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id}."
    )

    for project in db_workspace.projects:
        logging.info(f"Deleting secret {secret_id} from project {project.id}")

        namespace_name = project.container_id

    binding = db.first_or_404(
        db.select(DBSecretWorkspace).filter_by(
            secret_id=secret_id, workspace_id=workspace_id
        ),
        description=(
            f"No secret with ID {secret_id} on workspace ID {workspace_id}."
        )
    )

    try:
        db.session.remove(binding)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollout()
        return dict(msg=str(err)), 500

    return None, 200


def replace_secret(secret_id, secret):  # noqa: E501
    """Replace a secret

     # noqa: E501

    :param secret_id:
    :type secret_id: int
    :param secret: Secret specification object
    :type secret: dict | bytes

    :rtype: Union[Secret, Tuple[Secret, int], Tuple[Secret, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        secret = Secret.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers,
            secret_id=secret_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return LCMError(msg=err.msg), err.status_code

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=(
            f"Secret with ID {secret_id} does not exist; nothing to update"
        )
    )

    db_secret.name = secret.name

    secrets_to_add = []

    if secret.file:
        if db_secret.env_secrets:
            msg = f"Trying to update environment variables on a file-based secret {secret.id}."
            logging.error(msg)
            return dict(msg=msg), 404
        if not db_secret.file_secret:
            msg = f"Secret {secret.id} is not of type file."
            logging.error(msg)
            return dict(msg=msg), 500

        try:
            binary_contents = b64decode(secret.file.contents)
        except binascii.Error as err:
            msg = f"Error base64 decoding secret content: {err.msg}"
            logging.error(msg)
            return LCMError(msg=msg), 500

        db_secret.file_secret.path = secret.file.path
        db_secret.file_secret.contents = binary_contents
        db_secret.file_secret.contents_hash = (
            hashlib.sha512(binary_contents).hexdigest()
        )
    elif secret.env:
        if db_secret.file_secret:
            msg = f"Trying to update file on an env-based secret {secret.id}."
            logging.error(msg)
            return dict(msg=msg), 404
        if db_secret.env_secrets:
            msg = f"Secret {secret.id} is not of type env."
            logging.error(msg)
            return dict(msg=msg), 500

        env_secrets_by_name = dict()
        for es in db_secret.env_secrets:
            env_secrets_by_name[es.name] = es

        for name, value in secret.env.items():
            if name in env_secrets_by_name:
                # already exists
                env_secret = env_secrets_by_name[name]
                env_secret.value = value
            else:
                env_secret = DBEnvSecret(
                    name=name,
                    value=value,
                    secret_id=db_secret.id
                )

                secrets_to_add.append(env_secret)
    try:
        db.session.add_all(secrets_to_add)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return LCMError(msg=err.msg), 500

    return db_secret.to_api_model(), 200


def update_secret(secret_id, secret):  # noqa: E501
    """Update a secret

     # noqa: E501

    :param secret_id:
    :type secret_id: int
    :param secret: Secret specification object
    :type secret: dict | bytes

    :rtype: Union[Secret, Tuple[Secret, int], Tuple[Secret, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        secret = Secret.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        user, _, status_code = authorize_everything(
            connexion.request.headers,
            secret_id=secret_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return LCMError(msg=err.msg), err.status_code

    db_secret = db.first_or_404(
        db.select(DBSecret).filter_by(id=secret_id),
        description=(
            f"Secret with ID {secret_id} does not exist; nothing to update"
        )
    )

    db_secret.name = secret.name

    secrets_to_add = []

    if secret.file:
        if db_secret.env_secrets:
            msg = (
                "Trying to update environment variables on a "
                f"file-based secret {secret.id}."
            )
            logging.error(msg)
            return dict(msg=msg), 404
        if not db_secret.file_secret:
            msg = f"Secret {secret.id} is not of type file."
            logging.error(msg)
            return dict(msg=msg), 500

        try:
            binary_contents = b64decode(secret.file.contents)
        except binascii.Error as err:
            msg = f"Error base64 decoding secret content: {err.msg}"
            logging.error(msg)
            return LCMError(msg=msg), 500

        db_secret.file_secret.path = secret.file.path
        db_secret.file_secret.contents = binary_contents
        db_secret.file_secret.contents_hash = (
            hashlib.sha512(binary_contents).hexdigest()
        )
    elif secret.env:
        if db_secret.file_secret:
            msg = f"Trying to update file on an env-based secret {secret.id}."
            logging.error(msg)
            return dict(msg=msg), 404
        if db_secret.env_secrets:
            msg = f"Secret {secret.id} is not of type env."
            logging.error(msg)
            return dict(msg=msg), 500

        env_secrets_by_name = dict()
        for es in db_secret.env_secrets:
            env_secrets_by_name[es.name] = es

        for name, value in secret.env.items():
            if name in env_secrets_by_name:
                # already exists
                env_secret = env_secrets_by_name[name]
                env_secret.value = value
            else:
                env_secret = DBEnvSecret(
                    name=name,
                    value=value,
                    secret_id=db_secret.id
                )

                secrets_to_add.append(env_secret)
    try:
        db.session.add_all(secrets_to_add)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return LCMError(msg=err.msg), 500

    return db_secret.to_api_model(), 200
