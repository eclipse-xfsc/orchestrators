.. _LCM Services Introduction:

************
Introduction
************

LCM Service is the component enclosing the Orchestration engine that executes the IaC scripts and manages the
particular exploitation.
From the software point of view, the LCM Service is an API for any tool that can manage SDLC of services.
The user can access the functionalities of the LCM Service through the :term:`LCM Engine`.
When user creates a new deployment project (e.g., deploy a LAMP/MEAN stack), the :term:`LCM Engine` will spawn a new
deployment environment inside a container with LCM Service inside.

.. _LCM Services List of services:

****************
List of services
****************

:term:`LCM Engine` currently supports the following :term:`LCM Services<LCM Service>`:

+---------------------------------------+------------------------------------+
| LCM Service                           | Target IaC type for orchestration  |
+=======================================+====================================+
| :ref:`TOSCA xOpera LCM Service`       | TOSCA                              |
+---------------------------------------+------------------------------------+
| :ref:`Terraform LCM Service`          | Terraform                          |
+---------------------------------------+------------------------------------+

.. toctree::
   :hidden:

   0401-xopera.rst
   0402-terraform.rst

.. tip::

    To test :term:`LCM Services<LCM Service>` on real examples go to :ref:`Examples`.
