# iacctl

Small CLI wrapper for local Terraform operations via `agents-local/Makefile`.

## Usage

```bash
./app/iacctl/iacctl.sh <command> [environment]
```

## Commands

- `init`
- `validate`
- `plan`
- `apply`
- `destroy`
- `verify`

Default environment is `lab`.

## Examples

```bash
./app/iacctl/iacctl.sh init
./app/iacctl/iacctl.sh validate lab
./app/iacctl/iacctl.sh plan lab
./app/iacctl/iacctl.sh verify lab
./app/iacctl/iacctl.sh plan gcp-client-whitelist
```
