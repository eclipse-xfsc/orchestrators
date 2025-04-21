# IONOS and nginx
An example of deployment of VM with nginx on [IONOS Cloud].

## Prerequisites:
The [ionos-cloud/ionoscloud] provider needs to be configured with proper credentials before it can be used.

You can set the environment variables for HTTP basic authentication:

```bash
export IONOS_USERNAME="gaiax-trial@ionos.com"
export IONOS_PASSWORD="your_password_here"
```

Or you can use token authentication, described [here](https://github.com/ionos-cloud/sdk-go#token-authentication):

```bash
export IONOS_TOKEN="token"
```

## A few notes on IONOS Cloud infrastructure:
Servers can only be created inside a data center. The data center is in a specific geographic location 
(e.g., "de/txl"), but you can have multiple data centers in the same location.
When you check with the GUI tool you will see the data center and when you click on it you see inside the server, the 
lan, etc.

### Server config:
No need to use `remote_exec`. Using a cloud-init image we can pass the same script from the 
user_data field.
This means that we don't necessarily need to provide ssh_key_path(public key).
One of either `image_password` or `ssh_key_path` **must** be provided though.

## How to check what was installed:
You can use the GUI tool to check what is installed on the account: [dcd](https://dcd.ionos.com/latest/)

[IONOS Cloud]: https://cloud.ionos.com/
[ionos-cloud/ionoscloud]: https://registry.terraform.io/providers/ionos-cloud/ionoscloud/latest/docs
