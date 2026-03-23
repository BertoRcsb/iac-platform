terraform {
  required_version = ">= 1.6.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_string" "artifact_suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

resource "local_file" "artifact" {
  filename        = var.artifact_path
  file_permission = "0644"
  content         = <<-EOT
    name=${var.artifact_name}
    token=${random_string.artifact_suffix.result}
    metadata=${jsonencode(var.metadata)}
  EOT
}
