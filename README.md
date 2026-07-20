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

| Phase | Workflow / playbook | Purpose | Mode |
|---|---|---|---|
| 0. Pre-flight (optional) | `Azure - Connectivity check (dry run)`, `Azure - Permissions check (dry run)`, `Azure - Runbook preview (dry run)`, `AWS - Connectivity check (dry run)`, `AWS - Permissions check (dry run)`, `AWS - SSM preview (dry run)`, `Network - Connectivity path check (dry run)`, `Notify - SMTP preflight check (dry run)` | Read-only checks before mutating anything — see [Dry-run / preview templates](#dry-run--preview-templates) | Always |
| 1. Setup | `WF - Demo setup` | Provision Azure runbook, EC2 instance, SSM document, maintenance window | Lab/dev only |
| 2. Azure scenario | `WF - Azure Runbook execute and collect` | Run runbook and collect output | Always |
| 2. Azure scenario | `WF - Azure Runbook schedule` | Create recurring runbook schedule | Always |
| 2. AWS scenario | `WF - AWS SSM document execute and collect` | Run SSM document on EC2 target | Always |
| 2. AWS scenario | `WF - AWS SSM schedule via maintenance window` | Register scheduled SSM task | Always |
| 3. Teardown | `WF - Demo teardown` | Remove all demo resources | Lab/dev only |

Phases 1 and 3 only exist when `demo_manage_infrastructure: true` (default); see [Deployment modes](#deployment-modes) for the customer/PoC mode that runs phase 2 (and the optional phase 0 dry-run checks) only, against pre-existing infrastructure.

## Azure authentication mode

`azure_auth_mode` in `demo_variables.yml` (default `service_principal`) selects how every Azure ARM REST call authenticates, independent of the deployment mode below:

| `azure_auth_mode` | Requires | Notes |
|---|---|---|
| `service_principal` (default) | `vault_azure_client_id` / `vault_azure_client_secret` | Token acquired via an OAuth2 client-credentials POST. Works on any AAP topology and is the only option if AAP does not run on Azure. |
| `msi` | Nothing stored in AAP | Token acquired from the Azure Instance Metadata Service (IMDS) endpoint. AAP's execution node/EE container must itself be an Azure resource with a Managed Identity enabled — see [docs/setup.md](docs/setup.md#azure-authentication-mode-service-principal-vs-managed-identity) |

`azure_auth_mode` must be threaded through `extra_vars` on every Azure-facing job template (already done in `group_vars/all/job_templates.yml` / `job_templates_infra.yml`): `playbooks/demo/*.yml` and `playbooks/setup/*.yml` run against AAP's generated inventory, which does not reliably auto-load `group_vars/all/demo_variables.yml`.

## Deployment modes

`demo_manage_infrastructure` in `demo_variables.yml` (default `true`) controls how much of the AAP catalog this CasC creates:

| Mode | `demo_manage_infrastructure` | AAP objects created | Use when |
|---|---|---|---|
| Lab / dev | `true` (default) | Full lifecycle: `Setup - Azure runbook`, `Setup - AWS SSM resources`, `Teardown - Azure runbook`, `Teardown - AWS SSM resources`, `WF - Demo setup`, `WF - Demo teardown`, plus all scenario and dry-run objects | You are running the demo yourself and want AAP to create and destroy the Azure Automation Account and AWS networking/IAM/EC2 target |
| Customer / PoC | `false` | Only the scenario job templates (`Azure - Run Runbook and collect output`, `Azure - Schedule Runbook`, `AWS - Run SSM document and collect output`, `AWS - Schedule SSM via maintenance window`, `Notify - Email automation results`), the four dry-run templates, and their workflows | The customer already provides the Automation Account and SSM target; no provisioning or teardown object is created in AAP, removing any risk of accidentally launching a job that creates a duplicate Automation Account or tears down the customer's existing SSM target |

In customer mode, set `azure_automation_resource_group` / `azure_automation_account` / `azure_runbook_name` and `aws_ssm_document_name` / `aws_ssm_target_instance_id` to the customer's existing resources, and scope the Azure/AWS credentials down to the reduced permission set (see [docs/setup.md](docs/setup.md)).

`group_vars/all/demo_variables.yml.example` **and** `vault.yml.example` mark every variable/secret with `[ALWAYS REQUIRED]` or `[LAB/DEV ONLY]` banners so you can see at a glance what customer/PoC mode needs. `playbooks/aap_config.yml` and `playbooks/verify.yml` enforce this: the `[LAB/DEV ONLY]` variables are only validated when `demo_manage_infrastructure: true`, so leaving them at their example defaults never blocks a customer/PoC deployment.

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
    azure_precheck_connectivity.yml   Dry-run: Azure token + Automation Account reachability
    azure_precheck_permissions.yml    Dry-run: Azure RBAC action check on the resource group
    azure_runbook_preview.yml         Dry-run: runbook state + recent jobs, never starts a job
    aws_ssm_run_document.yml
    aws_ssm_schedule_maintenance.yml
    aws_precheck_connectivity.yml     Dry-run: AWS auth + SSM agent online check
    aws_precheck_permissions.yml      Dry-run: AWS IAM action simulation, never performs the actions
    aws_ssm_preview.yml               Dry-run: document/instance/window checks, never starts an execution
    precheck_network_path.yml         Dry-run: TCP reachability to Azure/AWS API endpoints (no auth)
    precheck_smtp.yml                 Dry-run: SMTP reachability + STARTTLS/LOGIN, never sends a message
    notify_results.yml
group_vars/all/
  demo_variables.yml.example
  organizations.yml, credentials.yml, inventories.yml, projects.yml
  execution_environments.yml, labels.yml
  job_templates.yml, workflow_templates.yml           Always-deployed objects
  job_templates_infra.yml, workflow_templates_infra.yml   Lab/dev-only provisioning/teardown objects
context/
  execution-environment.yml   Custom EE with awscli
files/
  smtp_auth_check.py   STARTTLS/LOGIN-only helper used by precheck_smtp.yml
docs/
  setup.md, procedures.md, testing.md, verification.md
```

## Prerequisites

- Python `boto3` on the control node — required by `amazon.aws` collection modules
  (`pip3 install boto3`).
- AWS CLI on the control node — required by setup playbooks for SSM document creation,
  maintenance window registration, and SSM agent polling. No certified Ansible module
  covers these operations (`pip3 install awscli`).
- Azure Service Principal (default) or Managed Identity — see
  [Azure authentication mode](#azure-authentication-mode) — with appropriate
  permissions. Two resource modes are supported:
  - **Bring-your-own** (default): supply names of a pre-existing resource group and
    Automation Account; the credential needs Automation Contributor on the
    resource group.
  - **Create from scratch**: set `azure_create_automation_account: true` in
    `demo_variables.yml`; `01_azure_setup.yml` creates the resource group and
    Automation Account. The credential needs Contributor on the subscription
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

The **Setup** and **Teardown** templates are only created in AAP when `demo_manage_infrastructure: true` (see [Deployment modes](#deployment-modes)); the **scenario** and **dry-run** templates are always created.

| Template | Playbook | Mode |
|---|---|---|
| Setup - Azure runbook | `setup/01_azure_setup.yml` | Lab/dev only |
| Setup - AWS SSM resources | `setup/02_aws_setup.yml` | Lab/dev only |
| Teardown - Azure runbook | `setup/01_azure_teardown.yml` | Lab/dev only |
| Teardown - AWS SSM resources | `setup/02_aws_teardown.yml` | Lab/dev only |
| Azure - Run Runbook and collect output | `demo/azure_runbook_run.yml` | Always |
| Azure - Schedule Runbook | `demo/azure_runbook_schedule.yml` | Always |
| AWS - Run SSM document and collect output | `demo/aws_ssm_run_document.yml` | Always |
| AWS - Schedule SSM via maintenance window | `demo/aws_ssm_schedule_maintenance.yml` | Always |
| Notify - Email automation results | `demo/notify_results.yml` (optional) | Always |

### Dry-run / preview templates

Read-only checks, useful in both deployment modes. Never wired into any workflow — launch standalone before (or instead of) the scenario workflows.

| Template | Playbook | Checks |
|---|---|---|
| Azure - Connectivity check (dry run) | `demo/azure_precheck_connectivity.yml` | Acquires an Azure token (SP or MSI) and confirms the Automation Account is reachable |
| Azure - Permissions check (dry run) | `demo/azure_precheck_permissions.yml` | Confirms the configured identity's RBAC role actually grants every action the scenario templates perform — a Reader-level identity passes the connectivity check above but fails here |
| Azure - Runbook preview (dry run) | `demo/azure_runbook_preview.yml` | Confirms the runbook is published, lists its recent jobs, reports the job name pattern the real run would create — never starts a job |
| AWS - Connectivity check (dry run) | `demo/aws_precheck_connectivity.yml` | Confirms AWS auth and that the SSM target instance is registered and online |
| AWS - Permissions check (dry run) | `demo/aws_precheck_permissions.yml` | Uses `aws iam simulate-principal-policy` to confirm every SSM action the scenario templates call evaluates to allowed, without performing any of them |
| AWS - SSM preview (dry run) | `demo/aws_ssm_preview.yml` | Confirms the Automation document and maintenance window exist, reports the parameters the real run would pass to `start-automation-execution` — never starts an execution |
| Network - Connectivity path check (dry run) | `demo/precheck_network_path.yml` | Opens a plain TCP connection (no auth) to the Azure ARM/AAD and AWS STS/SSM/EC2 endpoints, isolating firewall/proxy/DNS problems from credential problems |
| Notify - SMTP preflight check (dry run) | `demo/precheck_smtp.yml` | Confirms the SMTP server is reachable and the account can authenticate (STARTTLS + LOGIN) — no message is sent. Skipped when `enable_email_notification: false` |

## Collections

| Collection | Tier | Purpose |
|---|---|---|
| infra.aap_configuration | validated | CasC dispatch |
| ansible.controller | certified | Explicit object deletion in `aap_cleanup.yml` |
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
| SSM execution times out | SSM agent not registered on EC2 | Check instance profile; `02_aws_setup.yml` waits for registration; run `AWS - Connectivity check (dry run)` to confirm `PingStatus: Online` before launching the scenario workflow |
| `aws ssm create-document` fails with `DocumentAlreadyExists` | Document name already used | Delete manually (`aws ssm delete-document --name ...`) or change `aws_ssm_document_name` |
| Email notification skipped | `enable_email_notification` is `false` (default) | Set to `true` and configure SMTP variables |
| Azure MSI token request fails (`Managed Identity ... not found` or connection refused to `169.254.169.254`) | `azure_auth_mode: msi` set, but the AAP execution node/EE container does not run on Azure, or no Managed Identity is enabled on it | Enable a system- or user-assigned identity on the Azure resource running the execution node, or set `azure_auth_mode: service_principal` and configure `vault_azure_client_id`/`vault_azure_client_secret` instead |
| `Azure - Runbook preview (dry run)` fails with runbook state not `Published` | Runbook created but never published, or deleted outside Ansible | Run `01_azure_setup.yml` again (idempotent) to republish it |
| `Azure - Permissions check (dry run)` fails on a specific action | Configured identity has a role narrower than Automation Contributor on the resource group | Assign Automation Contributor (or Contributor) on `azure_automation_resource_group` |
| `AWS - Permissions check (dry run)` fails on `simulate-principal-policy` itself (not on an action) | Caller lacks `iam:SimulatePrincipalPolicy` on its own ARN | Attach a policy granting `iam:SimulatePrincipalPolicy` scoped to the caller's own ARN (self-test only, no other permissions) |
| `Network - Connectivity path check (dry run)` reports an endpoint unreachable | Outbound HTTPS blocked by firewall/proxy, or DNS resolution failure from the AAP execution node | Check egress rules for port 443 and DNS resolution before assuming a credentials problem |
| `Notify - SMTP preflight check (dry run)` fails on port reachability | SMTP host/port blocked by firewall, or wrong port for the provider | Confirm `smtp_host`/`smtp_port` and that egress on that port is allowed |
| `Notify - SMTP preflight check (dry run)` fails on authentication | Wrong `smtp_username`/`vault_smtp_password`, or STARTTLS required but `smtp_use_tls: false` | Verify credentials; most providers require `smtp_use_tls: true` on port 587 |

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
