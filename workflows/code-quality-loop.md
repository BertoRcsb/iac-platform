# Workflow: Code Quality Loop

1. Run risk review:
   - `./scripts/agentctl review-code --path .`
2. If findings include medium/high risk:
   - `./scripts/agentctl debug-auto --command "./scripts/agentctl-test.sh" --path . --apply-refactor`
3. Validate test result:
   - if pass, keep refactor
   - if fail, automatic rollback is applied
4. Publish scientific debug doc in `knowledge/shared`
5. Review and share lessons learned with team
