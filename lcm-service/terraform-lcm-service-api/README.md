# Terraform API
An HTTP API interface for Terraform CLI - single user, single project, single deployment.

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation and Quickstart](#installation-and-quickstart)
  - [Run in Docker](#run-in-docker)
  - [Run locally from source](#run-locally-from-source)
  - [Use a Go package dependency](#use-a-go-package-dependency)
- [Development](#development)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)

## Introduction
This project contains an API to a Terraform exec library for management of a single deployment Terraform project.
It can be used to manage your single Terraform deployment environment inside a container.

## Prerequisites
Install [go] if you are running from source.

## Installation and Quickstart
This part explains how to run the Terraform API.
After that you will be able to call different API endpoints that correspond to Terraform CLI.

### Run in Docker
You can run the REST API using a public [terraform-lcm-service-api Docker image] as follows:

```console
# run Terraform REST API in a Docker container and 
# navigate to localhost:8080/swagger
$ docker run --name terraform-api -p 8080:8080 -v $(pwd)/tests/hello-world:/hello-world -e TERRAFORM_API_DEBUG_MODE=true -e TERRAFORM_API_WORKDIR=/hello-world registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api:latest
# deploy mounted hello world example
curl -X POST localhost:8080/apply
{"message":"Apply complete!","data":null}
```

Or you can build the image locally and run it as follows:

```console
# build Docker container (it will take some time) 
$ docker build -t terraform-api .
# run Terraform REST API in a Docker container and 
# navigate to localhost:8080/swagger
$ docker run --name terraform-api -p 8080:8080 -v $(pwd)/tests/hello-world:/hello-world -e TERRAFORM_API_DEBUG_MODE=true -e TERRAFORM_API_WORKDIR=/hello-world terraform-api
# deploy mounted hello world example
curl -X POST localhost:8080/apply
{"message":"Apply complete!","data":null}
```

### Run locally from source
After installing [go] use the following commands:

```console
# clone the Terraform API repo and download prerequisites
git clone git@gitlab.com:gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api.git
cd terraform-lcm-service-api
go mod download
# generate Swagger UI
swag init --parseDependency --parseInternal --parseDepth 1
# run Terraform REST API in a Docker container and 
# navigate to localhost:8080/swagger
TERRAFORM_API_DEBUG_MODE=true TERRAFORM_API_WORKDIR=$(pwd)/tests/hello-world go run main.go
# deploy hello world example
curl -X POST localhost:8080/apply
{"message":"Apply complete!","data":null}
```

### Use a Go package dependency
You can also use the API as a [terraform-lcm-service-api] GoLang package.

## Development
Install [go] and run from source.
You can use integration tests by running `go test -v --race ./api`.
To generate new OpenAPI spec run `swag init --parseDependency --parseInternal --parseDepth 1`.
You can also run in debug mode and use other env vars.

## Usage
The Terraform API is meant to use Terraform configuration from the current dir, so you have to either mount your IaC to
the Docker container and/or specify the working directory if you are running from source.
After that you can use different API endpoints:

```console
TERRAFORM_API_DEBUG_MODE=true TERRAFORM_API_WORKDIR=$(pwd)/tests/hello-world go run main.go
curl -X POST localhost:8080/init
curl -X POST localhost:8080/validate
curl -X POST localhost:8080/plan
curl -X POST localhost:8080/apply
curl -X POST localhost:8080/destroy
```

## License
This work is licensed under the [Mozilla Public License Version 2.0].

## Contact
You can contact the XLAB's Gaia-X team by sending an email to [gaia-x@xlab.si].

[go]: (https://go.dev/doc/install
[terraform-lcm-service-api]: https://pkg.go.dev/gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
[terraform-lcm-service-api Docker image]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-a/container_registry
[gaia-x@xlab.si]: mailto:gaia-x@xlab.si
[Mozilla Public License Version 2.0]: https://www.mozilla.org/en-US/MPL/2.0/
