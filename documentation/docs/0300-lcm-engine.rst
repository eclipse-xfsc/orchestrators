.. _LCM Engine Introduction:

============
Introduction
============

This part covers the :term:`LCM Engine` architecture, API, and deployment of the corresponding server on Kubernetes. The source code is available in `orc/lcm-engine`_ GitLab repository.

--------------------------------------------

**LCM Engine** is the front part of the Gaia-X orchestration suite. It exposes an API through which various services can be deployed, undeployed and checked for deployment status. All the orchestration operations can be achieved through *LCM Engine* API.

RESTful by design, *LCM Engine* architecturally depends on a relational database to preserve and manage information about workspaces, secrets, users and projects. It orchestrates *LCM Services*, which, in turn, orchestrate application services. *LCM Services* differ in APIs and implementations, and know how to work with a specific orchestration environment, such as TOSCA or Terraform.

*LCM Engine*'s data model is composed of four main entities and their relations. These entities are users, workspaces, secrets and projects. Users can own and manage workspaces, secrets and projects. Workspaces associate users and secrets, and are containers for projects. Secrets store API keys and/or other credentials that might be required by an *LCM Service* in order to interact with cloud providers or other on-prem systems. A project is a representation of an *LCM Service* instance. When *LCM Engine* receives a request for a new project, the body of the request contains a ZIP package of manifests and scripts required to perform actual orchestration. *LCM Engine* deploys an associated *LCM Service*, passes the package and secrets to the *LCM Service*, and exposes an API that interacts with the *LCM Service* API.

*LCM Engine* is implemented in Python and Flask, and is licensed under `Apache License, Version 2.0`_.


.. _LCM Engine Installing and Running:

======================
Installing and Running
======================

*LCM Engine* can run as a server locally, as a Docker container or as a collection of Kubernetes resources. In either case, however, corresponding *LCM Services* that are managed by an *LCM Engine* are deployed on a Kubernetes cluster. In general, for full functionality, it is recommended to deploy *LCM Engine* on a Kubernetes cluster.

.. tabs::

    .. tab:: Local Deployment

        Local deployment is most useful for development purposes. *LCM Engine* can be run as any Python Flask server. It is recommended to install, activate and operate *LCM Engine* in a virtual environment, such as venv_. The engine has two requirements:

        - PostgreSQL database (can be deployed with Docker and Docker Compose),
        - Kubernetes configuration file.

        1. Deploy PostgreSQL Database

            The database can be deployed locally, in a Docker container, or we might use it as an external service. Here we describe how to deploy it with Docker Compose.

            Provide custom values in ``.env``, such as database name, username and password. Then run the database with Docker Compose:

            .. code-block:: console

                $ cp .env.example .env
                $ vim .env  # or use your favorite editor
                $ docker compose up -d lcm-engine-db

            The database is available at ``127.0.0.1:5432``.

        2. Deploy LCM Engine

            To deploy *LCM Engine* locally, install all the requirements and run the server. The Kubernetes configuration file is searched for in the standard location, e.g., ``~/.kube/config``.

            .. code-block:: console

                $ python3 -m pip install -r requirements.txt
                $ PYTHONPATH="$(pwd)" python3 lcm_engine/main.py

            See section `LCM Engine Environment Variables`_ for a list of environment variables that can be used to customize the server.


    .. tab:: Docker

        Docker image for *LCM Engine* can be built from the ``Dockerfile``. It is the most convenient to use Docker Compose. *LCM Engine* has two requirements:

        - PostgreSQL database and
        - Kubernetes configuration file.

        The Kubernetes configuration file is mounted from the host. Make sure it exists and provide its location in ``.env``. To deploy the database and *LCM Engine* with Docker Compose, run:

        .. code-block:: console

            $ cp .env.example .env
            $ vim .env  # or use your favorite editor
            $ docker compose up -d


    .. tab:: Kubernetes

        Deployment on Kubernetes requires administrative access to the cluster.

        1. Deploy *Traefik* Ingress Router
        
            *Traefik* can be used to:

                * route requests to the *LCM Engine* API server,
                * route requests to *LCM Services*,
                * protect the APIs with authorization (e.g., basic auth),
                * serve requests over HTTPs,
                * redirect HTTP requests to HTTPs and
                * obtain and renew Let's Encrypt X509 certificate.
                
            Please note that not all of the above features are required for *LCM Engine* to run properly; only the routing part is essential. *LCM Engine* assumes that *Traefik* is deployed as an ingress router implementing the Kubernetes operator pattern that exposes the *IngressRoute* and *Middleware* custom resources. It can be deployed with *Helm* and customized with a values file.

            Add Helm repository:

            .. code-block:: console

                $ helm repo add traefik https://helm.traefik.io/traefik
                $ helm repo update

            Customize the values file:

            .. code-block:: console

                $ cp k8s/traefik/helm/values.yaml.template \
                     k8s/traefik/values.yaml
                $ vim k8s/traefik/helm/values.yaml  # or use your favorite editor

            The template files were prepared with an assumption that all of the above listed features are enabled. Here we show the customization of parts that are likely to vary from one deployment to another.

            Configure domain name by setting ``ports.websecure.tls.domains`` as appropriate.

            Configure an X509 certificate resolver by setting the ``certResolvers`` section, especially the email part so that Let's Encrypt can notify you about certificate expiration.

            Provide storage class name in ``persistence.storageClass`` that supports the ``ReadWriteOnce`` access mode. This is used to store the Let's Encrypt certificate. The value should be one of the storage classes available in the cluster (obtained with ``kubectl get storageclass``).

            Deploy *Traefik*:

            .. code-block:: console

                $ helm install traefik traefik/traefik \
                    --version 20.6.0 \
                    --create-namespace \
                    --namespace traefik \
                    --values k8s/traefik/helm/values.yaml


        2. Deploy PostgreSQL Database

            Create the ``lcm-engine`` namespace:

            .. code-block:: console

                $ kubectl create namespace lcm-engine

            Configure the ``spec.storageClassName`` key in the ``k8s/lcm-engine-postgresql/pvc.yaml`` file to match the storage class name that supports the ``ReadWriteOnce`` access mode. This is used to store the database data.

            Configure the ``data.database`` key in the ``k8s/lcm-engine-postgresql/config-map.yaml`` file to provide custom database name. The default is ``lcm-engine``.

            .. code-block:: console

                $ cp k8s/lcm-engine-postgresql/secret.yaml.template \
                     k8s/lcm-engine-postgresql/secret.yaml

            Configure the ``data.username`` and ``data.password`` keys in the ``k8s/lcm-engine-postgresql/secret.yaml`` file to provide custom database username and password, respectively. These values should be base64 encoded.

            Deploy the database:

            .. code-block:: console

                $ kubectl create \
                    -f k8s/lcm-engine-postgresql/service.yaml \
                    -f k8s/lcm-engine-postgresql/pvc.yaml \
                    -f k8s/lcm-engine-postgresql/config-map.yaml \
                    -f k8s/lcm-engine-postgresql/secret.yaml \
                    -f k8s/lcm-engine-postgresql/deployment.yaml

        3. Deploy *LCM Engine*

            a. Configure users and HTTP basic auth

                To configure basic auth, create a *Secret* that encodes the information about users.

                .. code-block:: console
                    
                    $ cp k8s/lcm-engine/auth-secret.yaml.template \
                         k8s/lcm-engine/auth-secret.yaml

                Create a ``user:password`` pair by using ``htpasswd`` (comes as part of the `Apache httpd package`_) and encode it with ``base64``:

                .. code-block:: console

                    $ htpasswd -nb user password | base64
                    dXNlcjokYXByMSRUeGx3NUpnWCR2V21DQWFqM0w2bWJ2YXNrLlZvWnguCgo=

                For multiple users, call the ``htpasswd`` command for every user-password pair, place the result on a separate line each and base64 encode the concatenated lines.

                Copy the base64-encoded string and paste it into the ``data.users`` section of a *Secret* manifest:

                .. code-block:: yaml

                    # k8s/lcm-engine/auth-secret.yaml
                    apiVersion: v1
                    kind: Secret
                    metadata:
                        name: auth-secret
                        namespace: lcm-engine
                    data:
                        users: |2
                            dXNlcjokYXByMSRUeGx3NUpnWCR2V21DQWFqM0w2bWJ2YXNrLlZvWnguCgo=

                The ``users`` field contains the encoded ``user:password`` pair. This field is decoded by *Traefik* and used to authorize users.

                The middleware `k8s/lcm-engine/middleware.yaml` references this secret.

            b. Configure ingress routes

            .. code-block:: console

                $ cp k8s/lcm-engine/ingress-route-http.yaml.template \
                     k8s/lcm-engine/ingress-route-http.yaml
                $ cp k8s/lcm-engine/ingress-route-https.yaml.template \
                     k8s/lcm-engine/ingress-route-https.yaml

            Set domain name in the ``spec.routes[0].match`` key in files ``k8s/lcm-engine/ingress-route-http.yaml`` and ``k8s/lcm-engine/ingress-route-https.yaml``.

            The ingress route for HTTP entrypoint consumes the ``redirect-scheme`` middleware, which redirects all HTTP requests to HTTPS. The ingress route for HTTPS entrypoint consumes the ``basic-auth`` middleware, which authorizes users based on the ``auth-secret`` *Secret*.

            c. Configure PostgreSQL database connection

            .. code-block:: console

                $ cp k8s/lcm-engine/secret.yaml.template \
                     k8s/lcm-engine/secret.yaml

            Configure the ``data.db_connection_string`` key in the ``k8s/lcm-engine/secret.yaml`` file to provide the database host, name, port, username and password in the form of ``postgresql://<username>:<password>@<host>:<port>/<database>``. The host part is the name of the lcm-engine database *Service*, which is ``lcm-engine-db``. The connection string should be base64 encoded.

            d. Configure the kube config file

            Configure the ``data.kube-config`` key in the ``k8s/lcm-engine/secret.yaml`` file to provide the kube config file. The kube config file should be base64 encoded.
            
            e. Configure the kube config context

            Configure the ``spec.template.spec.containers[0].env[0].value`` key in the ``k8s/lcm-engine/deployment.yaml`` file to provide the kube config context. The kube config context should be the same as the one used in the kube config file.

            f. Configure the LCM Engine image

            Configure the ``spec.template.spec.containers[0].image`` key in the ``k8s/lcm-engine/deployment.yaml`` file to provide a custom LCM Engine image.

            g. Configure image pull secrets

            .. code-block:: console

                $ cp k8s/lcm-engine/docker-secret.yaml.template \
                     k8s/lcm-engine/docker-secret.yaml

            Provide Docker registry image pull secrets for accessing *LCM Engine* and **all** the *LCM Services'* images. Since *LCM Engine* deploys *LCM Services*, it needs to copy the Docker secret in the respective *LCM Service's* namespace. The Docker registry image pull secrets should be base64 encoded. The value can be copied from the ``~/.docker/config.json`` file, which becomes populated after running the ``docker login <registry-host>`` command. This is not necessary if all the images are public or if the registry does not require authentication or if the registry credentials are provided by some other means, e.g., on the cluster level.

            h. Deploy the *LCM Engine*

            .. code-block:: console

                $ kubectl create \
                    -f k8s/lcm-engine/docker-secret.yaml \
                    -f k8s/lcm-engine/secret.yaml \
                    -f k8s/lcm-engine/auth-secret.yaml \
                    -f k8s/lcm-engine/service.yaml \
                    -f k8s/lcm-engine/middleware.yaml \
                    -f k8s/lcm-engine/middleware-http2https.yaml \
                    -f k8s/lcm-engine/ingress-route-http.yaml \
                    -f k8s/lcm-engine/ingress-route-https.yaml \
                    -f k8s/lcm-engine/deployment.yaml

.. _`LCM Engine Environment Variables`:

---------------------
Environment Variables
---------------------

When running the API you can use the following environment variables:

- ``RUNTIME_ENVIRONMENT`` - set to ``local`` for local or Docker deployments. This type expects the access to a   Kubernetes cluster configured in the same way as ``kubectl``. Other acceptable values are ``k8s`` and ``kubernetes``, both having the same meaning. In this case, Kubernetes API is authenticated and authorized through a ``ServiceAccount`` and RBAC roles, giving the *LCM Engine* more fine-grained and restricted access to the Kubernetes cluster and is therefore recommended for production deployments.
- ``LCM_ENGINE_KUBE_CONFIG_PATH`` - path to the kubeconfig file. Used only when ``RUNTIME_ENVIRONMENT`` is ``local``.
- ``LCM_ENGINE_KUBE_CONFIG_CONTEXT`` - specifies context to use for ``kubeconfig`` files that define several contexts.
- ``LCM_ENGINE_DB_CONNECTION_STRING`` - relational database connection string, containing database protocol, hostname, port, username, password and connection.

.. _LCM Engine API Reference:

=============
API Reference
=============

*LCM Engine* API is a composition of two APIs. The first part of the API is specific to the *LCM Engine* and is common to all *LCM Engines*. This API manages users, secrets and workspaces. The second part of the API depends on the API of the respective *LCM Service* it is bound to. This API manages projects and for the most part passes requests to the respective *LCM Service*. This is planned to be changed in future versions such that *LCM Engine* has only one and stable API, while with helper services it will be able to delegate the *LCM Service* specific requests to the respective *LCM Service*.

.. _LCM Engine API Reference Status:

------
Status
------

Check operation status of *LCM Engine* and its related services.

+--------+-------------------+----------------------------------------------------------------------------------+
| Method | REST API Endpoint | Description                                                                      |
+========+===================+==================================================================================+
| GET    | ``/health``       | Get *LCM Engine*'s health status: checks connectivity with the database and k8s. |
+--------+-------------------+----------------------------------------------------------------------------------+

.. _LCM Engine API Reference Secrets:

-------
Secrets
-------

Work with secrets.

+--------+--------------------------------------------------+----------------------------------------------------------------------------------------+
| Method | REST API Endpoint                                | Description                                                                            |
+========+==================================================+========================================================================================+
| GET    | ``/secret``                                      | List user's secrets.                                                                   |
+--------+                                                  +----------------------------------------------------------------------------------------+
| POST   |                                                  | Create a new user's secret.                                                            |
+--------+--------------------------------------------------+----------------------------------------------------------------------------------------+
| GET    | ``/secret/{secretId}``                           | Describe user's secret identified by ``secretId``.                                     |
+--------+                                                  +----------------------------------------------------------------------------------------+
| PATCH  |                                                  | Update user's secret identified by ``secretId``.                                       |
+--------+                                                  +----------------------------------------------------------------------------------------+
| DELETE |                                                  | Delete user's secret identified by ``secretId``.                                       |
+--------+                                                  +----------------------------------------------------------------------------------------+
| PUT    |                                                  | Replace user's secret identified by ``secretId``.                                      |
+--------+--------------------------------------------------+----------------------------------------------------------------------------------------+
| GET    | ``/workspace/{workspaceId}/secret``              | List secrets assigned to the workspace identified by ``workspaceId``.                  |
+--------+--------------------------------------------------+----------------------------------------------------------------------------------------+ 
| PUT    | ``/workspace/{workspaceId}/secret/{secretId}``   | Assign secret with ID ``secretId`` to the workspace identified by ``workspaceId``.     |
+--------+                                                  +----------------------------------------------------------------------------------------+
| DELETE |                                                  | Remove secret with ID ``secretId`` from the workspace identified by ``workspaceId``.   |
+--------+--------------------------------------------------+----------------------------------------------------------------------------------------+

.. _LCM Engine API Reference Users:

-----
Users
-----

Work with users.

+--------+----------------------------------------------+-----------------------------------------------------------------------------------+
| Method | REST API Endpoint                            | Description                                                                       |
+========+==============================================+===================================================================================+
| POST   | ``/auth/logout``                             | Log out the current user.                                                         |
+--------+----------------------------------------------+-----------------------------------------------------------------------------------+
| GET    | ``/auth/status``                             | Get user's authentication status.                                                 |
+--------+----------------------------------------------+-----------------------------------------------------------------------------------+
| PUT    | ``/workspace/{workspaceId}/authorizations``  | Authorize the logged-in user to the workspace identified by ``workspaceId``.      |
+--------+                                              +-----------------------------------------------------------------------------------+
| GET    |                                              | List users authorized to the workspace identified by ``workspaceId``.             |
+--------+                                              +-----------------------------------------------------------------------------------+
| DELETE |                                              | Deauthorize the logged-in user from the workspace identified by ``workspaceId``.  |
+--------+----------------------------------------------+-----------------------------------------------------------------------------------+

.. _LCM Engine API Reference Workspaces:

----------
Workspaces
----------

Work with workspaces.

+--------+-------------------------------+-----------------------------------------------------------+
| Method | REST API Endpoint             | Description                                               |
+========+===============================+===========================================================+
| GET    | ``/workspace``                | List user's workspaces.                                   |
+--------+                               +-----------------------------------------------------------+ 
| POST   |                               | Create a new user's workspace.                            |
+--------+-------------------------------+-----------------------------------------------------------+
| GET    | ``/workspace/{workspaceId}``  | Describe user's workspace identified by ``workspaceId``.  |
+--------+                               +-----------------------------------------------------------+
| DELETE |                               | Delete user's workspace identified by ``workspaceId``.    |
+--------+                               +-----------------------------------------------------------+
| PATCH  |                               | Update user's workspace identified by ``workspaceId``.    |
+--------+                               +-----------------------------------------------------------+
| PUT    |                               | Replace user's workspace identified by ``workspaceId``.   |
+--------+-------------------------------+-----------------------------------------------------------+

.. _LCM Engine API Reference Projects:

--------
Projects
--------

Work with projects (and hence with *LCM Services*). All projects are defined within a workspace identified by ``workspaceId``.

+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+
| Method | REST API Endpoint                                               | Description                                                            |
+========+=================================================================+========================================================================+
| POST   | ``/workspace/{workspaceId}/project``                            | Create a new project and deploy a corresponding *LCM Service*.         |
+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+ 
| DELETE | ``/workspace/{workspaceId}/project/{projectId}``                | Delete user's project and undeploy the corresponding *LCM Service*.    |
+--------+                                                                 +------------------------------------------------------------------------+
| PATCH  |                                                                 | Update user's project.                                                 |
+--------+                                                                 +------------------------------------------------------------------------+
| GET    |                                                                 | Describe user's project.                                               |
+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+
| GET    | ``/workspace/{workspaceId}/project/{projectId}/creationStatus`` | Get creation status of user's project.                                 |
+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+
| GET    | ``/workspace/{workspaceId}/project/{projectId}/debugPackage``   | Get log outputs as a ZIP archive from the corresponding *LCM Service*. |
+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+
| GET    | ``/workspace/{workspaceId}/project/{projectId}/health``         | Get project's health.                                                  |
+--------+-----------------------------------------------------------------+------------------------------------------------------------------------+

.. _LCM Engine API Reference TOSCA LCM Service:

-----------------
TOSCA LCM Service
-----------------

Work with projects specific to *TOSCA LCM Services*. The base URI path for all the API endpoints is ``/workspace/{workspaceId}/project/{projectId}``. The endpoints defined by `TOSCA LCM Service API`_ are appended to the end of the base path, e.g., ``/workspace/{workspaceId}/project/{projectId}/deploy``.

.. _LCM Engine API Reference Terraform LCM Service:

---------------------
Terraform LCM Service
---------------------

Work with projects specific to *Terraform LCM Services*. The base URI path for all the API endpoints is ``/workspace/{workspaceId}/project/{projectId}``. The endpoints defined by `Terraform LCM Service API`_ are appended to the end of the base path, e.g., ``/workspace/{workspaceId}/project/{projectId}/apply``.

.. _LCM Engine Usage and Examples:

==================
Usage and Examples
==================

This part shows various aspects of using the *LCM Engine* API. It walks us through the creation of workspaces, secrets and projects, which in turn leads to the deployment of *LCM Services*. Then it leverages on *LCM Service*'s API to orchestrate an application: to deploy it, check its health and status, and undeploy it.

The guide demonstrates the orchestration with two applications, each specified in a different orchestration language. First application is a simple hello-world application, and uses TOSCA specification language and the *TOSCA LCM Service* to perform file write operation. Second application deploys a web page on IONOS Cloud, and uses Terraform specification language and the *Terraform LCM Service* to provision a virtual machine and to install Nginx on it.

-------------------------
Preparing the Environment
-------------------------

Let us prepare the environment which will facilitate the use of ``curl``.

.. note::

  *LCM Engine* is aware of users. It reads the information about current user from the ``X-Forwarded-User`` HTTP header. However, the *LCM Engine* itself does not perform authorization. If this is required, the *LCM Engine* should be fronted by a reverse-proxy (e.g., Traefik) that is capable of performing user authorization, such as with HTTP basic auth. In this case the reverse-proxy is assumed to copy the user from the ``Authorization`` header into the ``X-Forwarded-User`` header.

Let us assume that the *LCM Engine* is already deployed and its API is accessible on ``$LCM_ENGINE_HOST``. Depending on whether *LCM Engine* is fronted by a reverse-proxy configured with HTTP basic auth or not, we can define alias for ``curl`` named ``lcm_curl`` with the following parameters:

.. tabs::

  .. tab:: Without Authorization

    In a request we provide information about a user by explicitly setting the ``X-Forwarded-User`` HTTP header.

    .. code-block:: console

      alias lcm_curl="curl -H 'X-Forwarded-User: demo.user@example.com' -H 'Content-Type: application/json'"

  .. tab:: With HTTP Basic Auth Authorization

    In a request we provide authorization information, which contains a user and the credentials. A reverse-proxy is responsible for copying the user information from the ``Authorization`` header to the ``X-Forwarded-User`` header.

    .. code-block:: console

      alias lcm_curl="curl --basic --user demo.user@example.com:password -H 'Content-Type: application/json'"

---------------
Checking Status
---------------

^^^^^^^^^^^^
Check health
^^^^^^^^^^^^

To check if the *LCM Engine* is up and running we can call the ``/health`` API endpoint:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/health"

.. code-block:: json

  {
    "dependencies": [
      {
        "healthy": true,
        "name": "database"
      },
      {
        "healthy": true,
        "name": "k8s"
      }
    ],
    "healthy": true,
    "name": "application"
  }

A healthy connectivity means that *LCM Engine* can successfully communicate with the k8s API. Similarly, database connectivity is healthy if *LCM Engine* can communicate with its associated PostgreSQL database. Both dependencies are hard requirements for *LCM Engine*, meaning that it cannot operate properly if any of the dependencies are unhealthy. Application is healthy if both, connectivity and database are healthy.

^^^^^^^^^^^^^^^^^^^^^^^^^^
Check Authorization Status
^^^^^^^^^^^^^^^^^^^^^^^^^^

We can ask *LCM Engine* about the current user:

.. code-block:: console

    $ lcm_curl "$LCM_ENGINE_HOST/auth/status"

.. code-block::

    {
      "isLoggedIn": true,
      "userIdentifier": "demo.user@example.com"
    }

------------------------
Orchestrating with TOSCA
------------------------

We want to deploy a simple `hello-world TOSCA example`_ that upon deployment writes a string into a temporary file and upon undeployment deletes it. To achieve this, we want to use TOSCA as specification language and Ansible to perform operations. To fulfil this requirement, we need to deploy *TOSCA LCM Service* and then use it to orchestrate the application with TOSCA and Ansible.

^^^^^^^^^^^^^^^^^^^^^^
Create TOSCA Workspace
^^^^^^^^^^^^^^^^^^^^^^

First, we need to create a new workspace:

.. code-block:: console

    $ lcm_curl --data '{"name": "TOSCA workspace"}' "$LCM_ENGINE_HOST/workspace"

.. code-block:: json

    {
      "id": 1,
      "isOwner": true,
      "name": "TOSCA workspace",
      "projects": [],
      "secrets": []
    }

The response tells us that:

- the workspace has ID 1 (it might be different in your case) and name "TOSCA workspace",
- we are the workspace's owners and
- the workspace has no projects or secrets associated.

Let us assign the workspace's id into variable ``WORKSPACE_ID`` for future reference:

.. code-block:: console

    $ export WORKSPACE_ID=1


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Create Hello-World TOSCA Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we create a new project of kind ``si.xlab.lcm-service.tosca``, which will deploy the *TOSCA LCM Service* on the configured Kubernetes cluster. Besides the project name and kind, we also have to specify the deployment package, which is a base64-encoded ZIP file containing all the required files for the deployment. In TOSCA's parlance such package is known as *Cloud Service Archive (CSAR)*.

To simplify package preparation steps, we will download the `hello-world TOSCA example`_, base64 encode it and use it in the project specification.


+++++++++++++++++++++++++++++++++++++++
Download Hello-World TOSCA Example CSAR
+++++++++++++++++++++++++++++++++++++++

First we download the ZIP file.

.. code-block:: console

  $ curl -s -o hello-world.zip "https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/archive/main/examples-main.zip?path=tosca/hello-world/iac"


+++++++++++++++++++++++++++++++++++++++++++++++++++
Change Hello-World TOSCA CSAR's Directory Structure
+++++++++++++++++++++++++++++++++++++++++++++++++++

The ZIP archive contains file ``service.yaml``, which is the main (and only) TOSCA entrypoint, and Ansible playbooks with create and delete operations.

.. code-block:: console

  $ zipinfo -1 hello-world.zip

.. code-block:: console

  examples-main-tosca-hello-world-iac/
  examples-main-tosca-hello-world-iac/tosca/
  examples-main-tosca-hello-world-iac/tosca/hello-world/
  examples-main-tosca-hello-world-iac/tosca/hello-world/iac/
  examples-main-tosca-hello-world-iac/tosca/hello-world/iac/playbooks/
  examples-main-tosca-hello-world-iac/tosca/hello-world/iac/playbooks/create.yaml
  examples-main-tosca-hello-world-iac/tosca/hello-world/iac/playbooks/delete.yaml
  examples-main-tosca-hello-world-iac/tosca/hello-world/iac/service.yaml

However, to be able to use this package as a CSAR for the *TOSCA LCM Service*, we need to slightly change its directory structure: omit the preceding directories in the ZIP file, such that the ``service.yaml`` file is at the root, like this:

.. code-block:: console

  playbooks/create.yaml
  playbooks/delete.yaml
  service.yaml

One way to achieve this is to extract the flattened content and create new ZIP file with the correct structure.

.. code-block:: console

  $ mkdir -p csar/playbooks && \
    unzip -j hello-world.zip -d csar/playbooks && \
    mv csar/playbooks/service.yaml csar && \
    cd csar && \
    zip -r ../hello-world-csar.zip . && \
    cd .. && \
    rm -rf csar

The new ZIP file has the correct structure:

.. code-block:: console

  $ zipinfo -1 hello-world-csar.zip

.. code-block:: console

  service.yaml
  playbooks/
  playbooks/create.yaml
  playbooks/delete.yaml


++++++++++++++++++++++++++++++++++++
Base64 Encode Hello-World TOSCA CSAR
++++++++++++++++++++++++++++++++++++

We base64 encode the ZIP file:

.. code-block:: console

  $ base64 -w 0 hello-world-csar.zip > hello-world-csar.zip.base64


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Prepare Project Creation Request Body for Hello-World TOSCA
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To create a new project, we need to prepare a JSON with the following structure:

.. code-block:: json

  {
    "name": "hello-world",
    "kind": "si.xlab.lcm-service.tosca",
    "csar": "<base64-encoded csar>"
  }

Here, the ``jq`` tool comes in handy.

.. code-block:: console
  
  $ jq -r -n -M \
    --arg name "hello-world TOSCA" \
    --arg kind "si.xlab.lcm-service.tosca" \
    --arg csar $(cat hello-world-csar.zip.base64) \
    '{name: $name, kind: $kind, csar: $csar}' > hello-world-project.json


+++++++++++++++++++++++++++++++++++++++++++++++++
Get Project Creation Status for Hello-World TOSCA
+++++++++++++++++++++++++++++++++++++++++++++++++

To create a new project, make a POST request towards the ``/workspace/{workspaceId}/project`` endpoint:

.. code-block:: console

  $ lcm_curl --data @hello-world-project.json "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project"

.. code-block:: json

  {
    "id": 1
  }

If everything goes well, the response returns the ID (assuming it was 1) of a newly created project. Let us save it for a later reference:

.. code-block:: console

  $ export PROJECT_ID=1


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Obtaining Information about Hello-World TOSCA Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*LCM Engine* maintains and manages various information about a project. We may obtain project details, its creation status and health.


+++++++++++++++++++++++++++++++++++++
Get Hello-World TOSCA Project Details
+++++++++++++++++++++++++++++++++++++

The above response returned just the ID. We can ask for more details:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID"

.. code-block:: json

  {
    "id": 1,
    "kind": "si.xlab.lcm-service.tosca",
    "name": "hello-world TOSCA",
    "workspace": 1
  }


+++++++++++++++++++++++++++++++++++++++++++++
Get Hello-World TOSCA Project Creation Status
+++++++++++++++++++++++++++++++++++++++++++++

Since the project creation deploys an *LCM Service* on a Kubernetes cluster, it may take some time before the respective *LCM Service* becomes ready to serve HTTP requests, especially at first time, because this might require pulling *LCM Service*'s Docker image. We can check the project creation status:

.. code-block:: console

$ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/creationStatus"

.. code-block:: json

  {
    "finished": true,
    "status": "Running"
  }

Once the *status* becomes *Running*, it means that the respective *LCM Service*'s Pod is in the running state. If *finished* is *false*, it indicates that the project creation was not successful.


++++++++++++++++++++++++++++++++++++
Get Hello-World TOSCA Project Health
++++++++++++++++++++++++++++++++++++

Let us check the project's health:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/health"

.. code-block:: json

  {
    "connectivity": "layer5",
    "container": "running"
  }

The response tells us that the *LCM Service*'s container is running and that the *LCM Engine* can communicate with it over HTTP.


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Orchestrate with *TOSCA LCM Service*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From now on, we can call the `TOSCA LCM Service API`_ through the *LCM Engine*'s API. With the exception of a few resources, such as *creationStatus*, *debugPackage* and *health*, which *LCM Engine* responds to by itself, the API is exposed over the ``/workspace/$WORKSPACE_ID/project/$PROJECT_ID`` endpoint.


+++++++++++++++++++++++++++++++++
Get *TOSCA LCM Service*'s Version
+++++++++++++++++++++++++++++++++

To check if the *TOSCA LCM Service* actually responds to API requests, let us ask about its version:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/version"

.. code-block:: console

  "0.6.9"

.. note::

  Even though the *TOSCA LCM Service* is running and we specified the CSAR when we created the respective project, the deployment instructions within the CSAR itself have not been followed yet. Instead, what happened was that the *LCM Engine* deployed the *TOSCA LCM Service* on the configured Kubernetes cluster and prepared the directory structure for the *TOSCA LCM Service*, such that API calls towards the *LCM Service* can do some actual work with the CSAR. In other words, the *LCM Engine* extracted the CSAR ZIP file into a certain directory within the *TOSCA LCM Service*'s Pod.


+++++++++++++++++++++++++++++
Deploy Hello-World TOSCA CSAR
+++++++++++++++++++++++++++++

To execute the code inside the CSAR, we have to explicitly instruct the *TOSCA LCM Service* (or any other *LCM Service* in general) to deploy it.

.. code-block:: console

  $ lcm_curl --data '{"inputs": {}, "service_template": "service.yaml", "clean_state": true}' "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/deploy"

.. code-block:: json

  {
    "clean_state": true,
    "id": "609b0547-c226-4265-9f14-489dd274bfae",
    "inputs": {},
    "operation": "deploy",
    "service_template": "service.yaml",
    "state": "pending",
    "timestamp": "2022-09-15T16:14:34.034559+00:00"
  }

In the request we instructed the *TOSCA LCM Service* to:

- read the TOSCA service template specified in the file ``service.yaml`` of the CSAR,
- start with the clean state and
- use the default inputs (i.e., no inputs were given).

The *TOSCA LCM Service* responded that the deployment is in the *pending* state.


+++++++++++++++++++++++++++++++++++++++
Get Hello-World TOSCA Deployment Status
+++++++++++++++++++++++++++++++++++++++

We can ask about the deployment status to see if it has changed from the *pending* state:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/status"

.. code-block:: json

  [
    {
      "clean_state": true,
      "id": "609b0547-c226-4265-9f14-489dd274bfae",
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
      "timestamp": "2022-09-15T16:14:34.034559+00:00"
    }
  ]

The state is *success*, meaning that the deployment has been successful. There is yet another way to ask the *TOSCA LCM Service* about its status:

.. code-block:: console
  
  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/info"

.. code-block:: json

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

Besides the status, the *TOSCA LCM Service*'s ``/info`` resource gives some other useful information about the CSAR, such as template's author and version.

.. hint::

  Aside from the *TOSCA LCM Service*'s claims that the deployment has been successful, is there any other visible result of the deployment? The answer is: "there is", but it depends on the CSAR what the result should be.


++++++++++++++++++++++++++++++++++++++++++++
Verify Hello-World TOSCA Deployment with K8s
++++++++++++++++++++++++++++++++++++++++++++

In this simple example the deployment created file ``/tmp/playing-opera/hello/hello.txt`` in the *TOSCA LCM Service* Pod's file system with the content "default-marker". If we have administrative access to the Kubernetes cluster, and the ``kubectl`` tool installed and configured, we can check this with the following commands:

.. code-block:: console

  $ POD_NAME=$(kubectl get pods --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -o jsonpath='{ .items[0].metadata.name }'); \
    kubectl exec "$POD_NAME" -c tosca --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -- cat /tmp/playing-opera/hello/hello.txt

.. code-block:: console

    default-marker


+++++++++++++++++++++++++++++++
Undeploy Hello-World TOSCA CSAR
+++++++++++++++++++++++++++++++

We now undeploy the CSAR:

.. code-block:: console

  $ lcm_curl -X POST "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/undeploy"

.. code-block:: json

  {
    "clean_state": false,
    "id": "86f90081-6fc4-48e2-8e7f-3df0f4521dd6",
    "operation": "undeploy",
    "state": "pending",
    "timestamp": "2022-09-15T17:22:32.143809+00:00"
  }

and check the status until not finished.

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/status"

.. code-block:: json

  [
    {
      "clean_state": false,
      "id": "86f90081-6fc4-48e2-8e7f-3df0f4521dd6",
      "instance_state": {
        "hello": "initial",
        "hello-host-my-workstation": "initial",
        "my-workstation": "initial"
      },
      "operation": "undeploy",
      "state": "success",
      "stderr": "",
      "stdout": "**REDACTED**",
      "timestamp": "2022-09-15T17:22:32.143809+00:00"
    },
    {
      "clean_state": true,
      "id": "609b0547-c226-4265-9f14-489dd274bfae",
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
      "timestamp": "2022-09-15T16:14:34.034559+00:00"
    }
  ]

.. note::
  
  In the response, the first element of the list is the most recent one. It shows that the CSAR has been successfully undeployed. The *stdout* field of the first object was redacted for brevity. This field contains the strings that the xOpera has printed to the standard output.

After calling the ``undeploy`` endpoint, we expect that file ``/tmp/playing-opera/hello/hello.txt`` in the *TOSCA LCM Service* Pod's file system was deleted. Let us see:

.. code-block:: console

  $ POD_NAME=$(kubectl get pods --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -o jsonpath='{ .items[0].metadata.name }') \
    kubectl exec "$POD_NAME" -c tosca --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -- cat /tmp/playing-opera/hello/hello.txt

.. code-block:: console

  cat: can't open '/tmp/playing-opera/hello/hello.txt': No such file or directory
  command terminated with exit code 1


+++++++++++++++++++++++++++++++++++++++++++++++
Deploy Hello-World TOSCA CSAR with Custom Input
+++++++++++++++++++++++++++++++++++++++++++++++

We can now deploy the same CSAR again, this time with a different input. We want that the file content would be "custom-marker". This can be specified in the *inputs* attribute of the request's JSON body:

.. code-block:: console

  $ lcm_curl --data '{"inputs": {"marker": "custom-marker"}, "service_template": "service.yaml", "clean_state": true}' "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID/deploy"

.. code-block:: json

  {
    "clean_state": true,
    "id": "9c69e263-32be-440c-a3fb-fc32146ae5a5",
    "inputs": {
      "marker": "custom-marker"
    },
    "operation": "deploy",
    "service_template": "service.yaml",
    "state": "pending",
    "timestamp": "2022-09-15T17:53:43.002108+00:00"
  }

The response shows the inputs that we provided in the request. After state *success* is achieved, we can again print the file's content to see if we get the expected result:

.. code-block:: console

  $ POD_NAME=$(kubectl get pods --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -o jsonpath='{ .items[0].metadata.name }') \
    kubectl exec "$POD_NAME" -c tosca --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -- cat /tmp/playing-opera/hello/hello.txt

.. code-block:: console

  custom-marker

.. note::

  Whether the deployment package can be customized or not and how depends on the service template itself. In our case this is defined in the TOSCA ``service.yaml`` template.

.. important::

  When we no longer need the deployed CSAR, we undeploy it. For this, we use the undeploy API endpoint of a respective *LCM Service*. Please note that for this simple hello-world example the undeployment only deletes a file in the LCM Service Pod's file system and is therefore not crucial to call it. But in a more realistic scenario the undeployment might release acquired resources in a Cloud environment. Hence, always remember to undeploy a CSAR first before destroying the respective *LCM Service*.


^^^^^^^^^^^^^^^^^^^^^^^^^^
Undeploy TOSCA LCM Service
^^^^^^^^^^^^^^^^^^^^^^^^^^

To undeploy the *TOSCA LCM Service* itself (after we have undeployed the CSAR), we can issue the following request:

.. code-block:: console

  $ lcm_curl -X DELETE "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project/$PROJECT_ID"

It releases all the Kubernetes cluster's resources acquired by the *TOSCA LCM Service*. We can no longer use the *LCM Service*.


^^^^^^^^^^^^^^^^^^^^^^
Delete TOSCA Workspace
^^^^^^^^^^^^^^^^^^^^^^

We may delete the workspace too, following a similar pattern:

.. code-block:: console

    $ lcm_curl -X DELETE "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID"


----------------------------
Orchestrating with Terraform
----------------------------

Now that we know the basics, let us continue with a more complex example. We are going to create a Terraform project and with it deploy a web page on IONOS Cloud. Compared to the hello-world example, two things will be different:

1. we are going to use the *Terraform LCM Service*,
2. we need to provide the credentials in order to access the IONOS Cloud.


^^^^^^^^^^^^^^^^^^^^^^^^^^
Create Terraform Workspace
^^^^^^^^^^^^^^^^^^^^^^^^^^

Let us create a new workspace.

.. code-block:: console

  $ lcm_curl --data '{"name": "Terraform workspace"}' "$LCM_ENGINE_HOST/workspace"

.. code-block:: json

  {
    "id": 2,
    "isOwner": true,
    "name": "Terraform workspace",
    "projects": [],
    "secrets": []
  }

Store the workspace ID (assuming it is 2) for future reference.

.. code-block:: console

  $ export WORKSPACE_ID=2


^^^^^^^^^^^^^^^^^^^^^^^
Create Terraform Secret
^^^^^^^^^^^^^^^^^^^^^^^

Now create a secret, which in *LCM Engine* represents a file or an environment variable with potentially confidential information. In this example we use a file secret. It has to meet two requirements:

* it should be structured in a way that Terraform understands them and
* it must be placed in a path where Terraform is going to search for them.

`One possible way <https://registry.terraform.io/providers/ionos-cloud/ionoscloud/latest/docs>`_ is to define a ``.tf`` file with the following content:

.. code-block:: console

  $ base64 -w 0 << EOF > ionos-credentials.tf
  provider "ionoscloud" {
    username = "noname@ionos.com"
    password = "k33pm353cr3t!"
  }
  EOF

The request body for creation of a file secret has the following structure:

.. code-block:: json

  {
    "name": "Secret's name",
    "file": {
      "path": "/path/to/a/provider/file/credentials.tf",
      "contents": "<base64-encoded file secret content>"
    }
  }

We may use ``jq`` to format it accordingly and save the JSON into ``ionos-secret.json``:

.. code-block:: console

  $ jq -n -r -M \
    --arg name "Terraform IONOS secret" \
    --arg path "/terraform-api/credentials.tf" \
    --arg contents $(cat ionos-credentials.tf) \
    '{name: $name, file: {path: $path, contents: $contents}}' > ionos-secret.json

.. note::

  The directory path that we choose for the secret is ``/terraform-api`` and the file name is ``credentials.tf``. The name of a Terraform's provider file is arbitrary as long as it is a valid file name, does not collide with other ``.tf`` files (we will see these later) and ends with the ``.tf`` extension. The directory path, however, is important to be one of those that Terraform is going to search for. It is convenient to choose a working directory of the *Terraform LCM Service*, which in our case is ``/terraform-api``.

Let us now create a new secret.

.. code-block:: console

  $ lcm_curl --data @ionos-secret.json "$LCM_ENGINE_HOST/secret"

.. code-block:: json

  {
    "file": {
      "contentsHash": "38ef15caf8ec0c6190e451df6c35744775c81d29d2863e3beafe91d5f08e1adf253225643749d7039f7537e2d407b6f503873ba3149bafb2e22dfdcc2a1ada6a",
      "path": "/terraform-api/credentials.tf"
    },
    "id": 1,
    "name": "Terraform IONOS secret",
    "workspaces": []
  }

The *LCM Engine* responds with secret ID (assuming it is 1). We store it for future reference with ``export SECRET_ID=1``.

.. note::

  Instead of disclosing file contents in a plain text, it shows its SHA512 hash.


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Associate Terraform Secret With Workspace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  
The list of workspaces to which this secret is associated is empty. If we want to use the secret, we need to associate it with a workspace.

.. code-block:: console

  $ lcm_curl -X PUT "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/secret/$SECRET_ID"

To check the association, we may ask about workspace details.

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID"

.. code-block:: json

  {
    "id": 2,
    "isOwner": true,
    "name": "Terraform workspace",
    "projects": [],
    "secrets": [
      1
    ]
  }

As we can see, workspace with ID 2 has one secret associated and its ID is 1. We can check the association also by inspecting secret's details:

.. code-block:: console

  $ lcm_curl "$LCM_ENGINE_HOST/secret/$SECRET_ID"

.. code-block:: json

  {
    "file": {
      "contentsHash": "38ef15caf8ec0c6190e451df6c35744775c81d29d2863e3beafe91d5f08e1adf253225643749d7039f7537e2d407b6f503873ba3149bafb2e22dfdcc2a1ada6a",
      "path": "/terraform-api/credentials.tf"
    },
    "id": 1,
    "name": "Terraform IONOS secret",
    "workspaces": [
      2
    ]
  }

This time the list of workspaces is not empty.

.. note::

  To use the secret in a project, all we have to do is to create a new project in this workspace. The *LCM Engine* will inject all the associated secrets into a respective *LCM Service*'s file system (and/or set environment variables, if defined).


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Create Nginx IONOS Terraform Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before we create a new Terraform project, let us have a look into the deployment package (CSAR). We are going to use the `Nginx IONOS Terraform example`_.

++++++++++++++++++++++++++++++++++++++
Download Nginx IONOS Terraform Example
++++++++++++++++++++++++++++++++++++++

.. code-block:: console

  $ curl -s -o nginx-ionos.zip \
    "https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/archive/main/examples-main.zip?path=terraform/nginx-ionos/iac"


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Prepare Nginx IONOS Terraform Package's Directory Structure
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Check its directory structure.

.. code-block:: console

  $ zipinfo -1 nginx-ionos.zip

  examples-main-terraform-nginx-ionos-iac/
  examples-main-terraform-nginx-ionos-iac/terraform/
  examples-main-terraform-nginx-ionos-iac/terraform/nginx-ionos/
  examples-main-terraform-nginx-ionos-iac/terraform/nginx-ionos/iac/
  examples-main-terraform-nginx-ionos-iac/terraform/nginx-ionos/iac/main.tf
  examples-main-terraform-nginx-ionos-iac/terraform/nginx-ionos/iac/output.tf
  examples-main-terraform-nginx-ionos-iac/terraform/nginx-ionos/iac/variables.tf

Again, we need to fix the directory structure of the package, such that all the ``.tf`` files are in the root.

.. code-block:: console

  $ unzip -j nginx-ionos.zip -d nginx-ionos && \
    cd nginx-ionos && \
    zip -r ../nginx-ionos-csar.zip . && \
    cd .. && \
    rm -rf nginx-ionos


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Prepare Nginx IONOS Terraform Project Creation Request Body
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

We create project's request body JSON.

.. code-block:: console

  jq -r -n -M \
    --arg name "nginx @ ionos with terraform" \
    --arg kind "si.xlab.lcm-service.terraform" \
    --arg csar $(base64 -w 0 nginx-ionos-csar.zip) \
    '{name: $name, kind: $kind, csar: $csar}' > nginx-ionos-project.json


+++++++++++++++++++++++++++++++++++++++++++++++++
Get Nginx IONOS Terraform Project Creation Status
+++++++++++++++++++++++++++++++++++++++++++++++++

Create a Terraform project.

.. code-block:: console

  $ lcm_curl --data @nginx-ionos-project.json "$LCM_ENGINE_HOST/workspace/$WORKSPACE_ID/project"

.. code-block:: json

  {
    "id": 2
  }


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Inspect *Terraform LCM Service*'s Directory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming that the project ID is 2, we store it for future reference with ``export PROJECT_ID=2``. Once the *Terraform LCM Service*'s Pod is running (we can check that with project's ``/creationStatus``), we may observe the Pod's file structure (requires access to the Kubernetes cluster):

.. code-block:: console

  $ POD_NAME=$(kubectl get pods --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -o jsonpath='{ .items[0].metadata.name }'); \
    kubectl exec "$POD_NAME" -c terraform --namespace "lcm-service-w$WORKSPACE_ID-p$PROJECT_ID" -- ls /terraform-api

.. code-block:: console

  credentials.tf
  main.tf
  output.tf
  variables.tf

.. note::

  We see that directory ``/terraform-api`` in the *Terraform LCM Service* Pod's file system contains all files from the CSAR *and* the file secret, exactly how Terraform expects it.


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Orchestrate with *Terraform LCM Service*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To deploy the CSAR, we may follow the `Terraform LCM Service API`_'s reference to proceed. At minimum, we should first call ``/init``, followed by optional ``/plan`` and then ``/apply``. To undeploy the CSAR, call ``/destroy``.

.. note::

  Compared with the `TOSCA LCM Service API`_, the CSAR deployment steps are different. In general, between various *LCM Services* all the operations and their inputs are different, closely resembling their orchestrators' semantic.



.. _TOSCA LCM Service API: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/tosca-xopera-lcm-service-api
.. _Terraform LCM Service API: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
.. _lcm-service/terraform-lcm-service-api: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
.. _Apache License, Version 2.0: https://www.apache.org/licenses/LICENSE-2.0
.. _orc/lcm-service/terraform-lcm-service-api: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/container_registry/3080493
.. _OpenAPI Specification for Terraform LCM Service API: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/-/blob/main/docs/swagger.yaml
.. _hello-world Terraform example: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/-/tree/main/tests/hello_world
.. _orc/lcm-engine: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-engine
.. _hello-world TOSCA example: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/tosca/hello-world
.. _Nginx IONOS Terraform example: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/terraform/nginx-ionos
.. _venv: https://docs.python.org/3/library/venv.html
.. _Apache httpd package: https://httpd.apache.org/docs/current/programs/htpasswd.html