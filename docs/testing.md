# Testing log

Tracks testing progress for this demo. Update after each session. For procedural verification steps, see [verification.md](verification.md).

**Status values:** `Not tested` · `Pass` · `Partial` · `Fail` · `Blocked`

## Status summary

### Entry playbooks

| Component | Status | Last tested | Notes |
|---|---|---|---|
| CasC apply (`aap_config.yml`) | Pass | 2026-06-22 | `failed=0 changed=23`; fixes applied: Azure credential field names (`subscription`/`client`/`secret`), workflow nodes rewritten to `simplified_workflow_nodes` format |
| CasC cleanup (`aap_cleanup.yml`) | Not tested | — | |
| Smoke test (`verify.yml`) | Pass | 2026-06-22 | `failed=0`; confirms awscli, boto3, and required variables present |

### Execution environments

| Component | Status | Last tested | Notes |
|---|---|---|---|
| EE build and push | Not tested | — | |

### Inventories

| Component | Status | Last tested | Notes |
|---|---|---|---|
| Azure-Resources (source) | Not tested | — | |
| AWS-Resources (source) | Not tested | — | |
| Demo-Multicloud (parent) | Not tested | — | |

### Setup playbooks (local run)

| Component | Status | Last tested | Notes |
|---|---|---|---|
| `01_azure_setup.yml` (create-from-scratch) | Partial | 2026-06-20 | 9/9 tasks pass locally; not yet run as AAP job template |
| `01_azure_setup.yml` (bring-your-own) | Not tested | — | |
| `02_aws_setup.yml` (create-from-scratch) | Partial | 2026-06-22 | Passes locally; fixes applied: key_name CHANGE_ME omit, IAM propagation pause, assign_public_ip, user_data S3 RPM for RHEL AMIs. Bring-your-own mode and AAP job template not yet tested. |
| `02_aws_setup.yml` (bring-your-own) | Not tested | — | |
| `01_azure_teardown.yml` | Not tested | — | |
| `02_aws_teardown.yml` | Not tested | — | |

### Job templates

| Component | Status | Last tested | Notes |
|---|---|---|---|
| Setup - Azure runbook | Not tested | — | |
| Setup - AWS SSM resources | Not tested | — | |
| Teardown - Azure runbook | Not tested | — | |
| Teardown - AWS SSM resources | Not tested | — | |
| Azure - Run Runbook and collect output | Not tested | — | |
| Azure - Schedule Runbook | Not tested | — | |
| AWS - Run SSM document and collect output | Not tested | — | |
| AWS - Schedule SSM via maintenance window | Not tested | — | |
| Notify - Email automation results | Not tested | — | |

### Workflows

| Component | Status | Last tested | Notes |
|---|---|---|---|
| WF - Demo setup | Not tested | — | |
| WF - Demo teardown | Not tested | — | |
| WF - Azure Runbook execute and collect | Not tested | — | |
| WF - Azure Runbook schedule | Not tested | — | |
| WF - AWS SSM document execute and collect | Not tested | — | |
| WF - AWS SSM schedule via maintenance window | Not tested | — | |

## Open issues

- **Fixed 2026-06-20**: Azure Automation Account ARM body used wrong structure for API `2024-10-23` (`sku` was at top level, must be inside `properties`) and invalid SKU value (`Free` → `Basic`). Fixed in `01_azure_setup.yml`.
- **Fixed 2026-06-22**: `02_aws_setup.yml` now passes (create-from-scratch, local run). Four fixes applied: (1) `key_name` omitted when `CHANGE_ME`; (2) IAM instance profile propagation pause after role creation; (3) `assign_public_ip: true` explicitly set in create-from-scratch mode; (4) `user_data` bootstrap uses direct S3 RPM URL instead of `dnf install amazon-ssm-agent` (package not in standard RHEL repos). Outputs copied to `demo_variables.yml`.
- **Fixed 2026-06-22**: `aap_config.yml` now passes. Two CasC fixes: (1) Azure credential inputs renamed to AAP field names (`subscription_id`→`subscription`, `client_id`→`client`, `client_secret`→`secret`); (2) `workflow_templates.yml` rewritten from `workflow_nodes` dict format to `simplified_workflow_nodes` string format to avoid `KeyError: 'type'` in the `ansible.controller` module.
