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

module "local_foundation" {
  source = "../../platform/stacks/local_foundation"

  environment_name = var.environment_name
  artifact_name    = var.artifact_name
  artifact_path    = var.artifact_path
  metadata         = var.metadata
}
