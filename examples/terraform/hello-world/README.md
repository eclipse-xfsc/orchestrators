# Hello world
A minimal (hello world) example for Terraform - useful when we first encounter Terraform.

## Table of Contents
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Running with Terraform](#running-with-terraform)

## Description
This example creates an example file with example content.
After the deployment the file will be created at the specified location and will include the specified content.

## Prerequisites
To run manually you will need to install Terraform first. 
On Linux distributions you can run the following commands (on other OS follow 
[these](https://learn.hashicorp.com/tutorials/terraform/install-cli) instructions):

```console
$ sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl
$ curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
$ sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
$ sudo apt-get update && sudo apt-get install terraform
$ terraform -help
```

Before running you should modify the input values in `variables.tf`.

# Running with Terraform
We can first initialize the project (downloads needed Terraform plugins):

```console
$ cd tests/hello_world/
tests/hello_world$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/local versions matching "2.2.2"...
- Installing hashicorp/local v2.2.2...
- Installed hashicorp/local v2.2.2 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary
```

We can then validate our configuration as follows:

```console
tests/hello_world$ terraform validate
Success! The configuration is valid.
```

We can then preview our execution plan:

```console
tests/hello_world$ terraform plan

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # local_file.hello will be created
  + resource "local_file" "hello" {
      + content              = "Terraform was here!"
      + directory_permission = "0777"
      + file_permission      = "0777"
      + filename             = "/tmp/playing-terraform/hello.txt"
      + id                   = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + hello_output = "/tmp/playing-terraform/hello.txt has been created with contetent Terraform was here!."
```

Then we can apply the configuration and deploy the example as follows:

```console
tests/hello_world$ terraform apply -auto-approve

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # local_file.hello will be created
  + resource "local_file" "hello" {
      + content              = "Terraform was here!"
      + directory_permission = "0777"
      + file_permission      = "0777"
      + filename             = "/tmp/playing-terraform/hello.txt"
      + id                   = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + hello_output = "/tmp/playing-terraform/hello.txt has been created with contetent Terraform was here!."
local_file.hello: Creating...
local_file.hello: Creation complete after 0s [id=73d2ed5802230f9cbd81805a856204068f83329b]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

hello_output = "/tmp/playing-terraform/hello.txt has been created with contetent Terraform was here!."
```

To see only final output you can run:

```console
tests/hello_world$ terraform output
hello_output = "/tmp/playing-terraform/hello.txt has been created with contetent Terraform was here!."
```

You can undeploy the solution with:

```console
tests/hello_world$ terraform destroy -auto-approve
local_file.hello: Refreshing state... [id=73d2ed5802230f9cbd81805a856204068f83329b]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # local_file.hello will be destroyed
  - resource "local_file" "hello" {
      - content              = "Terraform was here!" -> null
      - directory_permission = "0777" -> null
      - file_permission      = "0777" -> null
      - filename             = "/tmp/playing-terraform/hello.txt" -> null
      - id                   = "73d2ed5802230f9cbd81805a856204068f83329b" -> null
    }

Plan: 0 to add, 0 to change, 1 to destroy.

Changes to Outputs:
  - hello_output = "/tmp/playing-terraform/hello.txt has been created with contetent Terraform was here!." -> null
local_file.hello: Destroying... [id=73d2ed5802230f9cbd81805a856204068f83329b]
local_file.hello: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```
