# Demo procedures

## Apply CasC

```bash
ansible-playbook playbooks/aap_config.yml -i inventory.yml --vault-id @prompt
```

## Dry run checks (optional)

Read-only pre-flight checks — never create, modify, or delete any resource. Run
these (or launch the equivalent `(dry run)` job templates) before the Azure/AWS
workflows below to confirm credentials and target resources are reachable.

```bash
ansible-playbook playbooks/demo/azure_precheck_connectivity.yml --vault-id @prompt
ansible-playbook playbooks/demo/azure_precheck_permissions.yml --vault-id @prompt
ansible-playbook playbooks/demo/azure_runbook_preview.yml --vault-id @prompt
ansible-playbook playbooks/demo/aws_precheck_connectivity.yml --vault-id @prompt
ansible-playbook playbooks/demo/aws_precheck_permissions.yml --vault-id @prompt
ansible-playbook playbooks/demo/aws_ssm_preview.yml --vault-id @prompt
ansible-playbook playbooks/demo/precheck_network_path.yml --vault-id @prompt
ansible-playbook playbooks/demo/precheck_smtp.yml --vault-id @prompt
```

## Azure Workflow 1 — Run runbook

1. Launch **WF - Azure Runbook execute and collect**.
2. Optionally set `azure_runbook_name` at launch.
3. Review job output and optional email notification node.

## Azure Workflow 2 — Schedule runbook

1. Launch **WF - Azure Runbook schedule**.
2. Confirm `azure_schedule_start_time` and frequency in extra vars.

## AWS Workflow 1 — Run SSM document

1. Launch **WF - AWS SSM document execute and collect**.
2. Provide `aws_ssm_document_name` and `aws_ssm_target_instance_id` if prompted.

## AWS Workflow 2 — Schedule via maintenance window

1. Launch **WF - AWS SSM schedule via maintenance window**.
2. Ensure `aws_ssm_maintenance_window_id` and `aws_ssm_service_role_arn` are set.

## Ad hoc examples

```bash
ansible-playbook playbooks/demo/azure_runbook_run.yml --vault-id @prompt
ansible-playbook playbooks/demo/aws_ssm_run_document.yml --vault-id @prompt
```

## Teardown

```bash
ansible-playbook playbooks/aap_cleanup.yml -e demo_cleanup_confirm=true --vault-id @prompt
```
