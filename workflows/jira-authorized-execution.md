# Workflow: Jira Authorized Execution

1. Manager selects Jira card to work on
2. Card is authorized with `jira-authorize`
3. System reads card via Jira API (`jira-run`)
4. System generates category, risks, plan, and next action
5. GO/NO-GO check validates readiness (`gate-check`)
6. Execution only runs when:
   - card is authorized
   - manager approval flags are provided
   - approver identity is provided (`approved_by`)
7. Optional external Jira adapter actions:
   - add comment
   - add comment from template mode (standardized communication)
   - transition status
   (same approval + allowlist rules)
8. Review and learning documentation are generated

Security rule:
- Non-authorized Jira cards are blocked from execution.
