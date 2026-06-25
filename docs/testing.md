# Testing log

Tracks testing progress for this demo. Update after each session. For procedural verification steps, see [verification.md](verification.md).

**Status values:** `Not tested` · `Pass` · `Partial` · `Fail` · `Blocked`

## Status summary

### Entry playbooks

| Component | Status | Last tested | Notes |
|---|---|---|---|
| CasC apply (`aap_config.yml`) | Pass | 2026-06-25 | `failed=0 changed=9`; job templates updated with full extra_vars for setup/teardown templates |
| CasC cleanup (`aap_cleanup.yml`) | Not tested | — | |
| Smoke test (`verify.yml`) | Pass | 2026-06-22 | `failed=0`; confirms awscli, boto3, and required variables present |

### Execution environments

| Component | Status | Last tested | Notes |
|---|---|---|---|
| EE build and push | Pass | 2026-06-22 | Built with ee-supported-rhel9/Python 3.12 and pushed to PAH; awscli installed via pip (not RPM — not in standard RHEL9 repos) |

### Inventories

| Component | Status | Last tested | Notes |
|---|---|---|---|
| Azure-Resources (source) | Not tested | — | |
| AWS-Resources (source) | Not tested | — | |
| Demo-Multicloud (parent) | Not tested | — | |

### Setup playbooks (local run)

| Component | Status | Last tested | Notes |
|---|---|---|---|
| `01_azure_setup.yml` (create-from-scratch) | Pass | 2026-06-25 | Tested as AAP job template via WF - Demo setup |
| `01_azure_setup.yml` (bring-your-own) | Not tested | — | |
| `02_aws_setup.yml` (create-from-scratch) | Pass | 2026-06-25 | Tested as AAP job template via WF - Demo setup |
| `02_aws_setup.yml` (bring-your-own) | Not tested | — | |
| `01_azure_teardown.yml` | Pass | 2026-06-25 | `failed=0 ok=10`; job schedule link, schedule, runbook, account, and resource group all removed end-to-end (create-from-scratch mode) |
| `02_aws_teardown.yml` | Pass | 2026-06-25 | `failed=0 ok=16 changed=10`; maintenance window, EC2, SSM doc, IAM roles, SG, subnet, route table, IGW, VPC all removed (create-from-scratch mode) |

### Job templates

| Component | Status | Last tested | Notes |
|---|---|---|---|
| Setup - Azure runbook | Pass | 2026-06-25 | Tested via WF - Demo setup |
| Setup - AWS SSM resources | Pass | 2026-06-25 | Tested via WF - Demo setup |
| Teardown - Azure runbook | Pass | 2026-06-25 | `failed=0 ok=10`; end-to-end pass as AAP job template |
| Teardown - AWS SSM resources | Pass | 2026-06-25 | `failed=0 ok=16 changed=10`; end-to-end pass as AAP job template |
| Azure - Run Runbook and collect output | Pass | 2026-06-22 | `failed=0`; runbook output confirmed end-to-end |
| Azure - Schedule Runbook | Pass | 2026-06-22 | `failed=0`; fixes applied: task order (schedule before jobSchedule), UUID as jobScheduleId, dynamic start time (+10 min) |
| AWS - Run SSM document and collect output | Pass | 2026-06-22 | `failed=0`; SSM Automation executed on EC2 target and collected outputs |
| AWS - Schedule SSM via maintenance window | Pass | 2026-06-22 | `failed=0 changed=1`; task registered in maintenance window |
| Notify - Email automation results | Not tested | — | |

### Workflows

| Component | Status | Last tested | Notes |
|---|---|---|---|
| WF - Demo setup | Pass | 2026-06-25 | `failed=0`; Azure runbook → AWS SSM resources sequenced correctly |
| WF - Demo teardown | Not tested | — | |
| WF - Azure Runbook execute and collect | Pass | 2026-06-22 | `failed=0`; workflow completed end-to-end |
| WF - Azure Runbook schedule | Pass | 2026-06-22 | `failed=0`; workflow completed end-to-end |
| WF - AWS SSM document execute and collect | Pass | 2026-06-22 | `failed=0`; workflow completed end-to-end |
| WF - AWS SSM schedule via maintenance window | Pass | 2026-06-22 | `failed=0 changed=1`; workflow completed end-to-end |

## Open issues

- **Fixed 2026-06-25**: `02_aws_setup.yml` and `02_aws_teardown.yml` — replaced deprecated `create_instance_profile`/`delete_instance_profile` options on `amazon.aws.iam_role` with explicit `amazon.aws.iam_instance_profile` tasks. Teardown now deletes the instance profile before the role (required ordering). The `assume_role_policy_document_raw` return value deprecation and residual `delete_instance_profile` warning on `state: absent` are upstream collection behavior, not suppressible at playbook level without disabling all warnings.


- **Fixed 2026-06-23**: `01_azure_teardown.yml` and `01_azure_setup.yml` lacked the Azure credential resolution pre_task present in the demo playbooks. When run as AAP job templates, the controller injects Azure credentials as environment variables (`AZURE_TENANT`, `AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_SUBSCRIPTION_ID`) rather than Ansible variables; without the fallback the token request failed with a censored fatal error. Added the same `set_fact` resolution pre_task to both setup playbooks.
- **Fixed 2026-06-23**: `01_azure_teardown.yml` did not clean up the Azure Automation schedule and job schedule link created by `azure_runbook_schedule.yml` in bring-your-own mode. Added explicit DELETE tasks for the job schedule link and schedule (with 404 handling) before the runbook deletion. In create-from-scratch mode the Automation Account deletion cascades these objects anyway.


- **Fixed 2026-06-20**: Azure Automation Account ARM body used wrong structure for API `2024-10-23` (`sku` was at top level, must be inside `properties`) and invalid SKU value (`Free` → `Basic`). Fixed in `01_azure_setup.yml`.
- **Fixed 2026-06-22**: `02_aws_setup.yml` now passes (create-from-scratch, local run). Four fixes applied: (1) `key_name` omitted when `CHANGE_ME`; (2) IAM instance profile propagation pause after role creation; (3) `assign_public_ip: true` explicitly set in create-from-scratch mode; (4) `user_data` bootstrap uses direct S3 RPM URL instead of `dnf install amazon-ssm-agent` (package not in standard RHEL repos). Outputs copied to `demo_variables.yml`.
- **Fixed 2026-06-22**: `aap_config.yml` now passes. Two CasC fixes: (1) Azure credential inputs renamed to AAP field names (`subscription_id`→`subscription`, `client_id`→`client`, `client_secret`→`secret`); (2) `workflow_templates.yml` rewritten from `workflow_nodes` dict format to `simplified_workflow_nodes` string format to avoid `KeyError: 'type'` in the `ansible.controller` module.
