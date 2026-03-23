output "artifact_path" {
  description = "Generated artifact path in local lab."
  value       = module.local_foundation.artifact_path
}

output "artifact_content_sha1" {
  description = "SHA1 hash of the generated local artifact content."
  value       = module.local_foundation.artifact_content_sha1
}

output "artifact_token" {
  description = "Random token generated in local lab."
  value       = module.local_foundation.artifact_token
}
