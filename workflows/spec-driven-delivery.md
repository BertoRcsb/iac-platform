# Workflow: Spec-Driven Delivery

1. Intake receives demand (`new` or `run`)
2. Analysis/Architect classify and plan (`plan`)
3. Spec pack is generated (`spec-pack`)
4. Spec quality gates are validated (`spec-analyze`)
5. Router chooses provider path (`route`)
6. GO/NO-GO validates execution readiness (`gate-check`)
7. Execution runs with approval gates (`execute`)
8. Review validates evidence and closes state (`review`)
9. Learning publishes scientific documentation (`learn`)

Rules:
- no hidden transitions
- no execution without approval when required
- all critical actions remain auditable
