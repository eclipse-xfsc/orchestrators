.. _Terraform LCM Service:

=====================
Terraform LCM Service
=====================

This part documents the Terraform LCM Service API.
The source code is available in `lcm-service/terraform-lcm-service-api`_ GitLab repository.

.. _Terraform LCM Service About:

-----
About
-----

**Terraform LCM Service** represented by the **Terraform API**.

Terraform API uses `terraform-exec`_ Go library for management of a single deployment Terraform project.
The API can manage just one state at a time (single user, single project, single deployment) and is a wrapper around
user's current orchestration environment, where his Terraform application is located.

The API is written in Go and licensed under `Mozilla Public License Version 2.0`_.

.. _Terraform LCM Service Installation and running:

------------------------
Installation and running
------------------------

Terraform API can be run in Docker or installed as a Go package.

.. tabs::
    .. tab:: Docker

        You can run Terraform API in a Docker container using `orc/lcm-service/terraform-lcm-service-api`_ Docker image
        and mount your files:

        .. code-block:: console

            $ docker run --name terraform-api -p 8080:8080 -v $(pwd)/tests/hello_world:/hello_world -e TERRAFORM_API_WORKDIR=/hello_world registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api:latest
            $ curl localhost:8080/version

    .. tab:: From source

        You can also run Terraform API from source GitLab repository.
        First ensure that you have Go installed.
        After that clone the repository and run from source.

        .. code-block:: console

            $ git clone git@gitlab.com:gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api.git
            $ cd terraform-lcm-service-api
            $ go mod download
            $ swag init
            $ TERRAFORM_API_WORKDIR=$(pwd)/tests/hello_world go run main.go
            $ curl localhost:8080/version

    .. tab:: Go package

        Terraform API is originally a GoLang package called `terraform-lcm-service-api`_ that is regularly published
        on `pkg.go.dev`_ and requires Go (install it from `go.dev`_).

        .. code-block:: console

            $ go get gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api

When running the API you can use the following environment variables:

- ``TERRAFORM_API_TERRAFORM_VERSION`` - sets Terraform version (default is 1.2.2)
- ``TERRAFORM_API_DEBUG_MODE`` - if `true` it will serve the OpenAPI Specification within Swagger UI
- ``TERRAFORM_API_SWAGGER_URL`` - path to Swagger UI (default is "swagger") if debug mode is on
- ``TERRAFORM_API_WORKDIR`` - absolute path to working directory to be used when the API starts
- ``TERRAFORM_API_PORT`` - API port (default is 8080)
- ``TERRAFORM_API_TRUSTED_PROXY`` - list of network origins (IP addresses) to trust (default is all)

.. _Terraform LCM Service API reference:

-------------
API reference
-------------

Terraform API exposes the following API endpoints:

+-------------------------------------------+--------------------------------------------------------------------------+
| REST API endpoint                         | Description                                                              |
+===========================================+==========================================================================+
| `GET /version`                            | Shows the current Terraform version                                      |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /show`                               | Shows the current state or a saved plan                                  |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /init`                              | Prepares your working directory for other commands                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /validate`                          | Checks whether the configuration is valid                                |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /plan`                              | Prepares your working directory for other commands                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /apply`                             | Create or update infrastructure                                          |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /destroy`                           | Destroys previously-created infrastructure                               |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /output`                             | Shows output values from your root module                                |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /fmt`                               | Reformats your configuration in the standard style                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /get`                               | Installs or upgrades remote Terraform modules                            |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /graph`                             | Generates a Graphviz graph of the steps in an operation                  |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /import`                            | Associates existing infrastructure with a Terraform resource             |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /force-unlock`                      | Releases a stuck lock on the current workspace                           |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /providers/lock`                    | Updates the dependency lock file to include a version for each provider  |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /providers/schema`                   | Shows the providers required for this configuration                      |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /state/mv`                          | Moves the remote objects                                                 |
+-------------------------------------------+--------------------------------------------------------------------------+
| `DELETE /state/rm`                        | Forgets the resource, while it continues to exist in the remote system   |
+-------------------------------------------+--------------------------------------------------------------------------+
| `DELETE /untaint`                         | Removes the tainted state from a resource instance                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /workspace/new`                     | Creates a new workspace                                                  |
+-------------------------------------------+--------------------------------------------------------------------------+
| `DELETE /workspace/delete`                | Deletes a workspace                                                      |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /workspace/select`                  | Select a workspace                                                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /workspace/show`                     | Shows the name of the current workspace                                  |
+-------------------------------------------+--------------------------------------------------------------------------+

For a detailed API reference see `OpenAPI Specification for Terraform LCM Service API`_.

.. _Terraform LCM Service Usage and examples:

------------------
Usage and examples
------------------

This part will show one deployment from the perspective of the user.

We first have to choose the IaC - i.e., TOSCA CSAR or TOSCA service template.
Let's deploy a `hello-world Terraform example`_ from `lcm-service/terraform-lcm-service-api`_ GitLab repository.

We will first clone the `lcm-service/terraform-lcm-service-api`_ GitLab repository and then run the Terraform API.
The Terraform API is meant to use Terraform IaC from the current dir, so you have to either mount your IaC to the Docker
container and/or specify the working directory if you are running from source.

.. code-block:: console

    $ git clone git@gitlab.com:gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api.git
    $ docker run --name terraform-api -p 8080:8080 -v $(pwd)/tests/hello_world:/hello_world -e TERRAFORM_API_DEBUG_MODE=true -e TERRAFORM_API_WORKDIR=/hello_world registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api:latest
    [GIN-debug] [WARNING] Creating an Engine instance with the Logger and Recovery middleware already attached.

    [GIN-debug] [WARNING] Running in "debug" mode. Switch to "release" mode in production.
     - using env:   export GIN_MODE=release
     - using code:  gin.SetMode(gin.ReleaseMode)

    [GIN-debug] POST   /init                     --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.initHandler (3 handlers)
    [GIN-debug] POST   /validate                 --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.validateHandler (3 handlers)
    [GIN-debug] POST   /plan                     --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.planHandler (3 handlers)
    [GIN-debug] POST   /apply                    --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.applyHandler (3 handlers)
    [GIN-debug] POST   /destroy                  --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.destroyHandler (3 handlers)
    [GIN-debug] POST   /fmt                      --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.fmtHandler (3 handlers)
    [GIN-debug] POST   /force-unlock             --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.forceUnlockHandler (3 handlers)
    [GIN-debug] POST   /get                      --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.getHandler (3 handlers)
    [GIN-debug] POST   /graph                    --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.graphHandler (3 handlers)
    [GIN-debug] POST   /import                   --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.importHandler (3 handlers)
    [GIN-debug] GET    /output                   --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.outputHandler (3 handlers)
    [GIN-debug] GET    /providers/schema         --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.providersSchemaHandler (3 handlers)
    [GIN-debug] POST   /providers/lock           --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.providersLockHandler (3 handlers)
    [GIN-debug] GET    /show                     --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.showHandler (3 handlers)
    [GIN-debug] DELETE /state/rm                 --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.stateRmHandler (3 handlers)
    [GIN-debug] POST   /state/mv                 --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.stateMvHandler (3 handlers)
    [GIN-debug] DELETE /untaint                  --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.untaintHandler (3 handlers)
    [GIN-debug] GET    /version                  --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.versionHandler (3 handlers)
    [GIN-debug] GET    /workspace/show           --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.workspaceShowHandler (3 handlers)
    [GIN-debug] GET    /workspace/list           --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.workspaceListHandler (3 handlers)
    [GIN-debug] POST   /workspace/select         --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.workspaceSelectHandler (3 handlers)
    [GIN-debug] POST   /workspace/new            --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.workspaceNewHandler (3 handlers)
    [GIN-debug] DELETE /workspace/delete         --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.workspaceDeleteHandler (3 handlers)
    [GIN-debug] GET    /swagger/*any             --> github.com/swaggo/gin-swagger.CustomWrapHandler.func1 (3 handlers)
    [GIN-debug] GET    /swagger.json             --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.SetupRouter.func1 (3 handlers)
    [GIN-debug] GET    /swagger.yaml             --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.SetupRouter.func2 (3 handlers)
    [GIN-debug] GET    /swagger                  --> gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/api.SetupRouter.func3 (3 handlers)
    [GIN-debug] [WARNING] You trusted all proxies, this is NOT safe. We recommend you to set a value.
    Please check https://pkg.go.dev/github.com/gin-gonic/gin#readme-don-t-trust-all-proxies for details.
    [GIN-debug] Listening and serving HTTP on :8080

After that you can use different API endpoints by calling ``localhost:8080``.
You can also navigate to ``localhost:8080/swagger`` and observe the Swagger UI API docs.
We will use ``curl`` for calling API endpoints.

1. Let's check the version of Terraform within the Terraform API.

.. code-block:: console

    $ curl -XGET localhost:8080/version
    {
      "message": "",
      "data": {
        "version": "1.2.2",
        "providers": {
          "registry.terraform.io/hashicorp/local": "2.2.2"
        }
      }
    }

2. After that let's check if our Terraform project is valid.

.. code-block:: console

    $ curl -XPOST localhost:8080/validate
    {
      "message": "Success! The configuration is valid.",
      "data": {
        "format_version": "1.0",
        "valid": true,
        "error_count": 0,
        "warning_count": 0,
        "diagnostics": []
      }
    }

3. Then we will inform ourselves about the current state.

.. code-block:: console

    $ curl -XGET localhost:8080/show
    {
      "message": "",
      "data": {
        "format_version": "1.0",
        "terraform_version": "1.2.2",
        "values": {
          "outputs": {
            "hello_output": {
              "sensitive": false,
              "value": "/tmp/playing-terraform/hello.txt has been created with content Terraform was here!."
            }
          },
          "root_module": {
            "resources": [
              {
                "address": "local_file.hello",
                "mode": "managed",
                "type": "local_file",
                "name": "hello",
                "provider_name": "registry.terraform.io/hashicorp/local",
                "schema_version": 0,
                "values": {
                  "content": "Terraform was here!",
                  "content_base64": null,
                  "directory_permission": "0777",
                  "file_permission": "0777",
                  "filename": "/tmp/playing-terraform/hello.txt",
                  "id": "73d2ed5802230f9cbd81805a856204068f83329b",
                  "sensitive_content": null,
                  "source": null
                },
                "sensitive_values": {}
              }
            ]
          }
        }
      }
    }

4. We can then initialize the project (downloads needed Terraform plugins).

.. code-block:: console

    $ curl -XPOST localhost:8080/init
    {
      "message": "Terraform has been successfully initialized!",
      "data": null
    }

5. Then we can apply the configuration and deploy the example as follows.

.. code-block:: console

    $ curl -XPOST localhost:8080/apply
    {
      "message": "Apply complete!",
      "data": null
    }

6. After that we can see the example output.

.. code-block:: console

    $ curl -XGET localhost:8080/output
    {
      "message": "",
      "data": {
        "output": {
          "hello_output": {
            "sensitive": false,
            "type": "string",
            "value": "/tmp/playing-terraform/hello.txt has been created with content Terraform was here!."
          }
        }
      }
    }

7. At last we can undeploy the solution.

.. code-block:: console

    $ curl -XPOST localhost:8080/destroy
    {
      "message": "Destroy complete!",
      "data": null
    }

And that's it.

.. tip::

    To test this LCM Service on real examples visit :ref:`Examples Terraform examples`.

.. _lcm-service/terraform-lcm-service-api: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
.. _terraform-exec: https://github.com/hashicorp/terraform-exec
.. _Mozilla Public License Version 2.0: https://www.mozilla.org/en-US/MPL/2.0/
.. _orc/lcm-service/terraform-lcm-service-api: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/container_registry/3080493
.. _terraform-lcm-service-api: https://pkg.go.dev/gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
.. _pkg.go.dev: https://pkg.go.dev/
.. _go.dev: https://go.dev/doc/install
.. _OpenAPI Specification for Terraform LCM Service API: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/-/blob/main/docs/swagger.yaml
.. _hello-world Terraform example: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/-/tree/main/tests/hello_world
