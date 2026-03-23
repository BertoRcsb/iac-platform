# Terraform Standards

- Every runnable root must define `required_version` and `required_providers`.
- Modules contain `main.tf`, `variables.tf`, `outputs.tf`, plus short README.
- Stacks expose clear input/output interfaces and compose modules.
- Variables must include type and concise description.
- Outputs must be purposeful and stable for downstream usage.
- Provider declarations must avoid hardcoded credentials and secrets.
- Use consistent naming across files, resources, and variables.
- Validation baseline: `terraform fmt`, `terraform validate`, `terraform plan` where applicable.
