# PPR
Participant Provider Role (PPR) API is used to obtain deployment instructions from Gaia-X Self-Descriptions.

## Table of Contents
  - [Description](#purpose-and-description)
  - [Usage and development](#usage-and-development)
    - [Run with Docker](#run-with-docker)
    - [Configuration](#configuration)
    - [Examples](#examples)
    - [Development](#development)
        - [Building Docker image](#building-docker-image)
        - [Running from source](#running-from-source)
        - [Testing](#testing)
        - [CI/CD](#cicd)
  - [License](#license)
  - [Contact](#contact)

## Purpose and description
The Participant Provider Role (PPR) is a REST API service used to obtain deployment instructions from 
Gaia-X Self-Descriptions.

Explore the [GXFS Documentation] for more information.

## Usage and development
This section explains how to use and develop the REST API.

### Run with Docker
You can run the REST API using a public [ppr Docker image] as follows:

```console
# run PPR REST API in a Docker container and access it on localhost:8080
$ docker run --name ppr-api -p 8080:8080 registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/ppr
```

### Configuration
The API will take into account the following environment variables:

| Name                  | Default                                                 | Description                                                                                                                                                                       |
|-----------------------|---------------------------------------------------------|------------------------------------------|
| `PPR_API_TITLE`       | "PPR API"                                               | API title.                               |
| `PPR_API_DESCRIPTION` | "Participant Provider Role API is used to obtain..."    | API description.                         |
| `PPR_API_VERSION`     | Version from SCM (e.g., 0.1.0dev7) or "unknown"         | API (semantic) version.                  |                                
| `PPR_API_DEBUG_MODE`  | "false"                                                 | Turns on API debug mode.                 |                                
| `PPR_API_SWAGGER_URL` | "/swagger"                                              | Enables Swagger UI (only in debug mode). |
| `PPR_API_REDOC_URL`   | "/redoc"                                                | Enables Redoc (only in debug mode).      |
| `ROOT_PATH`           | "/"                                                     | Root path for the API endpoints.         |

### Development
To start developing, you will first need to clone this repository.

```console
$ git clone git@gitlab.com:gaia-x/data-infrastructure-federation-services/orc/ppr.git
$ cd ppr
```

#### Building Docker image
You can build the Docker image locally and run it as follows:

```console
# build Docker container (it will take some time) 
$ docker build -t ppr-api .
# run PPR REST API in a Docker container and 
# navigate to localhost:8080/swagger or localhost:8080/redoc
$ docker run --name ppr-api -p 8080:8080 -e PPR_API_DEBUG_MODE="true" ppr-api
```

#### Running from source
To run the API locally from source:

```console
# install prerequisites
$ python3 -m venv .venv && . .venv/bin/activate
(.venv) $ pip install --upgrade pip 
(.venv) $ pip install -r requirements.txt
# run PPR REST API (add --reload flag to apply code changes on the way)
(.venv) $ PPR_API_DEBUG_MODE="true" uvicorn src.api:app
```

#### Testing
You can use `dev.sh` script to run tests locally, for example `./dev.sh lint` will run linters and `./dev.sh unit` will 
run unit tests.
You can explore all options with `./dev.sh help`.

#### CI/CD
GitLab CI/CD configuration is available in `.gitlab-ci.yml` file and contains the following stages:

* `lint`: checks code quality by running linters (on every push);
* `tests`: tests the API (on every push);
* `build`: build and push a Docker image to GitLab's Container Registry (on every push onto `main` branch Docker image 
            with `latest` tag is produced and on every Git tag push, we produce Docker image with the same tag);

## License
This work is licensed under the [Apache License 2.0].

## Contact
You can contact the XLAB's Gaia-X team by sending an email to [gaia-x@xlab.si].

[ppr Docker image]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/ppr/container_registry
[GXFS Documentation]: https://gaia-x.gitlab.io/data-infrastructure-federation-services/orc/documentation/
[gaia-x@xlab.si]: mailto:gaia-x@xlab.si
[Apache License 2.0]: https://www.apache.org/licenses/LICENSE-2.0
