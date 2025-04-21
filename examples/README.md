# Deployment examples for GXFS Orchestration
This repository contains IaC examples for deployment with LCM Engine and LCM Services.

## Table of Contents
  - [Description](#purpose-and-description)
  - [Structure](#structure)
  - [License](#license)
  - [Contact](#contact)

## Purpose and description
This repo contains IaC deployment examples with applications that can be used to test the GXFS Orchestration services 
or can be deployed separately from other environments.
Explore the [GXFS Documentation] for more information.

## Structure
Currently we have the following types of examples separated into folders:

- `terraform/` - contains Terraform examples (for [Terraform LCM Service])
- `tosca/` - contains TOSCA examples (for [TOSCA xOpera LCM Service])

Each of these folders contain multiple example folders and those contain the following two subfolders:

- `iac/` - contains IaC (in uncompressed/extracted form)
- `inputs/` - contains a single input file that supplies input values for IaC (this folder is optional)

All the examples are equipped with `README.md` instructions for deployment and possibly other materials.

You can navigate to [Package Registry] to download examples in compressed form, which is what LCM Engine 
and LCM Services expect.

## License
This work is licensed under the [Apache License 2.0].

## Contact
You can contact the XLAB's Gaia-X team by sending an email to [gaia-x@xlab.si].

[ppr Docker image]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/ppr/container_registry
[GXFS Documentation]: https://gaia-x.gitlab.io/data-infrastructure-federation-services/orc/documentation/
[Terraform LCM Service]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api
[TOSCA xOpera LCM Service]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/tosca-xopera-lcm-service-api
[Package Registry]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/examples/-/packages
[Apache License 2.0]: https://www.apache.org/licenses/LICENSE-2.0
[gaia-x@xlab.si]: mailto:gaia-x@xlab.si
