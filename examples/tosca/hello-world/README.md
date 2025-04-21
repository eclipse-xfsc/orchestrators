# Hello world
This is a hello world TOSCA template for xOpera. 

*This example is taken from: https://github.com/xlab-si/xopera-examples/tree/main/misc/hello-world.*

## Table of Contents
  - [Description](#description)
  - [Running with xOpera](#running-with-xopera)

# Description
The `iac/service.yaml` within this folder shows a minimal service template that is composed of two node templates:

- `hello`: a node template of type `tosca.nodes.SoftwareComponent` that
  invokes the `playbooks/hello/create.yaml` Ansible playbook as its
  `create` interface.
- `my-workstation`: this node template is necessary to fulfil the
  `hello`'s requirement for capability `host`. By assigning `localhost`
  as the values of the node template's attributes `private_address` and
  `public_address` we tell the `opera` orchestrator that it should
  host `hello` on the same workstation as we are running the `opera`
  from.

# Running with xOpera
We can run our hello-world as follows:

```console
(.venv) tosca/hello-world$ cd iac
(.venv) tosca/hello-world/iac$ opera deploy service.yaml
[Worker_0]   Deploying my-workstation_0
[Worker_0]   Deployment of my-workstation_0 complete
[Worker_0]   Deploying hello_0
[Worker_0]     Executing create on hello_0
[Worker_0]   Deployment of hello_0 complete
```

The result of this service template should be a new directory and a file on
the workstation:

```console
(.venv) tosca/hello-world/iac$ ls -lh /tmp/playing-opera/hello/
total 0
-rw-rw-rw- 1 user user 0 Feb 20 16:02 hello.txt
```

The solution can be also undeployed:

```console
(.venv) tosca/hello-world/iac$ opera undeploy
[Worker_0]   Undeploying hello_0
[Worker_0]     Executing delete on hello_0
[Worker_0]   Undeployment of hello_0 complete
[Worker_0]   Undeploying my-workstation_0
[Worker_0]   Undeployment of my-workstation_0 complete
```

After that the created directory and file are deleted:

```console
(.venv) tosca/hello-world/iac$ ls -lh /tmp/playing-opera/hello/
ls: cannot access '/tmp/playing-opera/hello/': No such file or directory
```
