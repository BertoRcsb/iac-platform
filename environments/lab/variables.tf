variable "environment_name" {
  description = "Logical environment name."
  type        = string
  default     = "lab"
}

variable "artifact_name" {
  description = "Logical name stored in the generated artifact."
  type        = string
  default     = "lab-artifact"
}

variable "artifact_path" {
  description = "Output file path for the generated artifact."
  type        = string
  default     = "lab-artifact.txt"
}

variable "metadata" {
  description = "Additional metadata added to the artifact content."
  type        = map(string)
  default = {
    owner   = "platform-team"
    purpose = "local-lab"
  }
}
