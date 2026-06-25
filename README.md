# Azure Runbook and AWS SSM Automation Demo

![Status](https://img.shields.io/badge/Status-Ready-brightgreen)
![Red Hat Ansible Automation Platform](https://img.shields.io/badge/AAP-2.6-red)
![Configuration as Code](https://img.shields.io/badge/CasC-infra.aap_configuration-blue)
![Azure Automation](https://img.shields.io/badge/Azure-Automation-0078d4)
![AWS SSM](https://img.shields.io/badge/AWS-Systems_Manager-ff9900)

## Introduction

Orchestrates Azure Automation Runbooks and AWS Systems Manager Automation documents
from AAP: immediate execution, scheduling, output collection, and optional email
notification. Setup playbooks provision all required cloud resources — no manual
cloud console steps are needed.

## How to run the demo

| Phase | Workflow / playbook | Purpose |
|---|---|---|
| 1. Setup | `WF - Demo setup` | Provision Azure runbook, EC2 instance, SSM document, maintenance window |
| 2. Azure scenario | `WF - Azure Runbook execute and collect` | Run runbook and collect output |
| 2. Azure scenario | `WF - Azure Runbook schedule` | Create recurring runbook schedule |
| 2. AWS scenario | `WF - AWS SSM document execute and collect` | Run SSM document on EC2 target |
| 2. AWS scenario | `WF - AWS SSM schedule via maintenance window` | Register scheduled SSM task |
| 3. Teardown | `WF - Demo teardown` | Remove all demo resources |

## Quick start

```bash
cd artifacts/demos/aap-demo-cloud-native-automation
ansible-galaxy collection install -r collections/requirements.yml -p collections
cp ansible.cfg.example ansible.cfg
cp group_vars/all/demo_variables.yml.example group_vars/all/demo_variables.yml
cp vault.yml.example vault.yml && ansible-vault encrypt vault.yml
```

Edit `demo_variables.yml` and `vault.yml` with your environment values,
then run the setup playbooks in order:

```bash
ansible-playbook playbooks/setup/01_azure_setup.yml --vault-id @prompt
ansible-playbook playbooks/setup/02_aws_setup.yml --vault-id @prompt
```

After `02_aws_setup.yml` prints the EC2 instance ID and maintenance window ID,
copy those values into `demo_variables.yml`, then apply CasC:

```bash
ansible-playbook playbooks/aap_config.yml --vault-id @prompt
```

See [docs/setup.md](docs/setup.md) for full step-by-step instructions and EE
build guidance.

## Architecture

```
+---------------------------------------------------------------+
|  AAP Controller                                               |
|                                                               |
|  WF - Azure Runbook          WF - AWS SSM document            |
|  execute and collect         execute and collect              |
|        |                           |                          |
|  [Azure - Run Runbook]       [AWS - Run SSM document]         |
|        |                           |                          |
|  [Notify - Email] (opt)      [Notify - Email] (opt)           |
+--------|---------------------------|---------------------------+
         |  ARM REST                 |  aws ssm CLI
         v                           v
+--------------------+     +------------------------------+
|  Azure Automation  |     |  AWS Systems Manager         |
|  Account           |     |                              |
|  Runbook           |     |  Automation document         |
|  (01_azure_setup)  |     |  EC2 instance  (02_aws_setup)|
+--------------------+     +------------------------------+
```

## Repository structure

```
playbooks/
  aap_config.yml          Apply CasC
  aap_cleanup.yml         Remove Controller objects
  verify.yml              Smoke test prerequisites
  setup/
    01_azure_setup.yml    Create Azure runbook (optionally also RG + Automation Account)
    01_azure_teardown.yml Delete Azure runbook (optionally also RG + Automation Account)
    02_aws_setup.yml      Create SSM document, EC2 instance, maintenance window
    02_aws_teardown.yml   Remove AWS resources
  demo/
    azure_runbook_run.yml
    azure_runbook_schedule.yml
    aws_ssm_run_document.yml
    aws_ssm_schedule_maintenance.yml
    notify_results.yml
group_vars/all/
  demo_variables.yml.example
  organizations.yml, credentials.yml, inventories.yml, projects.yml
  execution_environments.yml, labels.yml
  job_templates.yml, workflow_templates.yml
context/
  execution-environment.yml   Custom EE with awscli
docs/
  setup.md, procedures.md, testing.md, verification.md
```

## Prerequisites

- Python `boto3` on the control node — required by `amazon.aws` collection modules
  (`pip3 install boto3`).
- AWS CLI on the control node — required by setup playbooks for SSM document creation,
  maintenance window registration, and SSM agent polling. No certified Ansible module
  covers these operations (`pip3 install awscli`).
- Azure service principal with appropriate permissions — two modes are supported:
  - **Bring-your-own** (default): supply names of a pre-existing resource group and
    Automation Account; the service principal needs Automation Contributor on the
    resource group.
  - **Create from scratch**: set `azure_create_automation_account: true` in
    `demo_variables.yml`; `01_azure_setup.yml` creates the resource group and
    Automation Account. The service principal needs Contributor on the subscription
    (or on the target resource group scope). The teardown playbook removes both objects.
- AWS IAM user with `ssm:*`, `ec2:*`, `iam:*`, and maintenance window permissions.
- AWS EC2 networking and IAM instance profile — two modes are supported:
  - **Bring-your-own** (default): supply IDs for a pre-existing VPC subnet,
    security group, and IAM instance profile with `AmazonSSMManagedInstanceCore`.
  - **Create from scratch**: set `aws_create_network_resources: true` in
    `demo_variables.yml`; `02_aws_setup.yml` creates the VPC, subnet, internet
    gateway, route table, security group, IAM role, and instance profile.
    The teardown playbook removes all of these objects.

## Job templates

| Template | Playbook |
|---|---|
| Setup - Azure runbook | `setup/01_azure_setup.yml` |
| Setup - AWS SSM resources | `setup/02_aws_setup.yml` |
| Teardown - Azure runbook | `setup/01_azure_teardown.yml` |
| Teardown - AWS SSM resources | `setup/02_aws_teardown.yml` |
| Azure - Run Runbook and collect output | `demo/azure_runbook_run.yml` |
| Azure - Schedule Runbook | `demo/azure_runbook_schedule.yml` |
| AWS - Run SSM document and collect output | `demo/aws_ssm_run_document.yml` |
| AWS - Schedule SSM via maintenance window | `demo/aws_ssm_schedule_maintenance.yml` |
| Notify - Email automation results | `demo/notify_results.yml` (optional) |

## Collections

| Collection | Tier | Purpose |
|---|---|---|
| infra.aap_configuration | validated | CasC dispatch |
| azure.azcollection | certified | Azure authentication context |
| amazon.aws | certified | EC2 instance provisioning |
| community.general | community | Optional SMTP notification (no certified module) |

## REST/CLI design note

`azure.azcollection` does not expose runbook execution, content upload, or
publishing actions. `azure.azcollection` is used only for authentication context;
all Azure Automation operations use `ansible.builtin.uri` against the ARM REST API
directly. This constraint is documented in each affected playbook.

`amazon.aws` has no certified SSM Automation execution or maintenance window task
module. All SSM operations use the `aws` CLI embedded in the custom EE.

Document both constraints to customers reviewing support implications.

## Multicloud inventory structure

```
Demo-Multicloud
  Azure-Resources
    azure_automation  (group)
      azure-automation-anchor
  AWS-Resources
    aws_automation    (group)
      <ec2-instance-id>
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `aap_config.yml` fails on assert (`aap_hostname` or `demo_project_scm_url`) | Value still `CHANGE_ME` | Edit `demo_variables.yml` |
| `aap_config.yml` fails on assert (`azure_automation_account`) | Bring-your-own mode but account name not set | Set `azure_automation_account` in `demo_variables.yml`, or switch to `azure_create_automation_account: true` and run `01_azure_setup.yml` first |
| Azure ARM returns 403 on resource group or account creation | SP lacks Contributor role | Assign Contributor on the subscription or resource group scope |
| Azure ARM returns 403 on runbook operations | SP lacks Automation Contributor | Assign Automation Contributor on the resource group |
| SSM execution times out | SSM agent not registered on EC2 | Check instance profile; `02_aws_setup.yml` waits for registration |
| `aws ssm create-document` fails with `DocumentAlreadyExists` | Document name already used | Delete manually (`aws ssm delete-document --name ...`) or change `aws_ssm_document_name` |
| Email notification skipped | `enable_email_notification` is `false` (default) | Set to `true` and configure SMTP variables |

## Reset

```bash
ansible-playbook playbooks/aap_cleanup.yml -e demo_cleanup_confirm=true --vault-id @prompt
ansible-playbook playbooks/setup/01_azure_teardown.yml -e demo_cleanup_confirm=true --vault-id @prompt
ansible-playbook playbooks/setup/02_aws_teardown.yml -e demo_cleanup_confirm=true --vault-id @prompt
```

## References

- [Azure Automation REST API](https://learn.microsoft.com/en-us/rest/api/automation/)
- [AWS Systems Manager Automation documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html)
- [infra.aap_configuration collection](https://github.com/redhat-cop/aap_configuration)
- [Red Hat AAP 2.6 documentation](https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.6)

## License

Apache 2.0
