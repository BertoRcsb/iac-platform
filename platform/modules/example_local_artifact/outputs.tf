output "artifact_path" {
  description = "Generated file path."
  value       = local_file.artifact.filename
}

output "artifact_content_sha1" {
  description = "SHA1 hash of generated artifact content."
  value       = sha1(local_file.artifact.content)
}

output "artifact_token" {
  description = "Random token used in artifact content."
  value       = random_string.artifact_suffix.result
}
