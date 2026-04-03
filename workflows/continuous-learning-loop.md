# Workflow: Continuous Learning Loop

1. Intake captures demand (`intake-task.sh`).
2. Planning classifies and proposes execution (`plan-task.sh`).
3. Execution runs in controlled mode (`execute-task.sh`).
4. Learning script extracts outcomes (`learn-task.sh`).
5. Knowledge base is updated:
   - lessons learned
   - improvement log
   - decision log
6. Manager reviews trends and approves next adjustments.

## Rules
- Local-only execution by default.
- Dry-run remains default unless explicit approval is provided.
- Learning updates are append-only for traceability.
- Human leadership remains mandatory for critical decisions.
