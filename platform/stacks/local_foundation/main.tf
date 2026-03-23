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

module "artifact" {
  source = "../../modules/example_local_artifact"

  artifact_name = var.artifact_name
  artifact_path = var.artifact_path
  metadata = merge(
    {
      stack       = "local_foundation"
      environment = var.environment_name
    },
    var.metadata
  )
}
