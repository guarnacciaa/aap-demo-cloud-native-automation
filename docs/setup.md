# Environment setup

## Deployment mode: lab/dev vs customer/PoC

Set `demo_manage_infrastructure` in `group_vars/all/demo_variables.yml` **before** running `aap_config.yml`:

| `demo_manage_infrastructure` | Scenario | What CasC creates |
|---|---|---|
| `true` (default) | Lab, dev, or self-running the full demo; no pre-existing Azure Automation Account or AWS SSM target | `Setup - Azure runbook`, `Setup - AWS SSM resources`, `Teardown - Azure runbook`, `Teardown - AWS SSM resources` job templates, `WF - Demo setup`, `WF - Demo teardown`, plus all scenario and dry-run objects |
| `false` | Deploying at a customer site where the Automation Account and SSM target already exist | Only the scenario job templates (`Azure - Run Runbook and collect output`, `Azure - Schedule Runbook`, `AWS - Run SSM document and collect output`, `AWS - Schedule SSM via maintenance window`, `Notify - Email automation results`), the four dry-run templates, and their workflows |

The flag is read in `playbooks/aap_config.yml`: when `true`, the objects defined in `group_vars/all/job_templates_infra.yml` and `group_vars/all/workflow_templates_infra.yml` are merged into the lists the `infra.aap_configuration` dispatch role applies; when `false`, those two files are still loaded (Ansible auto-loads every file under `group_vars/all/`) but never merged in, so their objects are never created in AAP.

### Which variables to set in each mode

`group_vars/all/demo_variables.yml.example` **and** `vault.yml.example` group every variable/secret under the same banner:

- `[ALWAYS REQUIRED]` — needed regardless of mode: AAP connection, object names, Git repo, credential names, the AWS SSM identity variables (`aws_region`, `aws_ssm_document_name`, `aws_ssm_maintenance_window_id`, `aws_ssm_maintenance_task_name`, `aws_ssm_service_role_arn`, `aws_account_id`), the Azure Automation identity variables (`azure_subscription_id`, `azure_tenant_id`, `azure_automation_resource_group`, `azure_automation_account`, `azure_runbook_name`, `azure_job_schedule_name` and the schedule timing variables) — the scenario job templates authenticate against and target these objects in both modes. `vault_azure_client_id`/`vault_azure_client_secret` are further conditional on a second, independent axis: `azure_auth_mode` (see [Azure authentication mode](#azure-authentication-mode-service-principal-vs-managed-identity)) — only required when it is `service_principal` (the default), unused when it is `msi`.
- `aws_ssm_target_instance_id` / `aws_ssm_document_parameters` — **optional, mutually complementary**: set `aws_ssm_target_instance_id` only when `aws_ssm_document_name` runs `aws:runCommand` steps against an SSM-managed instance (the default lab/dev EC2 target). Leave it empty (`""`, the default) and use `aws_ssm_document_parameters` (a list of `"Key=Value"` strings) instead when the document orchestrates AWS API calls directly — for example a document whose real target is an EKS cluster (`ClusterName=...`), a Lambda function, or any other non-instance resource. Neither variable is validated in `aap_config.yml`'s pre-task assertions, since which one applies depends on the document's own design, not on the deployment mode.
- `[LAB/DEV ONLY]` — consumed exclusively by `Setup - *` / `Teardown - *`: `azure_create_automation_account`, `azure_resource_group_location`, `azure_automation_account_sku`, `azure_runbook_description`, and the whole AWS networking/IAM/EC2 provisioning block (`aws_create_network_resources`, EC2 instance settings, bring-your-own and create-from-scratch network/IAM variables, maintenance window creation settings) in `demo_variables.yml.example`. No secret in this demo is exclusively lab/dev-only today — see `vault.yml.example`.

Both `playbooks/aap_config.yml` (pre-task assertions) and `playbooks/verify.yml` enforce this split: the `[LAB/DEV ONLY]` checks only run `when: demo_manage_infrastructure | bool`, so a customer/PoC deployment fails fast only on the variables it actually needs, never on unrelated provisioning variables.

When `demo_manage_infrastructure: false`:

- Set `azure_automation_resource_group` / `azure_automation_account` / `azure_runbook_name` to the customer's existing Automation Account and runbook.
- Set `aws_ssm_document_name` / `aws_ssm_maintenance_window_id` / `aws_ssm_service_role_arn` / `aws_account_id` to the customer's existing SSM Automation document and maintenance window. Set `aws_ssm_target_instance_id` to the target instance ID only if the document runs commands on an SSM-managed instance; otherwise leave it empty and set `aws_ssm_document_parameters` to whatever the document actually expects (for example an EKS cluster name).
- Request Azure/AWS credentials scoped to **run + read only** (see [Reduced credential scope for customer/PoC mode](#reduced-credential-scope-for-customer-poc-mode) below) — the full provisioning permissions in [Azure Automation Account mode](#azure-automation-account-mode) and [AWS networking and IAM mode](#aws-networking-and-iam-mode) are not needed since no provisioning/teardown job template exists to use them.
- Switching modes later: change the flag and re-run `ansible-playbook playbooks/aap_config.yml --vault-id @prompt`. Going from `true` to `false` does **not** remove the infra job/workflow templates already created in AAP (dispatch only reconciles objects it is told about); delete them explicitly with `ansible-playbook playbooks/aap_cleanup.yml -e demo_cleanup_confirm=true --vault-id @prompt` and re-apply, or delete them manually from the Controller UI.

### Reduced credential scope for customer/PoC mode

When `demo_manage_infrastructure: false`, request credentials limited to:

- **Azure Service Principal**: `Microsoft.Automation/automationAccounts/read`, `Microsoft.Automation/automationAccounts/runbooks/*`, `Microsoft.Automation/automationAccounts/jobs/*`, `Microsoft.Automation/automationAccounts/jobSchedules/*`, `Microsoft.Automation/automationAccounts/schedules/*` on the resource group containing the existing Automation Account.
- **AWS IAM user or role**: `ssm:StartAutomationExecution`, `ssm:GetAutomationExecution`, `ssm:DescribeInstanceInformation`, `ssm:RegisterTaskWithMaintenanceWindow`, `ssm:DescribeDocument`, `ssm:DescribeMaintenanceWindows`, `sts:GetCallerIdentity`.

Do not request the `iam:CreateRole`/`iam:AttachRolePolicy`/`iam:CreateInstanceProfile`-family AWS permissions or the `Microsoft.Automation/automationAccounts/write`/resource-group-create Azure permissions listed below; they are only used by the setup and teardown playbooks, which are not deployed in this mode.

### Optional dry-run/preview job templates — additional permissions

Four read-only checks beyond the connectivity/preview templates above need a
little more than pure Reader access to prove anything useful; each is
optional and safe to skip if you would rather not grant the extra permission:

- **`Azure - Permissions check (dry run)`** calls `Microsoft.Authorization/permissions/list-for-resource-group`, which every role holder can call at their own scope — no extra Azure permission is required beyond the roles above.
- **`AWS - Permissions check (dry run)`** calls `aws iam simulate-principal-policy`, which requires the caller to additionally hold `iam:SimulatePrincipalPolicy` **scoped to its own ARN** (a self-test permission; it does not grant access to anything else). Without it the check fails on the simulation call itself, with a message naming the missing permission.
- **`Network - Connectivity path check (dry run)`** and **`Notify - SMTP preflight check (dry run)`** perform no authenticated calls at all (plain TCP connect, and STARTTLS+LOGIN respectively) and need no additional cloud IAM/RBAC permission.

## Azure authentication mode: Service Principal vs Managed Identity

`azure_auth_mode` in `group_vars/all/demo_variables.yml` (default `service_principal`) controls how every Azure Automation REST API call (token acquisition in `azure_runbook_run.yml`, `azure_runbook_schedule.yml`, `01_azure_setup.yml`, `01_azure_teardown.yml`, and the dry-run playbooks) authenticates to Azure. This is independent of `demo_manage_infrastructure` above — it applies in every deployment mode.

| `azure_auth_mode` | How it authenticates | Requirements |
|---|---|---|
| `service_principal` (default) | `azure_client_id` + `azure_client_secret` + `azure_tenant_id` are exchanged for a Resource Manager access token via an OAuth2 client-credentials POST to `login.microsoftonline.com` | `vault_azure_client_id` and `vault_azure_client_secret` in `vault.yml`. Works regardless of where AAP is hosted. |
| `msi` | The access token is requested from the Azure Instance Metadata Service (IMDS) endpoint (`http://169.254.169.254/metadata/identity/oauth2/token`) instead; no client secret is stored in AAP at all | The AAP execution node or execution environment container that actually runs the job must itself be an Azure resource (VM, VMSS, AKS node, etc.) with a system- or user-assigned Managed Identity enabled, and that identity must hold the same RBAC role documented in [Azure Automation Account mode](#azure-automation-account-mode) / [Reduced credential scope for customer/PoC mode](#reduced-credential-scope-for-customer-poc-mode). |

Notes:

- AAP's built-in "Microsoft Azure Resource Manager" credential type has **no Managed Identity input field** — it only supports Service Principal or Active Directory user/password. The IMDS token request is a capability implemented directly in this demo's playbooks (`ansible.builtin.uri` against the metadata endpoint), not something the Controller credential injects. The Azure credential is still created in `msi` mode (with only `azure_subscription_id` populated) so job templates keep a stable credential association, but `client`/`secret`/`tenant` are omitted entirely — no secret is ever stored.
- Choose `msi` only when you know AAP's execution nodes run on Azure infrastructure with an identity attached. In every other topology (on-prem, another cloud, OpenShift not on Azure), `service_principal` is the only option that works.
- `playbooks/aap_config.yml` and `playbooks/verify.yml` validate `azure_auth_mode` and only require the Service Principal vault secrets when it is set to `service_principal` (the default).
- Switching modes: change `azure_auth_mode` and re-run `ansible-playbook playbooks/aap_config.yml --vault-id @prompt` to update the Azure credential's stored inputs.
- **`azure_auth_mode` must be threaded through each job template's `extra_vars`** (see `group_vars/all/job_templates.yml` / `job_templates_infra.yml`). AAP runs `playbooks/demo/*.yml` and `playbooks/setup/*.yml` against its own generated inventory, not this repository's `inventory.yml`, so `group_vars/all/demo_variables.yml` is **not** auto-loaded for those nested playbooks the way it is for `playbooks/aap_config.yml` and `playbooks/verify.yml`. If a job template is missing `azure_auth_mode` in its `extra_vars`, the token acquisition tasks silently fall back to the `service_principal` branch — even with `azure_auth_mode: msi` set correctly in `demo_variables.yml` — and the Service Principal token request then fails because `azure_client_id`/`azure_client_secret` are empty. Re-run `aap_config.yml` after editing `extra_vars` so the stored job template definitions pick up the change.

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
| AWS networking (VPC, subnet, internet gateway, route table, security group) | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources | create-from-scratch only |
| AWS IAM (EC2 instance role/profile, SSM service role) | `playbooks/setup/02_aws_setup.yml` | `02_aws_teardown.yml` | Setup - AWS SSM resources | create-from-scratch only |

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

- `demo_manage_infrastructure` — `true` (default) for lab/dev, `false` for customer/PoC
  against pre-existing infrastructure (see [Deployment mode](#deployment-mode-labdev-vs-customerpoc) above)
- `aap_hostname` — Controller hostname or Gateway URL
- `azure_auth_mode` — `service_principal` (default) or `msi` (see
  [Azure authentication mode](#azure-authentication-mode-service-principal-vs-managed-identity) above)
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

`smtp_username`/`vault_smtp_password` are not passed to the Notify job templates as
plain `extra_vars` (unlike `smtp_host`/`smtp_port`/`notification_to`). They are instead
stored on the **SMTP Credentials** custom credential (`smtp_credential_name` in
`demo_variables.yml`, created by `group_vars/all/credential_types.yml` and
`credentials.yml`), which injects them as `extra_vars` at job-run time — the password
is never returned in plaintext by the Controller API/UI, before or after injection.

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
| EC2 instance ID | `aws_ssm_target_instance_id` (only relevant for instance-targeting documents — see [Which variables to set in each mode](#which-variables-to-set-in-each-mode)) |
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

Optionally, launch the eight read-only dry-run job templates from the Controller UI
(`Azure - Connectivity check (dry run)`, `Azure - Permissions check (dry run)`,
`Azure - Runbook preview (dry run)`, `AWS - Connectivity check (dry run)`,
`AWS - Permissions check (dry run)`, `AWS - SSM preview (dry run)`,
`Network - Connectivity path check (dry run)`, `Notify - SMTP preflight check
(dry run)`) before the scenario workflows — see
[docs/procedures.md](procedures.md) for the equivalent `ansible-playbook`
invocations. They never create, modify, or delete any resource.

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
