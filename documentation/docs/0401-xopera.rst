.. _TOSCA xOpera LCM Service:

========================
TOSCA xOpera LCM Service
========================

This part documents the TOSCA xOpera LCM Service API.
The source code is available in `lcm-service/tosca-xopera-lcm-service-api`_ GitLab repository.

.. _TOSCA xOpera LCM Service About:

-----
About
-----

**TOSCA xOpera LCM Service** represented by the **xOpera API**, which is originally located in `xlab-si/xopera-api`_
GitHub repository (and forked to `lcm-service/tosca-xopera-lcm-service-api`_).

xOpera API aims to be a lightweight xOpera orchestrator API.
`xOpera`_ is a project that includes a set of tools for advanced orchestration and comes with an orchestration tool
called **xOpera orchestrator** (or shorter **opera**).
**opera** aims to be a lightweight orchestrator compliant with `OASIS TOSCA`_ standard (the current compliance is with
the `TOSCA Simple Profile in YAML v1.3`_).
**opera** uses `Ansible`_ automation tool to implement the TOSCA standard and to run TOSCA interface operations using
Ansible playbooks.
You can find more information about xOpera in `xOpera documentation`_ and in `xlab-si/xopera-api`_ GitHub repository.

xOpera API is a wrapper around user's current orchestration environment, where he has his files and his version of
opera orchestrator and can manage just one state at a time (single user, single project, single deployment).

The API is written in Python and licensed under `Apache License 2.0`_.

.. _TOSCA xOpera LCM Service Installation and running:

------------------------
Installation and running
------------------------

xOpera API can be run in Docker or installed as a Python package.

.. tabs::
    .. tab:: Docker

        You can run xOpera API in a Docker container using `ghcr.io/xlab-si/xopera-api`_ Docker image and mount your
        files:

        .. code-block:: console

            $ docker run --name xopera-api -p 8080:8080 -v $(pwd)/hello-world:/hello-world ghcr.io/xlab-si/xopera-api
            $ curl localhost:8080/status

    .. tab:: Python package

        xOpera API is distributed as ``opera-api`` Python package that is regularly published on `PyPI`_ and
        `Test PyPI`_.
        ``opera-api`` requires python 3 (and a virtual environment).
        In a typical modern Linux environment, we should already be set.
        In Ubuntu, however, we might need to run the following commands:

        .. code-block:: console

            $ sudo apt update
            $ sudo apt install -y python3-venv python3-wheel python-wheel-common

        The simplest way to test ``opera-api`` is to install it into virtual environment:

        .. code-block:: console

            $ python3 -m venv .venv && . .venv/bin/activate
            (.venv) $ pip install opera-api
            (.venv) $ opera-api
            2022-04-04 12:45:34,097 - INFO - opera.api.cli - Running in production mode: tornado backend.

    .. tab:: From source

        You can also run xOpera API from source GitHub repository.
        First ensure that you have python 3 installed.
        After that clone the repository and run from source.

        .. code-block:: console

            $ git clone git@github.com:xlab-si/xopera-api.git
            $ cd xopera-api
            $ python3 -m venv .venv && . .venv/bin/activate
            (.venv) $ pip install -r requirements.txt requirements-dev.txt
            (.venv) $ pip install .
            (.venv) $ opera-api
            2022-04-04 12:45:34,097 - INFO - opera.api.cli - Running in production mode: tornado backend.

When running the API you can use the following environment variables:

- ``OPERA_API_DEBUG_MODE`` - if `true` it will also serve the OpenAPI Specification within Swagger UI
- ``OPERA_API_SWAGGER_URL`` - path to Swagger UI (default is "swagger") if debug mode is on
- ``OPERA_API_WORKDIR`` - absolute path to working directory to be used when the API starts
- ``OPERA_API_PORT`` - API port (default is 8080)

.. hint::

    Be careful when supplying environment variables and see the examples below.

    Supplying env vars while running Docker container should be done like this:

    .. code-block:: console

        $ docker run --name xopera-api -p 8080:9999 -v $(pwd)/my-tosca-csar:/my-tosca-csar \
          -e OPERA_API_DEBUG_MODE=true -e OPERA_API_SWAGGER_URL=docs -e OPERA_API_WORKDIR=/csar \
          -e OPERA_API_PORT=9999 ghcr.io/xlab-si/xopera-api

    When using the xOpera API Pyton package, you can supply variables like this

    .. code-block:: console

        (.venv) $ OPERA_API_DEBUG_MODE=true OPERA_API_SWAGGER_URL=docs OPERA_API_WORKDIR=/csar \
                  OPERA_API_PORT=9999 (.venv) $ opera-api

.. _TOSCA xOpera LCM Service API reference:

-------------
API reference
-------------

xOpera API exposes API endpoints that mimic CLI commands from opera orchestrator and are the following:

+-------------------------------------------+--------------------------------------------------------------------------+
| REST API endpoint                         | Description                                                              |
+===========================================+==========================================================================+
| `GET /version`                            | Get current version of opera orchestrator installed for the xOpera API   |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /info`                               | Get information about the current opera orchestration environment        |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /validate`                          | Validate TOSCA CSAR or TOSCA YAML service template                       |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /deploy`                            | Deploy TOSCA CSAR or TOSCA YAML service template                         |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /outputs`                            | Fetch deployment outputs                                                 |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /diff`                              | Do a diff between deployed and updated TOSCA service template            |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /update`                            | Do an update according to changes of currently deployed service template |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /notify/{trigger_name}`             | Do a notification and invoke triggers from TOSCA policies                |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /package`                           | Generate a TOSCA CSAR from a working directory.                          |
+-------------------------------------------+--------------------------------------------------------------------------+
| `POST /unpackage`                         | Unpackage a TOSCA CSAR.                                                  |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /status`                             | Fetch the status of a deployment or other operations                     |
+-------------------------------------------+--------------------------------------------------------------------------+
| `GET /status/{invocation_id}`             | Fetch the status of a particular invocation                              |
+-------------------------------------------+--------------------------------------------------------------------------+

For a detailed API reference see `OpenAPI Specification for TOSCA xOpera LCM Service API`_.

.. _TOSCA xOpera LCM Service Usage and examples:

------------------
Usage and examples
------------------

This part will show one deployment from the perspective of the user.

We first have to choose the IaC - i.e., TOSCA CSAR or TOSCA service template.
Let's deploy a `hello-world TOSCA example`_ from `xlab-si/xopera-examples`_ GitHub repository.

We will first clone the `xlab-si/xopera-examples`_ GitHub repository and then run the xOpera API.

.. tabs::
    .. tab:: Docker

        .. code-block:: console

            $ git clone git@github.com:xlab-si/xopera-examples.git
            $ cd xopera-examples
            $ docker run --name xopera-api -p 8080:8080 -v $(pwd)/misc/hello-world:/hello-world -e OPERA_API_DEBUG_MODE=true -e OPERA_API_WORKDIR=/hello-world ghcr.io/xlab-si/xopera-api

    .. tab:: Python package

        .. code-block:: console

            $ git clone git@github.com:xlab-si/xopera-examples.git
            $ cd xopera-examples
            (.venv) $ OPERA_API_DEBUG_MODE=true OPERA_API_WORKDIR=$(pwd)/misc/hello-world opera-api
            2022-07-14 07:58:08,040 - INFO - __main__ - Running in debug mode: flask backend.

After we have mounted the `hello-world` TOSCA CSAR, we can proceed with the API calls to ``localhost:8080``.
You can also navigate to ``localhost:8080/swagger`` and observe the Swagger UI API docs.
We will use ``curl`` for calling API endpoints.

1. Let's check the version of xOpera orchestrator.

.. code-block:: console

    $ curl -XGET localhost:8080/version
    "0.6.9"

2. Then we will inform ourselves about the current orchestration environment.

.. code-block:: console

    $ curl -XGET localhost:8080/info
    {
      "content_root": ".",
      "csar_valid": true,
      "service_template": "service.yaml",
      "service_template_metadata": {
        "template_author": "XLAB",
        "template_name": "hello-world",
        "template_version": "1.0"
      }
    }

3. After that let's check if our TOSCA CSAR is valid.

.. code-block:: console

    $ curl -XPOST localhost:8080/validate -H "Content-Type: application/json" -d '{"service_template": "service.yaml", "inputs": {}}'
    {
      "success": true
    }

4. Now we can deploy the example.

.. code-block:: console

    $ curl -XPOST localhost:8080/deploy -d '{"service_template": "service.yaml", "inputs": {}}'
    {
      "clean_state": false,
      "id": "1ac166b7-3866-4535-b89a-67c5e133bebc",
      "inputs": {},
      "operation": "deploy",
      "service_template": "service.yaml",
      "state": "pending",
      "timestamp": "2022-07-14T08:11:49.635318+00:00"
    }

5. Let's verify that the example has been deployed.

.. code-block:: console

    $ curl localhost:8080/info
    {
      "content_root": ".",
      "csar_valid": true,
      "inputs": {},
      "service_template": "service.yaml",
      "service_template_metadata": {
        "template_author": "XLAB",
        "template_name": "hello-world",
        "template_version": "1.0"
      },
      "status": "deployed"
    }

6. We can also obtain more details about the deployment.

.. code-block:: console

    $ curl -XGET localhost:8080/status/1ac166b7-3866-4535-b89a-67c5e133bebc
    {
      "clean_state": false,
      "id": "1ac166b7-3866-4535-b89a-67c5e133bebc",
      "inputs": {},
      "instance_state": {
        "hello": "started",
        "hello-host-my-workstation": "initial",
        "my-workstation": "started"
      },
      "operation": "deploy",
      "service_template": "service.yaml",
      "state": "success",
      "stderr": "",
      "stdout": "",
      "timestamp": "2022-07-14T08:11:49.635318+00:00"
    }

7. We can now undeploy our example.

.. code-block:: console

    $ curl -XPOST localhost:8080/undeploy
    {
      "clean_state": false,
      "id": "7cd8b99b-d8f8-4b51-925d-476989e2f0a8",
      "operation": "undeploy",
      "state": "pending",
      "timestamp": "2022-07-14T08:15:17.351850+00:00"
    }

8. Let's verify that the example has been undeployed.

.. code-block:: console

    $ curl -XGET localhost:8080/info
    {
      "content_root": ".",
      "csar_valid": true,
      "inputs": {},
      "service_template": "service.yaml",
      "service_template_metadata": {
        "template_author": "XLAB",
        "template_name": "hello-world",
        "template_version": "1.0"
      },
      "status": "undeployed"
    }

And that's it.

For more TOSCA examples visit `xlab-si/xopera-examples`_ GitHub repository and `xOpera documentation`_.
If you want to get in touch with `xOpera`_ team (from `XLAB <xlab.si>`_) you can send us an email at xopera@xlab.si.

.. tip::

    To test this LCM Service on real examples visit :ref:`Examples TOSCA examples`.

.. _lcm-service/tosca-xopera-lcm-service-api: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/tosca-xopera-lcm-service-api
.. _xOpera: https://www.xlab.si/solutions/orchestrator/
.. _xlab-si/xopera-api: https://github.com/xlab-si/xopera-api
.. _Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
.. _ghcr.io/xlab-si/xopera-api: https://github.com/xlab-si/xopera-api/pkgs/container/xopera-api
.. _opera-api: https://pypi.org/project/opera-api/
.. _PyPI: https://pypi.org/project/opera-api/
.. _Test PyPI: https://test.pypi.org/project/opera-api/
.. _OASIS TOSCA: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=tosca
.. _TOSCA Simple Profile in YAML v1.3: https://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.3/TOSCA-Simple-Profile-YAML-v1.3.html
.. _Ansible: https://www.ansible.com/
.. _xlab-si/xopera-opera: https://github.com/xlab-si/xopera-opera
.. _xOpera documentation: https://xlab-si.github.io/xopera-docs/
.. _OpenAPI Specification for TOSCA xOpera LCM Service API: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/tosca-xopera-lcm-service-api/-/blob/main/openapi-spec.yml
.. _xlab-si/xopera-examples: https://github.com/xlab-si/xopera-examples
.. _hello-world TOSCA example: https://github.com/xlab-si/xopera-examples/tree/master/misc/hello-world
