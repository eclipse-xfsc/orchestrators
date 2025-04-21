terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "2.2.2"
    }
  }
}

resource "local_file" "hello" {
  filename = var.file_path
  content  = var.file_content
}
