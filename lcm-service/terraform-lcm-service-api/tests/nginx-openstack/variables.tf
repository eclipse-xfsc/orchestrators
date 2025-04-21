variable "name" {
  default = "nginx-host"
}

variable "image_name" {
  default = "ubuntu-20.04.3"
}

variable "flavor_name" {
  default = "small"
}

variable "key_pair" {
  default = "key-pair"
}

variable "security_groups" {
  default = [
    "default",
  "my-group"]
}

variable "network" {
  default = "ostack2"
}

variable "ssh_key_file" {
  default = "/home/user1/.ssh/openstack.key/"
}

variable "ssh_user" {
  default = "ubuntu"
}
