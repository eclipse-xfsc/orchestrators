ARG BASE_IMAGE_PREFIX=""
FROM ${BASE_IMAGE_PREFIX}library/python:3.11.0-alpine3.16

WORKDIR /ppr
ENTRYPOINT ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]

ARG API_VERSION="unknown"
ENV PPR_API_VERSION=${API_VERSION}

ADD . /ppr
RUN pip install -r requirements.txt
