"""Provide utility functions that can be used as helpers throughout the code."""

from io import StringIO
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import yaml
from fastapi import FastAPI
from setuptools_scm import get_version


def validate_url(url: str) -> None:
    """
    Validate URL.

    :type url: URL as string
    """
    parsed_url = urlparse(url)
    supported_url_schemes = ("https", "http")
    if parsed_url.scheme not in supported_url_schemes:
        raise Exception(f"URL '{url}' has invalid URL scheme, supported are: {', '.join(supported_url_schemes)}.")

    if len(url) > 2048:
        raise Exception(f"URL '{url}' exceeds maximum length of 2048 characters.")

    if not parsed_url.netloc:
        raise Exception(f"No URL domain specified in '{url}'.")

    try:
        with urlopen(url):
            return
    except URLError as e:
        raise Exception(f"Cannot open URL '{url}'.") from e


def retrieve_api_version_from_scm(root_folder: str) -> str:
    """
    Retrieve API version from source control management (i.e., git, mercurial).

    :param root_folder: Root folder of the project
    :return: Version string
    """
    try:
        return get_version(root=root_folder, local_scheme=lambda v: "", relative_to=__file__)
    except (LookupError, OSError):
        return "unknown"


def retrieve_openapi_yaml(api_instance: FastAPI) -> str:
    """
    Return OpenAPI specification as YAML string.

    :param api_instance: FastAPI object
    :return: A string with YAML OpenAPI Specification
    """
    openapi_json = api_instance.openapi()
    string_stream = StringIO()
    yaml.dump(openapi_json, string_stream)
    yaml_string = string_stream.getvalue()
    string_stream.close()
    return yaml_string
