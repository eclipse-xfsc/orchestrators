terraform {
    required_version = ">= 1.0.0"
    required_providers {
        ionoscloud = {
            source = "ionos-cloud/ionoscloud"
            version = "6.3.0"
        }
    }
}

resource "ionoscloud_datacenter" "dc_for_vm" {
    name = "dc_for_vm"
    location = var.location
    description = "Test Datacenter for vm with nxingx"
}

# lan connected to the server in the nic defined on the server
resource "ionoscloud_lan" "lan_for_vm" {
    name = "Lan for vm with nxingx"
    datacenter_id = ionoscloud_datacenter.dc_for_vm.id
    public = true
}

# we need 1 public ip
resource "ionoscloud_ipblock" "public_ip" {
    name = "ipblock_for_lan"
    location = ionoscloud_datacenter.dc_for_vm.location
    size = 1
}

resource "ionoscloud_server" "vm" {
    name = var.name
    datacenter_id = ionoscloud_datacenter.dc_for_vm.id
    cores = var.cores
    ram = var.ram
    image_name = var.image_name
    availability_zone = "AUTO"
    ssh_key_path = [
        var.public_key_file]
    #   image_password = var.image_name
    volume {
        # /dev/vda1
        name = "main-hdd"
        size = 100
        disk_type = "HDD"
        user_data = base64encode(<<EOF
#!/bin/bash
sudo apt update
sudo apt-get -y update
sudo apt-get -y install nginx
sudo chown -R $USER:$USER /var/www /usr/share/nginx
tee /var/www/html/index.html /usr/share/nginx/html/index.html <<-EOF >/dev/null
<!doctype html>
<html lang="en">
<head>
<title>Hello GXFS Demo!</title>
</head>
<body>

    <h1>Webpage deployed on Ionos Cloud</h1>


<p>Shaping the future data infrastructure together - secure, open and transparent
Innovation through digital sovereignty - that's the goal of Gaia-X. This is achieved by establishing an ecosystem in which data is made available, collated and shared in a trustworthy environment where users always retain sovereignty over their data. What emerges is not a cloud, but a federated system that links many cloud service providers and users together.
</p>


<a href="https://www.gxfs.eu/">https://www.gxfs.eu/</a>

<a href="https://www.gxfs.eu/"><img src="https://www.gxfs.eu/wp-content/uploads/2022/01/GFXS_DE_Logo.jpg" width="400" alt="GXFS"></a>


</body>
</html>
      EOF
        )
    }
    nic {
        lan = ionoscloud_lan.lan_for_vm.id
        dhcp = true
        firewall_active = false
        name = "public_nic"
        ips = [
            ionoscloud_ipblock.public_ip.ips[0]]
    }
}

