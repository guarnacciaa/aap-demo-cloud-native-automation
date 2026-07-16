# Verification

## Smoke test

```bash
ansible-playbook playbooks/verify.yml
```

## Optional pre-flight dry-run checks

Before running the functional checks below, optionally launch the four
read-only dry-run job templates (`Azure - Connectivity check (dry run)`,
`Azure - Runbook preview (dry run)`, `AWS - Connectivity check (dry run)`,
`AWS - SSM preview (dry run)`) — see [docs/procedures.md](procedures.md#dry-run-checks-optional).
They confirm credentials and target resources are reachable without creating,
modifying, or deleting anything, which narrows down whether a functional
check failure is a configuration/connectivity issue or a real regression.

## Functional checks

### Azure Automation

- Portal → Automation Account → Jobs: new job with status **Completed**.
- Job output stream contains expected runbook text.

### AWS SSM

```bash
aws ssm describe-automation-executions --filters Key=DocumentName,Values=<document> --region <region>
```

## References

- [Azure Automation Job REST API](https://learn.microsoft.com/en-us/rest/api/automation/job/create)
- [AWS StartAutomationExecution](https://docs.aws.amazon.com/cli/latest/reference/ssm/start-automation-execution.html)
- [AWS RegisterTaskWithMaintenanceWindow](https://docs.aws.amazon.com/cli/latest/reference/ssm/register-task-with-maintenance-window.html)
