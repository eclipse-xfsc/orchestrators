output "ip_address" {
    value = ionoscloud_ipblock.public_ip.ips[0]
}
