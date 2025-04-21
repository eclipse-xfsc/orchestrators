.. _Glossary:

========
Glossary
========

Here we provide a list of terms and abbreviations that the readers of this documentation need to be familiar with to
understand the **GXFS Orchestration**.

.. glossary::

    GAIA-X
        Gaia-X is an European initiative developing the next generation of federated and secure data infrastructure
        with digital sovereignty composing a system that can link together many cloud services providers.
        For more info see `gaia-x.eu`_.

    GXFS
        Gaia-X Federation Services are services needed to get started with a cloud-based self-sovereign data
        infrastructure ecosystem.
        These services are for instance Identity and Trust Services, Federated Catalogue, Data Sovereignty Services,
        Compliance, Portal and Integration and others.
        Federations are promoted within :term:`Gaia-X` as a new model of cloud data exchange.
        You can find more info at `gxfs.eu`_.

    Gaia-X Service
        A (cloud) application that can consist of multiple resources described within :term:`Self-Descriptions<SD>`
        and their :term:`deployment instructions`.
        This application is usually prepared to be deployed on a specific cloud provider (e.g., AWS, Azure, GCP).

    LCM
        Life Cycle Management encompasses orchestration actions (e.g., creating, updating, deleting, reading state) on
        resources and/or :term:`Services<Gaia-X Service>`.

    Deployment technology
        The name of technology (e.g., Terraform, Ansible) that used to deploy a Gaia-X Service.
        For example Kubernetes would mean deploying onto a Kubernetes cluster, Ansible would mean deployment

    Deployment instructions
        All commands that need to be executed to make a specific :term:`Gaia-X Service` run.
        These instructions are in the form of IaC (e.g., Terraform template, a Kubernetes manifest file, an OpenStack
        Heat template) and are fetched from the PPR.

    IaC
        Infrastructure as Code (deployment instructions - e.g., TOSCA, Terraform, Ansible accompanied with other files
        needed for the application deployment).

    SD
        Gaia-X Self-Description can describe any Gaia-X entity (Asset, Resource, Service Offering) or whole
        :term:`Gaia-X Service` in a human readable and machine interpretable format.
        Self-Descriptions can be expressed using the `JSON-LD`_ (or `Turtle`_) format.
        Moreover, they are `W3C Verifiable Presentations`_ in the `JSON-LD serialization of the RDF graph data model`_.
        SDs can be signed (with SHA-256) to ensure that they come from a trusted source.
        Each SD can be equipped with different :term:`deployment instructions` by providing links to appropriate
        :term:`IaC` that is used to deploy an entity or :term:`Gaia-X Service` described within the SD.

    Catalogue
        A Gaia-X Catalogue is an instance of the Federation Service called Federated Catalogue and presents a list of
        available Gaia-X entities and :term:`Services<Gaia-X Service>`.
        Catalogues will store :term:`Self-Descriptions<SD>` (and their :term:`deployment instructions`).

    Orchestrator
        An orchestration tool (e.g., Terraform, TOSCA orchestrator) that can manage life-cycle of application by
        running different orchestration actions (e.g., deploy, undeploy, monitor, scale) using provided :term:`IaC`.

    Gaia-X Orchestration
        A Federation Service responsible for the instantiation and management of :term:`Services<Gaia-X Service>` with
        the core feature of dealing with the :term:`LCM` of :term:`Gaia-X Services<Gaia-X Service>`.
        Orchestration includes three main components: :term:`LCM Engine`, :term:`LCM Services<LCM Service>` and
        :term:`PPR`, all provided as a REST API services that can be set up using Kubernetes and Docker containers.

    Gaia-X Portal
        A Federation Service where Participants (registered users) can interact with central Federation Service
        functions via a graphical user interface.
        Apart from other services the portal is also an orchestration portal, which automates the application delivery
        to a specific cloud provider on behalf of a user.
        The vision is that users will be able to select services from the catalogue of service providers through the
        Gaia-X Portal and then instantiate them through the :term:`Gaia-X Life Cycle Management Engine<LCM Engine>`,
        which will select an appropriate :term:`Life Cycle Management Service<LCM Service>` (e.g. TOSCA orchestrator
        API, Terraform API, Ansible API, Kubernetes API and others) to deploy applications and services.

    LCM Engine
        Gaia-X Life Cycle Management Engine is a service that belongs to the Portal and acts as an interface (API)
        between the :term:`Portal<Gaia-X Portal>`, the :term:`LCM Services<LCM Service>`. and the :term:`PPR`.
        :term:`LCM Engine` can be viewed as an *orchestrator of orchestrators* being a component managing all
        deployment and delivery projects, where one project contains the :term:`Gaia-X Service` that gets deployed.

    LCM Service
        Life Cycle Management Service is a service that can be used to manage :term:`Gaia-X Services<Gaia-X Service>`
        by running different CRUD operations for one orchestration project (i.e., one application instance).
        LCM Service is a REST API to the corresponding automation/orchestration tools (e.g., TOSCA orchestrator,
        Terraform, Ansible, Kubernetes and others) and is tied directly to the :term:`LCM Engine` that manages the
        creation of :term:`LCM Services<LCM Service>` when needed for orchestration.

    PPR
        Participant Provider Role​plays a role of a :term:`Service<Gaia-X Service>`. providers catalogue or a library
        of :term:`Self-Descriptions<SD>` and the corresponding :term:`IaC`.
        PPR is responsible for the fetching of the :term:`deployment instructions` (by the :term:`LCM Engine`).
        PPR can be viewed as *catalogue of catalogues* as it provides an API linked to multiple
        :term:`Catalogues<Catalogue>`, each containing multiple :term:`SDs<SD>`.

.. _gaia-x.eu: https://gaia-x.eu/
.. _gxfs.eu: https://www.gxfs.eu/
.. _xlab.si: https://www.xlab.si/
.. _JSON-LD: https://json-ld.org/
.. _Turtle: https://www.w3.org/TR/turtle/
.. _W3C Verifiable Presentations: https://www.w3.org/TR/vc-data-model/#presentations
.. _JSON-LD serialization of the RDF graph data model: https://www.w3.org/2018/jsonld-cg-reports/json-ld/#serializing-deserializing-rdf
