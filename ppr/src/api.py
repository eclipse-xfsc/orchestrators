"""Provide a REST API."""

import functools
import logging
import os
import urllib.request
from pathlib import Path
from typing import Optional, List, Union
from uuid import uuid4

from content_size_limit_asgi import ContentSizeLimitMiddleware
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.responses import Response
from starlette.background import BackgroundTask

from src.api_configuration import ApiConfiguration
from src.catalogue_helpers import SelfDescriptionCatalogue, SelfDescription, InfrastructureAsCode, IaCType, \
    self_description_catalogue_mock
from src.utils import validate_url, retrieve_openapi_yaml

# set API configuration and logger
api_configuration = ApiConfiguration()
logger = logging.getLogger("uvicorn.error")

# create an API instance
app = FastAPI(
    title=api_configuration.title,
    description=api_configuration.description,
    version=api_configuration.version,
    docs_url=api_configuration.swagger_url,
    redoc_url=api_configuration.redoc_url,
    root_path=api_configuration.root_path
)

# limit maximum size for file uploads to 50 MB
app.add_middleware(ContentSizeLimitMiddleware, max_content_size=52428800)

self_description_catalogues: List[SelfDescriptionCatalogue] = []


@app.on_event("startup")
async def startup_event() -> None:
    """Do everything that needs to be done before calling the API."""
    # TODO: remove example catalogue mock when PPR is really connected to the Self-Description catalogues
    self_description_catalogue_example = self_description_catalogue_mock(
        Path(__file__).resolve().parent.parent / "example_catalogue", "example_catalogue",
        "An example catalogue for testing the PPR")
    self_description_catalogues.append(self_description_catalogue_example)

    if api_configuration.debug_mode:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    logger.info(api_configuration)


@app.get("/openapi.json", include_in_schema=False)
@functools.lru_cache()
def get_openapi_json() -> Response:
    """
    GET OpenAPI specification in JSON format (.json).

    :return: Response object
    """
    try:
        logger.debug("Retrieving OpenAPI Specification (openapi.json)...")
        response = Response(status_code=status.HTTP_200_OK, content=app.openapi(), media_type="text/json")
        logger.debug("Successfully retrieved OpenAPI Specification (openapi.json)!")
        return response
    except Exception as e:
        logger.error("Error retrieving OpenAPI Specification (openapi.json): %s", str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Error retrieving OpenAPI Specification.")


@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def get_openapi_yaml() -> Response:
    """
    GET OpenAPI specification in YAML format (.yaml).

    :return: Response object
    """
    try:
        logger.debug("Retrieving OpenAPI Specification (openapi.yaml)...")
        response = Response(status_code=status.HTTP_200_OK, content=retrieve_openapi_yaml(app), media_type="text/yaml")
        logger.debug("Successfully retrieved OpenAPI Specification (openapi.yaml)!")
        return response
    except Exception as e:
        logger.error("Error retrieving OpenAPI Specification (openapi.yaml): %s", str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Error retrieving OpenAPI Specification.")


@app.get("/openapi.yml", include_in_schema=False)
@functools.lru_cache()
def get_openapi_yml() -> Response:
    """
    GET OpenAPI specification in YAML format (.yml).

    :return: Response object
    """
    try:
        logger.debug("Retrieving OpenAPI Specification (openapi.yml)...")
        response = Response(status_code=status.HTTP_200_OK, content=retrieve_openapi_yaml(app), media_type="text/yml")
        logger.debug("Successfully retrieved OpenAPI Specification (openapi.yml)!")
        return response
    except Exception as e:
        logger.error("Error retrieving OpenAPI Specification (openapi.yml): %s", str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Error retrieving OpenAPI Specification.")


@app.get("/catalogues", summary="Retrieve (and filter) catalogues of Self-Descriptions",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues(keyword: Optional[str] = None, uuid: Optional[str] = None) -> JSONResponse:
    """
    Retrieve (and filter) catalogues of Self-Descriptions (GET method).

    :param keyword: Substring for filtering within catalogue name or description
    :param uuid: Unique id for filtering by catalogue uuid
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving and filtering catalogues of Self-Descriptions...")
        filtered_catalogues = self_description_catalogues
        if keyword is not None and uuid is not None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Use only one parameter to filter!")
        if uuid is not None and keyword is None:
            filtered_catalogues = list(
                filter(lambda cat: uuid.lower() == cat.uuid.lower(), filtered_catalogues))  # type: ignore
        if keyword is not None and uuid is None:
            filter_fun = lambda cat: keyword.lower() in cat.name.lower() or keyword.lower() in cat.description.lower()
            filtered_catalogues = list(filter(filter_fun, filtered_catalogues))

        logger.debug("Successfully retrieved catalogues of Self-Descriptions!")
        return JSONResponse(status_code=status.HTTP_200_OK, content=[cat.to_json() for cat in filtered_catalogues])
    except Exception as e:
        logger.error("Error retrieving catalogues of Self-Descriptions: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving catalogues of Self-Descriptions."})


@app.get("/catalogues/{uuid}/self_descriptions", summary="Retrieve (and filter) Self-Descriptions in the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues_uuid_self_descriptions(uuid: str, keyword: Optional[str] = None,
                                                sha256: Optional[str] = None) -> JSONResponse:
    """
    Retrieve (and filter) Self-Descriptions in the catalogue (GET method).

    :param uuid: Unique id of catalogue
    :param keyword: Substring for filtering within Self-Description name or description
    :param sha256: Unique id for filtering by Self-Description sha256 hash
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving and filtering Self-Descriptions in the catalogue...")
        filtered_catalogues = list(filter(lambda cat: uuid.lower() == cat.uuid.lower(), self_description_catalogues))
        filtered_self_descriptions: List[SelfDescription] = []

        if filtered_catalogues:
            filtered_catalogue = filtered_catalogues[0]
            filtered_self_descriptions = filtered_catalogue.self_descriptions
            if keyword is not None and sha256 is not None:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                    content="Use only one parameter to filter!")
            if sha256 is not None and keyword is None:
                filtered_self_descriptions = filtered_catalogue.get_self_descriptions_by_sha256(sha256)
            if keyword is not None and sha256 is None:
                filtered_self_descriptions = filtered_catalogue.get_self_descriptions_by_keyword(keyword)

        logger.debug("Successfully retrieved Self-Descriptions in the catalogue!")
        return JSONResponse(status_code=status.HTTP_200_OK, content=[sd.to_json() for sd in filtered_self_descriptions])
    except Exception as e:
        logger.error("Error retrieving Self-Descriptions in the catalogue: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving Self-Descriptions in the catalogue."})


@app.get("/catalogues/{uuid}/self_descriptions/{sha256}/json_ld",
         summary="Get Self-Description in JSON-LD format from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues_uuid_self_descriptions_sha256_jdon_ld(uuid: str, sha256: str) -> JSONResponse:
    """
    Get Self-Description in JSON-LD format from the catalogue (GET method).

    :param uuid: Unique id of catalogue
    :param sha256: Unique sha256 hash for Self-Description
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving JSON-LD for the Self-Description...")
        retrieved_self_description_json_ld = {}
        filtered_catalogues = list(filter(lambda cat: uuid.lower() == cat.uuid.lower(), self_description_catalogues))

        if filtered_catalogues:
            filtered_catalogue = filtered_catalogues[0]

            self_descriptions = filtered_catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                retrieved_self_description_json_ld = self_descriptions[0].json_ld

        logger.debug("Successfully retrieved JSON-LD for the Self-Description!")
        return JSONResponse(status_code=status.HTTP_200_OK, content=retrieved_self_description_json_ld)
    except Exception as e:
        logger.error("Error retrieving JSON-LD for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving JSON-LD for the Self-Description."})


@app.get("/catalogues/{uuid}/self_descriptions/{sha256}/iac",
         summary="Get IaC (package and inputs) that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues_uuid_self_descriptions_sha256_iac(uuid: str, sha256: str,
                                                           iac_type: Optional[IaCType] = None) -> JSONResponse:
    """
    Get IaC (package and inputs) that implements Self-Description from the catalogue (GET method).

    :param uuid: Unique id of catalogue
    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving IaC for the Self-Description...")
        retrieved_self_description_iac: List[InfrastructureAsCode] = []
        filtered_catalogues = list(filter(lambda cat: uuid.lower() == cat.uuid.lower(), self_description_catalogues))

        if filtered_catalogues:
            filtered_catalogue = filtered_catalogues[0]

            self_descriptions = filtered_catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                retrieved_self_description_iac = self_descriptions[0].filter_iac(iac_type)

        logger.debug("Successfully retrieved IaC for the Self-Description!")
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=[iac.to_json() for iac in retrieved_self_description_iac])
    except Exception as e:
        logger.error("Error retrieving IaC for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC for the Self-Description."})


@app.get("/catalogues/{uuid}/self_descriptions/{sha256}/iac/url",
         summary="Download IaC package that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues_uuid_sds_sha256_iac_url(uuid: str, sha256: str, iac_type: IaCType) -> Union[JSONResponse,
                                                                                                     FileResponse]:
    """
    Download IaC package that implements Self-Description from the catalogue (GET method).

    :param uuid: Unique id of catalogue
    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Downloading IaC package for the Self-Description...")
        filtered_catalogues = list(filter(lambda cat: uuid.lower() == cat.uuid.lower(), self_description_catalogues))

        if filtered_catalogues:
            filtered_catalogue = filtered_catalogues[0]

            self_descriptions = filtered_catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                iac = self_descriptions[0].filter_iac(iac_type)[0]
                if iac.url and isinstance(iac.url, str):
                    iac_url = iac.url.strip()
                    validate_url(iac_url)
                    with urllib.request.urlopen(iac_url) as response:
                        data = response.read()
                        filename = response.headers.get_filename()
                        filepath = str(uuid4().hex)
                        with open(filepath, "wb") as out_file:
                            out_file.write(data)

                        logger.debug("Successfully prepared IaC package for the Self-Description!")
                        return FileResponse(path=filepath, filename=filename,
                                            background=BackgroundTask(lambda: os.remove(filepath)))

        logger.debug("IaC package file could not be retrieved!.")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="IaC package file could not be retrieved!")
    except Exception as e:
        logger.error("Error retrieving IaC package for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC package for the Self-Description."})


@app.get("/catalogues/{uuid}/self_descriptions/{sha256}/iac/inputs",
         summary="Download IaC inputs for IaC package that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_catalogues_uuid_sds_sha256_iac_inputs(uuid: str, sha256: str, iac_type: IaCType) -> Union[JSONResponse,
                                                                                                        FileResponse]:
    """
    Download IaC inputs for IaC package that implements Self-Description from the catalogue (GET method).

    :param uuid: Unique id of catalogue
    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Downloading IaC inputs for the Self-Description...")
        filtered_catalogues = list(filter(lambda cat: uuid.lower() == cat.uuid.lower(), self_description_catalogues))

        if filtered_catalogues:
            filtered_catalogue = filtered_catalogues[0]

            self_descriptions = filtered_catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                iac = self_descriptions[0].filter_iac(iac_type)[0]
                if iac.inputs:
                    with urllib.request.urlopen(iac.inputs) as response:
                        data = response.read()
                        filename = response.headers.get_filename()
                        filepath = str(uuid4().hex)
                        with open(filepath, "wb") as out_file:
                            out_file.write(data)

                        logger.debug("Successfully prepared IaC inputs for the Self-Description!")
                        return FileResponse(path=filepath, filename=filename,
                                            background=BackgroundTask(lambda: os.remove(filepath)))

        logger.debug("IaC input file could not be retrieved!.")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="IaC input file could not be retrieved!")
    except Exception as e:
        logger.error("Error retrieving IaC inputs for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC inputs for the Self-Description."})


@app.get("/self_descriptions", summary="Retrieve (and filter) Self-Descriptions from all catalogues",
         responses={200: {}, 400: {"model": str}})
async def get_self_descriptions(keyword: Optional[str] = None,
                                sha256: Optional[str] = None) -> JSONResponse:
    """
    Retrieve (and filter) Self-Descriptions from all catalogues (GET method).

    :param keyword: substring for filtering within Self-Description name or description
    :param sha256: Unique id for filtering by Self-Description sha256 hash
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving and filtering catalogues of Self-Descriptions...")
        filtered_self_descriptions: List[SelfDescription] = []
        for catalogue in self_description_catalogues:
            filtered_self_descriptions_catalogue = catalogue.self_descriptions
            if keyword is not None and sha256 is not None:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                    content="Use only one parameter to filter!")
            if sha256 is not None and keyword is None:
                filtered_self_descriptions_catalogue = catalogue.get_self_descriptions_by_sha256(sha256)
            if keyword is not None and sha256 is None:
                filtered_self_descriptions_catalogue = catalogue.get_self_descriptions_by_keyword(keyword)

            filtered_self_descriptions += filtered_self_descriptions_catalogue

        logger.debug("Successfully retrieved catalogues of Self-Descriptions!")
        return JSONResponse(status_code=status.HTTP_200_OK, content=[sd.to_json() for sd in filtered_self_descriptions])
    except Exception as e:
        logger.error("Error retrieving catalogues of Self-Descriptions: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving catalogues of Self-Descriptions."})


@app.get("/self_descriptions/{sha256}/json_ld",
         summary="Get Self-Description in JSON-LD format from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_self_descriptions_sha256_json_ld(sha256: str) -> JSONResponse:
    """
    Get Self-Description in JSON-LD format from the catalogue (GET method).

    :param sha256: Unique sha256 hash for Self-Description
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving JSON-LD for the Self-Description...")
        retrieved_self_description_json_ld = {}
        for catalogue in self_description_catalogues:
            self_descriptions = catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                retrieved_self_description_json_ld = self_descriptions[0].json_ld
                break

        logger.debug("Successfully retrieved JSON-LD for the Self-Description!")
        return JSONResponse(status_code=status.HTTP_200_OK, content=retrieved_self_description_json_ld)
    except Exception as e:
        logger.error("Error retrieving JSON-LD for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving JSON-LD for the Self-Description."})


@app.get("/self_descriptions/{sha256}/iac",
         summary="Get IaC (package and inputs) that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_self_descriptions_sha256_iac(sha256: str, iac_type: Optional[IaCType] = None) -> JSONResponse:
    """
    Get IaC (package and inputs) that implements Self-Description from the catalogue (GET method).

    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Retrieving IaC for the Self-Description...")
        retrieved_self_description_iac: List[InfrastructureAsCode] = []
        for catalogue in self_description_catalogues:
            self_descriptions = catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                retrieved_self_description_iac = self_descriptions[0].filter_iac(iac_type)
                break

        logger.debug("Successfully retrieved IaC for the Self-Description!")
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=[iac.to_json() for iac in retrieved_self_description_iac])
    except Exception as e:
        logger.error("Error retrieving IaC for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC for the Self-Description."})


@app.get("/self_descriptions/{sha256}/iac/url",
         summary="Download IaC package that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_self_descriptions_sha256_iac_url(sha256: str, iac_type: IaCType) -> Union[JSONResponse, FileResponse]:
    """
    Download IaC package that implements Self-Description from the catalogue (GET method).

    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Downloading IaC package for the Self-Description...")
        for catalogue in self_description_catalogues:
            self_descriptions = catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                iac = self_descriptions[0].filter_iac(iac_type)[0]
                if iac.url and isinstance(iac.url, str):
                    iac_url = iac.url.strip()
                    validate_url(iac_url)
                    with urllib.request.urlopen(iac_url) as response:
                        data = response.read()
                        filename = response.headers.get_filename()
                        filepath = str(uuid4().hex)
                        with open(filepath, "wb") as out_file:
                            out_file.write(data)

                    logger.debug("Successfully prepared IaC package for the Self-Description!")
                    return FileResponse(path=filepath, filename=filename,
                                        background=BackgroundTask(lambda: os.remove(filepath)))

        logger.debug("IaC package file could not be retrieved!.")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="IaC package file could not be retrieved!")
    except Exception as e:
        logger.error("Error retrieving IaC package for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC package for the Self-Description."})


@app.get("/self_descriptions/{sha256}/iac/inputs",
         summary="Download IaC inputs for IaC package that implements Self-Description from the catalogue",
         responses={200: {}, 400: {"model": str}})
async def get_self_descriptions_sha256_iac_inputs(sha256: str, iac_type: IaCType) -> Union[JSONResponse, FileResponse]:
    """
    Download IaC inputs for IaC package that implements Self-Description from the catalogue (GET method).

    :param sha256: Unique sha256 hash for Self-Description
    :param iac_type: Type of IaC (e.g., TOSCA, Terraform)
    :return: JSONResponse object (with status code 200 or 400)
    """
    try:
        logger.debug("Downloading IaC inputs for the Self-Description...")
        for catalogue in self_description_catalogues:
            self_descriptions = catalogue.get_self_descriptions_by_sha256(sha256)
            if self_descriptions is not None:
                iac = self_descriptions[0].filter_iac(iac_type)[0]
                if iac.inputs:
                    with urllib.request.urlopen(iac.inputs) as response:
                        data = response.read()
                        filename = response.headers.get_filename()
                        filepath = str(uuid4().hex)
                        with open(filepath, "wb") as out_file:
                            out_file.write(data)

                        logger.debug("Successfully prepared IaC inputs for the Self-Description!")
                        return FileResponse(path=filepath, filename=filename,
                                            background=BackgroundTask(lambda: os.remove(filepath)))

        logger.debug("IaC input file could not be retrieved!.")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "IaC input file could not be retrieved!"})
    except Exception as e:
        logger.error("Error retrieving IaC inputs for the Self-Description: %s", str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Error retrieving IaC inputs for the Self-Description."})
