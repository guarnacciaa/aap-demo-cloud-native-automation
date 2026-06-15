# Environment setup

## Requirements

| Component | Version |
|---|---|
| Red Hat Ansible Automation Platform | 2.6+ |
| Azure Automation Account | Existing account; runbook is created by setup playbook |
| AWS IAM user | `ssm:*`, `ec2:*`, `ssm:CreateMaintenanceWindow` permissions |
| AWS IAM instance profile | `AmazonSSMManagedInstanceCore` attached |
| Network | Outbound HTTPS from AAP to Azure Management API and AWS API endpoints |

## Supporting dependencies

The following cloud resources are created by the setup playbooks before the demo
can run. No manual cloud console steps are required.

| Dependency | Playbook | Teardown playbook | Job template |
|---|---|---|---|
| Azure Automation runbook | `playbooks/setup/01_azure_setup.yml` | `01_azure_teardown.yml` | Setup - Azure runbook |
| AWS SSM Automation document | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources |
| AWS EC2 instance (SSM target) | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources |
| AWS maintenance window | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources |

The `WF - Demo setup` workflow runs the Azure and AWS setup steps in sequence
from the Controller UI.

## Step 1 — Install collections

```bash
cd artifacts/demos/aap-demo-cloud-native-automation
ansible-galaxy collection install -r collections/requirements.yml -p collections
cp ansible.cfg.example ansible.cfg
```

## Step 2 — Configure variables and vault

```bash
cp group_vars/all/demo_variables.yml.example group_vars/all/demo_variables.yml
cp vault.yml.example vault.yml
ansible-vault encrypt vault.yml
```

Edit `group_vars/all/demo_variables.yml` and set at minimum:

- `aap_hostname` — Controller hostname or Gateway URL
- `azure_subscription_id`, `azure_tenant_id`
- `azure_automation_resource_group`, `azure_automation_account`
- `aws_region`, `aws_account_id`
- `aws_ec2_ami_id` — Amazon Linux 2023 or RHEL AMI in your region
- `aws_ec2_vpc_subnet_id`, `aws_ec2_security_group_ids`
- `aws_ec2_iam_instance_profile` — IAM instance profile with `AmazonSSMManagedInstanceCore`
- `demo_project_scm_url`

Edit `vault.yml` (after encrypting) and set:

- `vault_controller_username`, `vault_controller_password`
- `vault_azure_client_id`, `vault_azure_client_secret`
- `vault_aws_access_key`, `vault_aws_secret_key`
- `vault_smtp_password` (only when `enable_email_notification: true`)

## Step 3 — Build and push the custom Execution Environment

The SSM playbooks require `awscli` inside the EE. Build from the provided
`context/execution-environment.yml`:

```bash
cd context
ansible-builder build -f execution-environment.yml -t ee-cloud-native-automation:latest
```

Push the image to your registry and update `demo_execution_environment_name` in
`demo_variables.yml` if the image name differs.

## Step 4 — Run setup playbooks

Run these from the artifact root in order:

```bash
ansible-playbook playbooks/setup/01_azure_setup.yml --vault-id @prompt
ansible-playbook playbooks/setup/02_aws_setup.yml --vault-id @prompt
```

After `02_aws_setup.yml` completes, the playbook prints:

- **EC2 instance ID** — copy this value into `aws_ssm_target_instance_id` in `demo_variables.yml`
- **Maintenance window ID** — copy into `aws_ssm_maintenance_window_id`

Alternatively, launch the `WF - Demo setup` workflow from the Controller UI after
applying CasC (Step 5).

## Step 5 — Apply CasC

```bash
ansible-playbook playbooks/aap_config.yml --vault-id @prompt
```

This creates all Controller objects: organization, credentials, inventories, project,
execution environment, job templates, and workflow templates.

## Step 6 — Verify the environment

```bash
ansible-playbook playbooks/verify.yml --vault-id @prompt
```

## Hybrid REST/CLI approach

Azure runbook creation, execution, and scheduling use `ansible.builtin.uri` against
the Azure Resource Manager REST API. `azure.azcollection` does not expose runbook
content upload or execution modules; this constraint is documented in each playbook
header.

AWS SSM automation runs via the `aws` CLI (included in the custom EE). No certified
collection module exists for SSM Automation execution or maintenance window task
registration.

## Teardown and reset

To remove all demo resources:

```bash
# Remove Controller objects
ansible-playbook playbooks/aap_cleanup.yml -e demo_cleanup_confirm=true --vault-id @prompt

# Remove supporting cloud resources
ansible-playbook playbooks/setup/01_azure_teardown.yml -e demo_cleanup_confirm=true --vault-id @prompt
ansible-playbook playbooks/setup/02_aws_teardown.yml -e demo_cleanup_confirm=true --vault-id @prompt
```

Or launch the `WF - Demo teardown` workflow from the Controller UI with
`demo_cleanup_confirm=true` as an extra variable.
