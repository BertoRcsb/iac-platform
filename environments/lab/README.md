# lab environment

Runnable local environment for Terraform workflow validation.

## Commands

```bash
terraform -chdir=environments/lab init
terraform -chdir=environments/lab validate
terraform -chdir=environments/lab plan
terraform -chdir=environments/lab apply
```

This environment is intentionally cloud-free and does not require credentials.
