.. _Creating a new LCM service:

**************************
Creating a new LCM service
**************************

This part provides a complete step-by-step guide for creating a new :term:`LCM Service`.

.. _Inform yourself about the background:

=======================================
1. Inform yourself about the background
=======================================

Before reading this you should be familiar with the important terms (see :ref:`Glossary`) and
:ref:`background<Introduction>`.
You should also the :ref:`PPR<PPR Introduction>`) and :ref:`LCM Engine<LCM Engine Introduction>`) sections.

.. _Know the goal you are trying to achieve:

==========================================
2. Know the goal you are trying to achieve
==========================================

:term:`LCM Service` is an API for the target tool that can manage life-cycle operations for a target service (i.e.,
application or its parts).
:term:`LCM Services<LCM Service>` are created and managed by :term:`LCM Engine`.
In other words you will be creating a containerized (dockerized) HTTP/REST API for an automation/orchestration or other
type of DevOps tool that will not be accessible directly by the users, but will be accessed through
:term:`LCM Engine` API.
Note that an :term:`LCM Service` is meant to be a lightweight API to only one (deployment) project and not for multiple
environments or users.
This is because the :term:`LCM Engine` already has the universal support for users, workspaces and projects.

.. tip::

    Also take a look at :ref:`List of already supported LCM services <LCM Services List of services>`, so that you will
    not create what's already supported.

.. _Satisfy the requirements:

===========================
3. Satisfy the requirements
===========================

If we draw a line the following requirements are needed for :term:`LCM Service`:

- is an HTTP/REST API for the specific :term:`LCM` tool;
- an API endpoints support most or all the actions that the tool is capable of executing;
- an API comes with public YAML/JSON `OpenAPI Specification`_;
- an API should be tested with unit/integration tests;
- provides single project and single user API access;
- can be written in any programming language and use any open-source libraries;
- is available as a public Docker image and can be run within a Docker container;
- the source code resides within a public Git repository with an open-source license;
- an API or it's packages and Docker images should have versions;
- comes with detailed documentation or README.

.. _Be familiar with the target tool:

===================================
4. Be familiar with the target tool
===================================

Before starting to code you should be familiar with the DevOps tool that you are creating an :term:`LCM Service` for.
This means that you should be familiar with the tool's usage and distribution.
You should know what kind of modes of interaction the target tool has (e.g., an API, CLI, GUI, SDK, etc.) and if it
already supports the API, you should verify that it is in line with the requirements for the :term:`LCM Service` that
are specified above.

You should look if the tool is distributed as a package or if there are any public SDKs available (for example
Terraform has `terraform-exec`_ Go library that allows using Terraform programmatically).
If so, you can use the library and create appropriate API.
If there is no library you should look if the tool support the CLI and if so, you can map the CLI commands to
corresponding API endpoints.
If there is no existing API, CLI or SDK, the tool is probably proprietary or closed-sourced and therefore you cannot
proceed with creating the :term:`LCM Service` for that tool.

.. _Do the work:

==============
5. Do the work
==============

Within this step you can create (and publish) a public Git repository, where your :term:`LCM Service` will reside.
If possible name your repository like this: *<tool-name> LCM Service API* (e.g., Terraform LCM Service API).

.. hint::

    If you don't know where to put your :term:`LCM Service`'s source code, we can create a public Git repository for
    you within `orc/lcm-service`_ GitLab GXFS Orchestration subgroup (see our contact info - :ref:`Get in touch`).

This part is where you will do most of the programming.
Make sure that you test your API multiple times.
You can create the API in a similar style that we created ours (see `orc/lcm-service`_) or in any other way.
Just make sure that your API is clear and well documented (also with `OpenAPI Specification`_) and also that endpoints
are easy to use.
It's also recommended that you provide API configuration (e.g., debug mode, allowed hosts, trusted proxies, Swagger URL,
API port, etc.) via environment variables.
Your :term:`LCM Service` can be also distributed as a package in the specific programming language that you have chosen.
Apart from that you have to dockerize you API by composing a proper ``Dockerfile``.
Try to make the Docker image as lightweight as possible.
Test building and running your Docker image locally and after that you can publish it as a public Docker image on any
Docker registry (e.g., GitLab/GitHub registry, DockerHub, etc.).
You should also take care of providing good documentation on how to run and use your :term:`LCM Service` API.

After you are done the :term:`LCM Service` should be runnable from a public Docker image and this means that it can be
also included in :term:`LCM Engine` (continue reading).

.. _Next steps (optional):

========================
6. Next steps (optional)
========================

Congrats, you are done and have created your :term:`LCM Service`!

Currently there is no automatic procedure to include custom :term:`LCM Services<LCM Service>` to the :term:`LCM Engine`,
but we are working on it.
Until then you can contact us (see :ref:`Get in touch`) and provide us a link to your repository with the
:term:`LCM Service` and all additional data.
We will test it and get back to you and if everything is okay, your :term:`LCM Service` will be a part of
:term:`LCM Engine` and the users will be able to use it within their :term:`LCM Engine` projects.

.. _terraform-exec: https://github.com/hashicorp/terraform-exec
.. _orc/lcm-service: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service
.. _OpenAPI Specification: https://swagger.io/specification/
