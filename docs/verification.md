# Verification

## Smoke test

```bash
ansible-playbook playbooks/verify.yml
```

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
