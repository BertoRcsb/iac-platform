# Workflow: Jira Authorized Execution

1. Manager selects Jira card to work on
2. Card is authorized with `jira-authorize`
3. System reads card via Jira API (`jira-run`) when API is enabled
4. If Jira API is disabled, card can still be processed by pasting URL/key in local run input (`run`)
5. System generates category, risks, plan, and next action
6. GO/NO-GO check validates readiness (`gate-check`)
7. Execution only runs when:
   - card is authorized
   - manager approval flags are provided
   - approver identity is provided (`approved_by`)
8. Optional external Jira adapter actions:
   - add comment
   - add comment from template mode (standardized communication)
   - transition status
   (same approval + allowlist rules)
9. Review and learning documentation are generated
10. Optional auto-sync on review close:
   - if enabled, review final state (`DONE/BLOCKED`) posts final Jira template comment
   - optional transition can run based on final state
   - simulated execution is skipped by default unless `JIRA_AUTO_SYNC_ON_SIMULATION=true`

Security rule:
- Non-authorized Jira cards are blocked from execution.
