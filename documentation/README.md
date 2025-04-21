# GXFS Orchestration documentation
This repository holds the documentation for the [GXFS Orchestration].

## Table of Contents
  - [Description](#purpose-and-description)
  - [Run with Docker](#run-with-docker)
  - [Local building and testing](#local-building-and-testing)
  - [License](#license)
  - [Contact](#contact)

## Purpose and description
This project documents all the related GXFS Orchestration tools and services.
The documentation is available on https://gaia-x.gitlab.io/data-infrastructure-federation-services/orc/documentation/.

## Run with Docker
You can run the docs using a public [orc/documentation] Docker image as follows:

```console
# serve the documentation in a Docker container and navigate to localhost:8000
$ docker run --name gxfs-orchestration-docs -p 8000:80 registry.gitlab.com/gaia-x/data-infrastructure-federation-services/orc/documentation
```

Or you can build the image locally and run it as follows:

```console
# build Docker container
$ docker build -t gxfs-orchestration-docs .
# serve the documentation in a Docker container and navigate to localhost:8000
$ docker run --name gxfs-orchestration-docs -p 8000:80 gxfs-orchestration-docs
```

## Local building and testing
For building the documentation we use the [Sphinx documentation tool].
Here we can render Sphinx Documentation from RST files and we use [Read the Docs] theme.

To test the documentation locally run the commands below:

```console
# create and activate a new Python virualenv
$ python3 -m venv .venv && . .venv/bin/activate
# update pip and install Sphinx requirements
(.venv) $ pip install --upgrade pip
(.venv) $ pip install -r requirements.txt
# build the HTML documentation
(.venv) $ sphinx-build -M html docs build
# build the Latex and PDF documentation
(.venv) $ sphinx-build -M latexpdf docs build
```

After that you will found rendered documentation HTML files in `build` folder and you can open and view them inside 
your browser. 

## License
This work is licensed under the [Apache License 2.0].

## Contact
You can contact the XLAB's Gaia-X team by sending an email to [gaia-x@xlab.si].

[GXFS Orchestration]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc
[orc/documentation]: https://gitlab.com/gaia-x/data-infrastructure-federation-services/orc/documentation/container_registry/3125214
[Sphinx documentation tool]: https://www.sphinx-doc.org/en/master/
[Read the Docs]: https://readthedocs.org/
[Apache License 2.0]: https://www.apache.org/licenses/LICENSE-2.0
[gaia-x@xlab.si]: mailto:gaia-x@xlab.si
