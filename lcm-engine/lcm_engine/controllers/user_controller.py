import logging

import connexion
from flask import make_response

from lcm_engine.models.authentication_status import AuthenticationStatus  # noqa: E501
from lcm_engine.models.error import Error as LCMError  # noqa: E501
from lcm_engine.models.workspace_user_authorization_request import (
    WorkspaceUserAuthorizationRequest,
)  # noqa: E501
from lcm_engine.controllers.helper import (
    get_or_create_user,
    logout_cookie,
    authorize_everything,
    AuthError,
)
from lcm_engine.db_models.models import db
from lcm_engine.db_models.user import User as DBUser
from lcm_engine.db_models.workspace import Workspace as DBWorkspace
from lcm_engine.db_models.user_workspace import (
    UserWorkspace as DBUserWorkspace
)


def auth_logout():  # noqa: E501
    """Log out of the application

     # noqa: E501

    :rtype: Union[AuthenticationStatus, Tuple[AuthenticationStatus, int], Tuple[AuthenticationStatus, int, Dict[str, str]]
    """

    try:
        user = get_or_create_user(connexion.request.headers)
    except Exception as err:
        logging.error(f"Error while logging out: {err}")

    user_id = user.oidc_identifier

    auth_status = AuthenticationStatus(
        is_logged_in=False, user_identifier=user_id
    )
    response = make_response(auth_status)
    response.set_cookie("_forward_auth", **logout_cookie())
    response.status_code = 200

    return response


def auth_status():  # noqa: E501
    """Get the authentication status

     # noqa: E501

    :rtype: Union[AuthenticationStatus, Tuple[AuthenticationStatus, int], Tuple[AuthenticationStatus, int, Dict[str, str]]
    """

    logged_in = True
    try:
        user = get_or_create_user(connexion.request.headers)
    except Exception as err:
        logging.error(f"Error obtaining authentication status: {err}")
        logged_in = False

    auth_status = AuthenticationStatus(
        is_logged_in=logged_in, user_identifier=user.oidc_identifier
    )

    return auth_status, 200


def authorize_workspace_user(
    workspace_id, workspace_user_authorization_request
):  # noqa: E501
    """Authorize a new user to the workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param workspace_user_authorization_request: Authorization specification object
    :type workspace_user_authorization_request: dict | bytes

    :rtype: Union[object, Tuple[object, int], Tuple[object, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        workspace_user_authorization_request = (
            WorkspaceUserAuthorizationRequest.from_dict(
                connexion.request.get_json()
            )
        )  # noqa: E501

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers, workspace_id=workspace_id
        )
    except AuthError as err:
        msg = f"Cannot authorize everything: {err.msg}"
        logging.error(msg=msg)
        return LCMError(msg=msg), err.status_code

    workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"Cannot obtain a workspace with ID {workspace_id}"
    )

    oidc_id = workspace_user_authorization_request.user

    requested_user = db.first_or_404(
        db.select(DBUser).filter_by(oidc_identifier=oidc_id),
        description=f"Cannot obtain a user with OIDC ID {oidc_id}"
    )

    for uw in workspace.users:
        if uw.user.oidc_identifier == oidc_id:
            logging.info("User already authorized.")
            return dict(description="User already authorized."), 200

    binding = DBUserWorkspace(
        user=requested_user,
        workspace=workspace,
        is_owner=False,
    )
    requested_user.workspaces.append(binding)
    workspace.users.append(binding)

    logging.info(f"Authorizing user: {binding}")

    try:
        db.session.add(binding)
        db.session.commit()
    except Exception as err:
        logging.error(f"Error authorizing workspace user: {err}.")
        db.session.rollback()
        return LCMError(msg=str(err)), 500

    logging.info("Authorization success.")

    return dict(description="Authorization success."), 200


def deauthorize_workspace_user(workspace_id, deauthorization_request):  # noqa: E501
    """Deauthorize a user from the workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int
    :param deauthorization_request: Authorization specification object
    :type deauthorization_request: dict | bytes

    :rtype: Union[object, Tuple[object, int], Tuple[object, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        deauthorization_request = WorkspaceUserAuthorizationRequest.from_dict(
            connexion.request.get_json()
        )  # noqa: E501

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers, workspace_id=workspace_id
        )
    except AuthError as err:
        logging.error(err.msg)
        return None, err.status_code

    authorized_user = db.session.execute(
        db.select(DBUser)
        .join(DBUserWorkspace)
        .filter(DBUserWorkspace.workspace_id == 1)
        .filter(DBUser.oidc_identifier == deauthorization_request.user)
    ).first()

    user_currently_authorized = authorized_user is not None

    if user_currently_authorized:
        logging.info("User is authorized.")
    else:
        logging.info("User not authorized, will not deauthorize.")
        return None, 200

    auth_binding = db.session.execute(
        db.select(DBUserWorkspace)
        .filter_by(user_id=authorized_user.id, workspace_id=workspace_id)
    ).first()

    if auth_binding.is_owner:
        msg = "Cannot deauthorize owner"
        logging.error(msg)
        return msg, 400

    logging.info(f"Deauthorizing user: {auth_binding}")

    try:
        db.session.remove(auth_binding)
        db.session.commit()
    except Exception as err:
        logging.error(err)
        db.session.rollback()
        return None, 500

    logging.info("Deauthorization success.")

    return None, 200


def get_workspace_authorizations(workspace_id):  # noqa: E501
    """List users authorized to this workspace

     # noqa: E501

    :param workspace_id:
    :type workspace_id: int

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """

    try:
        _, _, status_code = authorize_everything(
            connexion.request.headers,
            workspace_id=workspace_id,
        )
    except AuthError as err:
        logging.error(err.msg)
        return dict(msg=err.msg), 401

    workspace = db.first_or_404(
        db.select(DBWorkspace).filter_by(id=workspace_id),
        description=f"No workspace with ID {workspace_id}"
    )

    users = [user.user.oidc_identifier for user in workspace.users]

    return users, 200
