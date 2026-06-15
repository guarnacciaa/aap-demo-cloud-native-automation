# Environment setup

## Requirements

| Component | Version |
|---|---|
| Red Hat Ansible Automation Platform | 2.6+ |
| Azure Automation Account | Pre-existing runbook and custom EE |
| AWS Systems Manager | Pre-existing automation document |
| Network | AAP (Azure) reaches AWS API endpoints |

## Customer prerequisites

- Azure Automation runbook with permissions configured for the service principal.
- AWS SSM document and instance profile/IAM role for targets.
- Azure SP with Automation Contributor on the automation account resource group.
- AWS IAM user/role with `ssm:StartAutomationExecution`, `ssm:GetAutomationExecution`, and maintenance window APIs.

## Install collections

```bash
cd artifacts/demos/aap-demo-cloud-native-automation
ansible-galaxy collection install -r collections/requirements.yml -p collections
cp ansible.cfg.example ansible.cfg
cp group_vars/all/demo_variables.yml.example group_vars/all/demo_variables.yml
cp vault.yml.example vault.yml && ansible-vault encrypt vault.yml
```

## Custom Execution Environment

SSM playbooks require `awscli` in the EE:

```bash
cd context
ansible-builder build -f execution-environment.yml -t ee-cloud-native-automation:latest
```

## Hybrid REST/CLI approach

Azure runbook **run** and **schedule** use `ansible.builtin.uri` against Azure Resource Manager because `azure_rm_automationrunbook` only supports CRUD. AWS SSM execution uses AWS CLI for the same reason.

## Apply CasC

```bash
ansible-playbook playbooks/aap_config.yml --vault-id @prompt
```

## Multicloud inventory (UC4)

Groups `azure_automation` and `aws_automation` under child inventories document where native cloud automation targets live in the AAP hierarchy.
