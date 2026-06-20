# Testing log

Tracks testing progress for this demo. Update after each session. For procedural verification steps, see [verification.md](verification.md).

**Status values:** `Not tested` · `Pass` · `Partial` · `Fail` · `Blocked`

## Status summary

### Entry playbooks

| Component | Status | Last tested | Notes |
|---|---|---|---|
| CasC apply (`aap_config.yml`) | Blocked | 2026-06-20 | Pre-task validation works; blocked on `02_aws_setup.yml` outputs not yet copied to `demo_variables.yml` |
| CasC cleanup (`aap_cleanup.yml`) | Not tested | — | |
| Smoke test (`verify.yml`) | Not tested | — | |

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
| `02_aws_setup.yml` | Not tested | — | |
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
- **Pending**: `02_aws_setup.yml` not yet run — `aws_ssm_target_instance_id`, `aws_ssm_maintenance_window_id`, `aws_account_id`, and `aws_ssm_service_role_arn` still `CHANGE_ME` in `demo_variables.yml`. Unblocks `aap_config.yml`.
