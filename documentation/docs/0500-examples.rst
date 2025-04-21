.. _Examples:

************
Introduction
************

**GXFS Orchestration examples** are IaC examples for deploying different (cloud) applications.
These IaC examples contain deployment instructions :term:`Deployment instructions` and leverage different
:term:`Deployment technologies<Deployment technology>`.

Examples can be used to test :term:`LCM Engine` and :term:`LCM Services<LCM Service>` or can be deployed separately in
other environments.
They can also be linked to Gaia-X :term:`Self-Descriptions<SD>` that are then gathered in
:term:`Catalogues<Catalogue>` and those can be connected to the :term:`PPR`.

Examples are available in `orc/examples`_ GitLab repository and are licensed under `Apache License 2.0`_.

.. _Examples TOSCA examples:

**************
TOSCA examples
**************

The table below lists all the currently available TOSCA examples and can be used to test
:ref:`TOSCA xOpera LCM Service`.

+--------------------------------------------+-----------------------------------------------------------------+
| Example name and link                      | A brief description                                             |
+============================================+=================================================================+
| `hello-world-tosca`_                       | The very first and minimal hello world xOpera example.          |
+--------------------------------------------+-----------------------------------------------------------------+
| `nginx-openstack-tosca`_                   | Deploy nginx site on top of OpenStack VM.                       |
+--------------------------------------------+-----------------------------------------------------------------+
| `aws-thumbnail-generator-tosca`_           | FaaS thumbnail generator blueprint for AWS.                     |
+--------------------------------------------+-----------------------------------------------------------------+

.. _hello-world-tosca: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/tosca/hello-world
.. _nginx-openstack-tosca: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/tosca/nginx-openstack
.. _aws-thumbnail-generator-tosca: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/tosca/aws-thumbnail-generator

.. _Examples Terraform examples:

******************
Terraform examples
******************

The table below lists all the currently available Terraform examples and can be used to test
:ref:`Terraform LCM Service`.

+--------------------------------------------+-----------------------------------------------------------------+
| Example name and link                      | A brief description                                             |
+============================================+=================================================================+
| `hello-world-terraform`_                   | The very first and minimal hello world Terraform example.       |
+--------------------------------------------+-----------------------------------------------------------------+
| `nginx-openstack-terraform`_               | Deploy nginx site on top of OpenStack VM.                       |
+--------------------------------------------+-----------------------------------------------------------------+
| `nginx-ionos-terraform`_                   | An example of deployment of VM with nginx on IONOS Cloud.       |
+--------------------------------------------+-----------------------------------------------------------------+

.. _hello-world-terraform: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/terraform/hello-world
.. _nginx-openstack-terraform: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/terraform/nginx-openstack
.. _nginx-ionos-terraform: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/tree/main/terraform/nginx-ionos

.. _orc/examples: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples
.. _Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
