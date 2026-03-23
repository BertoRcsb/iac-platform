output "artifact_path" {
  description = "Generated artifact path."
  value       = module.artifact.artifact_path
}

output "artifact_content_sha1" {
  description = "SHA1 hash of generated artifact content."
  value       = module.artifact.artifact_content_sha1
}

output "artifact_token" {
  description = "Random token generated for the artifact content."
  value       = module.artifact.artifact_token
}
