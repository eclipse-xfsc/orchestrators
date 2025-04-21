terraform {
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
      version = "~> 1.47.0"
    }
  }
}

resource "openstack_compute_instance_v2" "vm" {
  name = var.name
  image_name = var.image_name
  flavor_name = var.flavor_name
  key_pair = var.key_pair
  security_groups = var.security_groups

  network {
    name = var.network
  }

  provisioner "remote-exec" {
    connection {
      type = "ssh"
      user = var.ssh_user
      private_key = file(var.ssh_key_file)
      host = openstack_compute_instance_v2.vm.access_ip_v4
    }

    inline = [
      <<EOF
      sudo apt-get -y update
      sudo apt-get -y install nginx
      sudo service nginx start
      sudo chown -R $USER:$USER /var/www /usr/share/nginx
      tee /var/www/html/index.html /usr/share/nginx/html/index.html <<-EOF >/dev/null
        <!doctype html>
        <html lang="en">
        <head>
          <title>Hello World!</title>
        </head>
        <body>
          <h1>Sample web page</h1>
          <p>With little content ;)</p>
        </body>
        </html>
      EOF
    ]
  }
}
