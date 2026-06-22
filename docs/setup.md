# Environment setup

## Requirements

| Component | Version / Notes |
|---|---|
| Red Hat Ansible Automation Platform | 2.6+ |
| Python + boto3 | Required on the control node for `amazon.aws` modules (`pip3 install boto3`) |
| AWS CLI (`awscli`) | Required on the control node for SSM document, maintenance window, and SSM agent tasks (`pip3 install awscli`) |
| Azure Automation Account | Existing account (bring-your-own) **or** created from scratch — see below |
| AWS IAM user | `ssm:*`, `ec2:*`, `iam:*`, `ssm:CreateMaintenanceWindow` permissions |
| AWS networking and IAM instance profile | Bring-your-own **or** created from scratch — see below |
| Network | Outbound HTTPS from AAP to Azure Management API and AWS API endpoints |

## Supporting dependencies

The following cloud resources are created by the setup playbooks before the demo
can run. No manual cloud console steps are required.

| Dependency | Playbook | Teardown playbook | Job template | Mode |
|---|---|---|---|---|
| Azure resource group | `playbooks/setup/01_azure_setup.yml` | `01_azure_teardown.yml` | Setup - Azure runbook | create-from-scratch only |
| Azure Automation Account | `playbooks/setup/01_azure_setup.yml` | `01_azure_teardown.yml` | Setup - Azure runbook | create-from-scratch only |
| Azure Automation runbook | `playbooks/setup/01_azure_setup.yml` | `01_azure_teardown.yml` | Setup - Azure runbook | always |
| AWS SSM Automation document | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources | always |
| AWS EC2 instance (SSM target) | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources | always |
| AWS maintenance window | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources | always |

The `WF - Demo setup` workflow runs the Azure and AWS setup steps in sequence
from the Controller UI.

## Step 1 — Install collections

```bash
cd artifacts/demos/aap-demo-cloud-native-automation
ansible-galaxy collection install -r collections/requirements.yml -p collections
cp ansible.cfg.example ansible.cfg
```

## Azure Automation Account mode

`01_azure_setup.yml` supports two modes, selected by `azure_create_automation_account`
in `demo_variables.yml`:

### Bring-your-own (default: `azure_create_automation_account: false`)

Use this mode when a resource group and Automation Account already exist in your Azure
subscription. The service principal must have **Automation Contributor** on the
resource group.

Set the following variables to the names of the pre-existing resources:

```yaml
azure_automation_resource_group: my-existing-rg
azure_automation_account: my-existing-automation-account
```

`01_azure_teardown.yml` removes only the demo runbook. The resource group and
Automation Account are not deleted.

### Create from scratch (`azure_create_automation_account: true`)

Use this mode when no Automation Account exists or when you want the demo to be fully
self-contained. `01_azure_setup.yml` creates:

- Resource group (`azure_automation_resource_group` / `azure_resource_group_location`)
- Automation Account (`azure_automation_account` / `azure_automation_account_sku`)
- The demo runbook inside the new account

The service principal needs **Contributor** on the subscription (or at minimum on the
resource group scope if the group already exists).

Set desired names for the new resources (not `CHANGE_ME`) and configure location and
SKU:

```yaml
azure_create_automation_account: true
azure_automation_resource_group: aap-demo-cna-rg
azure_automation_account: aap-demo-automation-account
azure_resource_group_location: eastus   # any valid Azure region
azure_automation_account_sku: Basic     # Basic or Free (Free: 500 job-minutes/month)
```

`01_azure_teardown.yml` removes the runbook, Automation Account, and resource group.
Deletion of the resource group is asynchronous and may take a few minutes to complete
in Azure.

## AWS networking and IAM mode

`02_aws_setup.yml` supports two modes, selected by `aws_create_network_resources` in
`demo_variables.yml`:

### Bring-your-own (default: `aws_create_network_resources: false`)

Use this mode when a suitable VPC, subnet, and security group already exist in your
AWS account. You must also have an IAM instance profile with the
`AmazonSSMManagedInstanceCore` policy attached.

Set the following variables to the IDs of the pre-existing resources:

```yaml
aws_ec2_vpc_subnet_id: subnet-xxxxxxxxxxxxxxxxx
aws_ec2_security_group_ids:
  - sg-xxxxxxxxxxxxxxxxx
aws_ec2_iam_instance_profile: MyExistingInstanceProfile
```

`02_aws_teardown.yml` removes only the EC2 instance, SSM document, and maintenance
window. It does not touch the pre-existing network or IAM objects.

### Create from scratch (`aws_create_network_resources: true`)

Use this mode when no suitable network exists or when you want the demo to be fully
self-contained. `02_aws_setup.yml` creates:

- VPC (`aws_vpc_name` / `aws_vpc_cidr`)
- Subnet (`aws_subnet_name` / `aws_subnet_cidr`), public, with internet gateway and route table
- Security group (`aws_sg_name`) — no inbound rules; all outbound allowed for SSM agent
- IAM role and instance profile (`aws_iam_role_name`) with `AmazonSSMManagedInstanceCore`

The IAM user running the playbook needs `iam:CreateRole`, `iam:AttachRolePolicy`,
`iam:CreateInstanceProfile`, `iam:AddRoleToInstanceProfile`, and related `iam:*`
permissions in addition to `ec2:*` and `ssm:*`.

`02_aws_teardown.yml` removes all of the above objects in addition to the EC2 instance,
SSM document, and maintenance window.

## Step 2 — Configure variables and vault

```bash
cp group_vars/all/demo_variables.yml.example group_vars/all/demo_variables.yml
cp vault.yml.example vault.yml
ansible-vault encrypt vault.yml
```

Edit `group_vars/all/demo_variables.yml` and set at minimum:

- `aap_hostname` — Controller hostname or Gateway URL
- `azure_subscription_id`, `azure_tenant_id`
- `azure_create_automation_account` — `false` (default) to use a pre-existing account,
  `true` to have `01_azure_setup.yml` create the resource group and Automation Account
  (see [Azure Automation Account mode](#azure-automation-account-mode) above)
- When `azure_create_automation_account: false`: set `azure_automation_resource_group`
  and `azure_automation_account` to existing resource names
- When `azure_create_automation_account: true`: set `azure_automation_resource_group`
  and `azure_automation_account` to desired names; configure `azure_resource_group_location`
  and `azure_automation_account_sku` as needed
- `aws_region`, `aws_account_id`
- `aws_ec2_ami_id` — Amazon Linux 2023 or RHEL AMI in your region
- `aws_create_network_resources` — `false` (default) to use pre-existing resources,
  `true` to have `02_aws_setup.yml` create the network and IAM profile from scratch
  (see [AWS networking and IAM mode](#aws-networking-and-iam-mode) above)
- When `aws_create_network_resources: false`: `aws_ec2_vpc_subnet_id`,
  `aws_ec2_security_group_ids`, `aws_ec2_iam_instance_profile`; set
  `aws_ec2_assign_public_ip: true` if the subnet is public and you want the
  instance to receive a public IP (the module does not always inherit the
  subnet's `MapPublicIpOnLaunch` setting)
- `demo_project_scm_url`

Edit `vault.yml` (after encrypting) and set:

- `vault_controller_username`, `vault_controller_password`
- `vault_azure_client_id`, `vault_azure_client_secret`
- `vault_aws_access_key`, `vault_aws_secret_key`
- `vault_smtp_password` (only when `enable_email_notification: true`)

## Step 3 — Build and push the custom Execution Environment

The demo job templates require a custom EE with `awscli`, `boto3`, `amazon.aws`,
and `azure.azcollection`. Install `ansible-builder` if not already present:

```bash
pip3 install ansible-builder
```

Build and push from the artifact root (not from `context/`). Replace
`<PAH-HOST>` with your Private Automation Hub hostname or IP:

```bash
# Build (requires access to registry.redhat.io and cloud.redhat.com)
ansible-builder build \
  -f context/execution-environment.yml \
  -t <PAH-HOST>/ee-cloud-native-automation:latest \
  --container-runtime podman

# Authenticate to PAH (add --tls-verify=false for self-signed certificates)
podman login <PAH-HOST> --tls-verify=false

# Push to Private Automation Hub
podman push <PAH-HOST>/ee-cloud-native-automation:latest --tls-verify=false
```

Then set the image URL in `demo_variables.yml`:

```yaml
demo_execution_environment_image: <PAH-HOST>/ee-cloud-native-automation:latest
```

`aap_config.yml` (Step 5) registers this URL in Controller and creates the PAH
Container Registry credential used to pull the image at job execution time.

## Step 4 — Run setup playbooks

Run these from the artifact root in order:

```bash
ansible-playbook playbooks/setup/01_azure_setup.yml --vault-id @prompt
ansible-playbook playbooks/setup/02_aws_setup.yml --vault-id @prompt
```

After `02_aws_setup.yml` completes, the playbook prints four values that must be
copied into `demo_variables.yml`:

| Printed value | Variable |
|---|---|
| EC2 instance ID | `aws_ssm_target_instance_id` |
| Maintenance window ID | `aws_ssm_maintenance_window_id` |
| AWS account ID | `aws_account_id` |
| SSM service role ARN | `aws_ssm_service_role_arn` |

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
