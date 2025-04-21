from io import StringIO
import re
from typing import Any, List, Mapping, Tuple
from datetime import datetime, timedelta
import logging

from lcm_engine.db_models.models import db
from lcm_engine.db_models.user import User as DBUser
from lcm_engine.db_models.secret import Secret as DBSecret
from lcm_engine.db_models.project import Project as DBProject
from lcm_engine.db_models.user_workspace import (
    UserWorkspace as DBUserWorkspace
)


class AuthError(Exception):
    def __init__(self, msg, status_code=403):
        self._msg = msg
        self._status_code = status_code

    @property
    def msg(self):
        return self._msg

    @property
    def status_code(self):
        return self._status_code


def sanitize_name_rfc_1123(name: str, prefix: str = "volume-") -> str:
    # [a-z0-9]([-a-z0-9]*[a-z0-9])?
    s_name = name or "a"
    s_name = name.lower()
    s0 = s_name[0]

    sanitized = StringIO()

    first_re = last_re = re.compile(r"[a-z0-9]")
    if first_re.match(s0):
        sanitized.write(s0)
    else:
        sanitized.write(prefix)

    mid_re = re.compile(r"[-a-z0-9]")
    for c in s_name[1:-1]:
        if mid_re.match(c):
            sanitized.write(c)
        else:
            sanitized.write("-")

    if last_re.match(s_name[-1]):
        sanitized.write(s_name[-1])
    else:
        sanitized.write("-")
        sanitized.write(str(len(s_name)))

    return sanitized.getvalue()


def logout_cookie() -> Mapping[str, Any]:
    return dict(
        value="",
        path="/",
        domain="xlab.si",
        expires=datetime.now() - timedelta(days=1),
        secure=True,
        httponly=True,
    )


def _create_user(oidc_id: int) -> DBUser:
    new_user = DBUser(oidc_identifier=oidc_id)

    db.session.add(new_user)
    db.session.commit()

    return new_user


def get_or_create_user(headers: Mapping[str, str]) -> DBUser:
    oidc_id = headers.get("X-Forwarded-User")

    if oidc_id is None:
        return

    logging.info(f"Getting user from X-Forwarded-User: {oidc_id}")

    existing_user = db.session.execute(
        db.select(DBUser).filter_by(oidc_identifier=oidc_id)
    ).first()

    if existing_user:
        logging.info("User exists")
        return existing_user.User

    logging.info("No user exists, creating a new one")
    existing_user = _create_user(oidc_id)

    return existing_user


def authorize_secret(user: DBUser, secret_id: int) -> bool:
    secret = db.session.execute(
        db.select(DBSecret).filter_by(id=secret_id)
    ).first()

    if not secret:
        raise AuthError("Secret not found", status_code=404)

    if secret.Secret.user_id != user.id:
        msg = (
            "Secret failed authorization: wanted "
            f"{user.id}, got {secret.Secret.user_id}"
        )
        raise AuthError(msg)

    return True


def authorize_project(user: DBUser, project_id: int) -> bool:
    user_workspace = db.session.execute(
        db.select(DBUserWorkspace)
        .where(DBUserWorkspace.workspace_id == DBProject.workspace_id)
        .where(DBUserWorkspace.user_id == user.id)
        .where(DBProject.id == project_id)
    ).first()

    if not user_workspace:  # if user_workspace is None:
        raise AuthError("Project failed authorization")

    return user_workspace.UserWorkspace.is_owner


def authorize_workspace(user: DBUser, workspace_id: int) -> bool:
    user_workspace = db.session.execute(
        db.select(DBUserWorkspace).filter_by(
            user_id=user.id, workspace_id=workspace_id
        )
    ).first()

    if not user_workspace:  # if user_workspace is None:
        raise AuthError("Workspace failed authorization")

    return user_workspace.UserWorkspace.is_owner


def authorize_everything(
    headers: Mapping[str, str],
    workspace_id: int = None,
    project_id: int = None,
    secret_id: int = None,
):
    is_owner_total = False
    try:
        user = get_or_create_user(headers)

        ids = (secret_id, project_id, workspace_id)
        auth_fs = (
            authorize_secret,
            authorize_project,
            authorize_workspace,
        )

        for id, auth_f in zip(ids, auth_fs):
            if id is not None:
                is_owner = auth_f(user, id)
                is_owner_total = is_owner_total or is_owner

    except Exception as e:
        logging.error(e)
        raise AuthError(e, status_code=403)

    return user, is_owner_total, 0


def generate_workspace_owner_map(
    user_id: int
) -> Tuple[List[int], Mapping[int, int]]:
    user_ws = db.session.execute(
        db.select(DBUserWorkspace).filter_by(user_id=user_id)
    ).all()

    if user_ws is None:
        msg = f"No user workspaces for user id: {user_id}"
        logging.error(msg)
        raise AuthError(msg)

    ws_owner_map = {
        uw.UserWorkspace.workspace_id: uw.UserWorkspace.user_id
        for uw in user_ws
    }
    ws_ids = list(ws_owner_map.keys())

    return (
        ws_ids,
        ws_owner_map,
    )
