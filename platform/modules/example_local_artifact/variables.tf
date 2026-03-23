variable "artifact_name" {
  description = "Logical artifact name stored inside the file content."
  type        = string
}

variable "artifact_path" {
  description = "Path to the generated local artifact file."
  type        = string
}

variable "metadata" {
  description = "Free-form metadata persisted with the artifact."
  type        = map(string)
  default     = {}
}
