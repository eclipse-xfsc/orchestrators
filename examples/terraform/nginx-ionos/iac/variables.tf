variable "name" {
    default = "nginx-host"
}

variable "location" {
    default = "de/txl"
}

variable "cores" {
    default = 2
}

variable "ram" {
    default = 2048
}
variable "image_name" {
    default = "ubuntu:20.04"
}

variable "public_key_file" {
    default = "/opt/vm_nginx.key.pub"
}

# not used, can replace public_key_file
variable "image_password" {
    default = "K3tTj8G14a3EgKyNeeiY"
}
