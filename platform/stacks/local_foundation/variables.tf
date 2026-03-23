variable "environment_name" {
  description = "Environment name associated with this stack execution."
  type        = string
  default     = "lab"
}

variable "artifact_name" {
  description = "Logical artifact name."
  type        = string
  default     = "lab-artifact"
}

variable "artifact_path" {
  description = "Where to write the generated local artifact file."
  type        = string
  default     = "lab-artifact.txt"
}

variable "metadata" {
  description = "Additional metadata stored in the generated artifact."
  type        = map(string)
  default     = {}
}
