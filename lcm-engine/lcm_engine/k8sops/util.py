from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path
from base64 import b64encode
from hashlib import sha3_512
import re
import logging


# Validation regex: [a-z0-9]([-a-z0-9]*[a-z0-9])?')
SECRET_KEY_SANITIZED_NAME_RE = re.compile(r"[^-a-z0-9]")

URL_PATH_SEPARATOR_RE = re.compile(r"/+")


def no_duplicated_path_separators(path: str) -> str:
    return URL_PATH_SEPARATOR_RE.sub("/", path)


def encode64(string):
    return b64encode(bytes(string), encoding="utf-8")


def sanitize_name(name, replacement="-", prefix=""):
    name_lc = name.lower()
    sanitized_name = SECRET_KEY_SANITIZED_NAME_RE.sub(replacement, name_lc)
    sanitized_name = f"{prefix}{sanitized_name}"
    logging.debug(
        f"sanitize_name({name}, replacement={replacement}): "
        f"sanitized_name = {sanitized_name}"
    )

    return sanitized_name


def name_hash(name, length):
    hash = sha3_512(bytes(name, encoding="ascii"))
    logging.debug(f"name_hash({length}): hash = {hash}")
    return hash.hexdigest()[:length]


def secret_key_name(path: Path, length: int = 6) -> str:
    sanitized_name = sanitize_name(path.name, prefix="path-")
    hash = name_hash(path.as_posix(), length)

    key_name = f"{sanitized_name}-{hash}"

    logging.debug(
        f"secret_key_name({path}, length={length}): "
        f"key_name = {key_name}"
    )

    return key_name


class TBasePath(ABC):
    def __init__(self, path, hostname: Union[str, None] = None):
        self._path = path
        self._hostname = hostname

    @abstractmethod
    def to_traefik_path(self, path_prefix: str) -> str:
        path = f"{path_prefix}/{self._path}"
        path = no_duplicated_path_separators(path)

        path_parts = path.split("/")

        new_path_parts = []

        for part in path_parts:
            if part.startswith("{"):
                group_name = part[1:-1]
                regex = r"[:;.+a-zA-Z0-9-]+"
                part = f"{{{group_name}:{regex}}}"
            new_path_parts.append(part)

        return "/".join(new_path_parts)

    def __str__(self):
        return self.to_traefik_path("")

    def __repr__(self):
        return self.to_traefik_path("")


class TPath(TBasePath):
    def to_traefik_path(self, path_prefix: str) -> str:
        path = super().to_traefik_path(path_prefix)

        path_parts = []
        if self._hostname:
            path_parts.append(f"Host(`{self._hostname}`)")
        path_parts.append(f"Path(`{path}`)")

        return " && ".join(path_parts)
