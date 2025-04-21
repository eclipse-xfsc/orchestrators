"""Provide API configuration."""

import os

from src.utils import retrieve_api_version_from_scm


class ApiConfiguration:
    """Store API Configuration."""

    def __init__(self) -> None:
        """Initialize ApiConfiguration object."""
        self.title = os.getenv("PPR_API_TITLE", "PPR API")
        self.description = os.getenv("PPR_API_DESCRIPTION", "Participant Provider Role API is used to obtain "
                                                            "deployment instructions from Gaia-X Self-Descriptions.")
        self.version = os.getenv("PPR_API_VERSION", retrieve_api_version_from_scm(".."))
        self.debug_mode = os.getenv("PPR_API_DEBUG_MODE", "false").lower() == "true"
        self.swagger_url = os.getenv("PPR_API_SWAGGER_URL", "/swagger") if self.debug_mode else None
        self.redoc_url = os.getenv("PPR_API_REDOC_URL", "/redoc") if self.debug_mode else None
        self.root_path = os.getenv("ROOT_PATH", "/")

    def __str__(self) -> str:
        """
        Present ApiConfiguration as a string.

        :return: String that presents ApiConfiguration object
        """
        return f"API config - title: {self.title} | description: {self.description} | version: {self.version} | " \
               f"debug_mode: {self.debug_mode} | swagger_url: {self.swagger_url} | redoc_url: {self.redoc_url} | " \
               f"root_path: {self.root_path}"
