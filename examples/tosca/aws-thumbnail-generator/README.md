# AWS thumbnail generator
Image resize functionality deployment with xOpera for Amazon Web Services.

*This example is taken from: https://github.com/xlab-si/xopera-examples/tree/main/cloud/aws/thumbnail-generator.*

## Table of Contents
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Running with xOpera](#running-with-xopera)

## Description
The main functionality of image-resize is to create thumbnails from the source image. Source image must be uploaded 
into source bucket and then three thumbnails will be created and saved to another bucket.

The solution includes next deployment modules separated into folders:

| Role | Description |
|:-------------|:-------------|
| **prerequisites** | Installs prerequisite packages |
| **lambda_role** | Creates a new AWS IAM role for AWS Lambda |
| **bucket** | Creates a new AWS S3 bucket |
| **lambda** | Prepares a zipfile with function and deploys it to AWS Lambda |
| **bucket-notification** | Creates notification on bucket for triggering the lambda |

You can modify values in `inputs/inputs.yaml` to set the appropriate params (IPs, auth params, container names etc.).

## Prerequisites
This example requires a Python dev environment. To set everything up run the following commands:

```console
# Initialize virtualenv with Python and install prerequisites
cd aws
python3 -m venv .venv && . .venv/bin/activate
pip install --upgrade pip
pip install opera
```

Your AWS credentials should be located in `~/.aws/credentials` (you can also use `~/.aws/config`) or you should export
them into `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` environment variables.

You can also install and configure AWS CLI manually.

```console
# Install AWS CLI
pip install awscli

# Configure your account with your aws credentials (access key, secret key, region)
aws configure
```

## Running with xOpera
You can modify values in `inputs.yaml` to set the appropriate params(IPs, auth params, container names etc.).

| Input | Description | Example |
|:-------------|:-------------|:-------------|
| `host_ip` | Host IP address | localhost |
| `region` | AWS region for your resources | eu-central-1 |
| `lambda_role_name` | The name of the new AWS role | LambdaRole |
| `function_name` | The name of the new AWS Lambda function | image-resize-function |
| `function_alias` | New alias for the function | latest |
| `permission_id` | Id of the permission - a unique statement identifier for lambda policy | lambda_test_permission |
| `bucket_in_name` | Name of the incoming bucket for original images | original |
| `bucket_out_name` | The name of the bucket containing resized images | resized |
| `lambda_runtime` | Runtime of the deployed lambda | python3.8 |
| `lambda_handler` | Function and method with lambda handler | Python example: image_resize.lambda_handler, Java example:package.ClassName::handlerFunction |
| `lambda_timeout` | Function timeout in seconds | 5 |
| `lambda_memory` | Function memory in MB | 128 |

You can invoke the deployment using the command below. 

```console
(.venv) tosca/aws-thumbnail-generator$ cd iac
(.venv) tosca/aws-thumbnail-generator/iac$ opera deploy -i ../inputs/inputs.yaml service.yaml
[Worker_0]   Deploying my-workstation_0
[Worker_0]   Deployment of my-workstation_0 complete
[Worker_0]   Deploying prerequisites_0
[Worker_0]     Executing create on prerequisites_0
[Worker_0]   Deployment of prerequisites_0 complete
[Worker_0]   Deploying lambda_role_0
[Worker_0]     Executing create on lambda_role_0
[Worker_0]   Deployment of lambda_role_0 complete
[Worker_0]   Deploying lambda_0
[Worker_0]     Executing create on lambda_0
[Worker_0]   Deployment of lambda_0 complete
[Worker_0]   Deploying bucket_in_0
[Worker_0]     Executing create on bucket_in_0
[Worker_0]   Deployment of bucket_in_0 complete
[Worker_0]   Deploying bucket_out_0
[Worker_0]     Executing create on bucket_out_0
[Worker_0]   Deployment of bucket_out_0 complete
[Worker_0]   Deploying bucket_notification_0
[Worker_0]     Executing create on bucket_notification_0
[Worker_0]   Deployment of bucket_notification_0 complete
```

You can undeploy the solution with:

```console
(.venv) tosca/aws-thumbnail-generator/iac$
[Worker_0]   Undeploying bucket_out_0
[Worker_0]     Executing delete on bucket_out_0
[Worker_0]   Undeployment of bucket_out_0 complete
[Worker_0]   Undeploying bucket_notification_0
[Worker_0]     Executing delete on bucket_notification_0
[Worker_0]   Undeployment of bucket_notification_0 complete
[Worker_0]   Undeploying lambda_0
[Worker_0]     Executing delete on lambda_0
[Worker_0]   Undeployment of lambda_0 complete
[Worker_0]   Undeploying lambda_role_0
[Worker_0]     Executing delete on lambda_role_0
[Worker_0]   Undeployment of lambda_role_0 complete
[Worker_0]   Undeploying bucket_in_0
[Worker_0]     Executing delete on bucket_in_0
[Worker_0]   Undeployment of bucket_in_0 complete
[Worker_0]   Undeploying prerequisites_0
[Worker_0]     Executing delete on prerequisites_0
[Worker_0]   Undeployment of prerequisites_0 complete
[Worker_0]   Undeploying my-workstation_0
[Worker_0]   Undeployment of my-workstation_0 complete
```
