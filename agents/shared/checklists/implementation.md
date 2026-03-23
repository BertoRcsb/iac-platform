# Implementation Checklist

- [ ] `terraform fmt -recursive` completed.
- [ ] `terraform validate` completed for changed runnable environments.
- [ ] Lint run (`tflint`) or explicitly skipped if unavailable.
- [ ] Security scan run (`trivy config .`) or explicitly skipped if unavailable.
- [ ] No duplicated patterns introduced.
- [ ] Assumptions documented where needed.
- [ ] No out-of-scope files or behavior changed.
