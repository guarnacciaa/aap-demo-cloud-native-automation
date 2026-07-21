# Testing log

Tracks testing progress for this demo. Update after each session. For procedural verification steps, see [verification.md](verification.md).

**Status values:** `Not tested` · `Pass` · `Partial` · `Fail` · `Blocked`

## Status summary

### Entry playbooks

| Component | Status | Last tested | Notes |
|---|---|---|---|
| CasC apply (`aap_config.yml`) | Not tested | — | Logic changed for azure_auth_mode/demo_manage_infrastructure (new mode-aware asserts, `_infra` template merge); default service_principal path not yet re-verified. Also added `update_project: true` to `projects.yml` 2026-07-21 (see Open issues) after job template creation failed with "Playbook not found for project." |
| CasC cleanup (`aap_cleanup.yml`) | Pass | 2026-06-25 | `failed=0 changed=7`; all AAP objects removed cleanly |
| Smoke test (`verify.yml`) | Not tested | — | Logic changed for azure_auth_mode/demo_manage_infrastructure (new mode-aware asserts); default service_principal path not yet re-verified |

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
| `01_azure_setup.yml` (create-from-scratch) | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified |
| `01_azure_setup.yml` (bring-your-own) | Not tested | — | |
| `02_aws_setup.yml` (create-from-scratch) | Pass | 2026-06-25 | Tested as AAP job template via WF - Demo setup |
| `02_aws_setup.yml` (bring-your-own) | Not tested | — | |
| `01_azure_teardown.yml` | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0 ok=10` |
| `02_aws_teardown.yml` | Pass | 2026-06-25 | `failed=0 ok=16 changed=10`; maintenance window, EC2, SSM doc, IAM roles, SG, subnet, route table, IGW, VPC all removed (create-from-scratch mode) |

### Job templates

| Component | Status | Last tested | Notes |
|---|---|---|---|
| Setup - Azure runbook | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified |
| Setup - AWS SSM resources | Pass | 2026-06-25 | Tested via WF - Demo setup |
| Teardown - Azure runbook | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0 ok=10` |
| Teardown - AWS SSM resources | Pass | 2026-06-25 | `failed=0 ok=16 changed=10`; end-to-end pass as AAP job template |
| Azure - Run Runbook and collect output | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| Azure - Schedule Runbook | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| AWS - Run SSM document and collect output | Pass | 2026-06-22 | `failed=0`; SSM Automation executed on EC2 target and collected outputs |
| AWS - Schedule SSM via maintenance window | Pass | 2026-06-22 | `failed=0 changed=1`; task registered in maintenance window |
| Notify - Email automation results | Not tested | — | |
| Azure - Connectivity check (dry run) | Not tested | — | New job template |
| Azure - Permissions check (dry run) | Not tested | — | New job template |
| Azure - Runbook preview (dry run) | Not tested | — | New job template |
| AWS - Connectivity check (dry run) | Not tested | — | New job template |
| AWS - Permissions check (dry run) | Not tested | — | New job template; requires iam:SimulatePrincipalPolicy on the caller's own ARN |
| AWS - SSM preview (dry run) | Not tested | — | New job template |
| Network - Connectivity path check (dry run) | Not tested | — | New job template |
| Notify - SMTP preflight check (dry run) | Not tested | — | New job template |

### Workflows

| Component | Status | Last tested | Notes |
|---|---|---|---|
| WF - Demo setup | Not tested | — | Depends on Setup - Azure runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0` |
| WF - Demo teardown | Not tested | — | Depends on Teardown - Azure runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0` |
| WF - Azure Runbook execute and collect | Not tested | — | Depends on Azure - Run Runbook and collect output, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| WF - Azure Runbook schedule | Not tested | — | Depends on Azure - Schedule Runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| WF - AWS SSM document execute and collect | Pass | 2026-06-22 | `failed=0`; workflow completed end-to-end |
| WF - AWS SSM schedule via maintenance window | Pass | 2026-06-22 | `failed=0 changed=1`; workflow completed end-to-end |

## Open issues

- **2026-07-21**: `aap_config.yml` failed creating `Network - Connectivity path check (dry run)` with `Unable to create job_template ...: {'playbook': ['Playbook not found for project.']}`. Root cause: `infra.aap_configuration`'s `controller_projects` role only triggers a new SCM sync when `scm_url`/`scm_branch` change, so re-running `aap_config.yml` after pushing new playbook files to the same branch leaves the project's local checkout stale before `controller_job_templates` runs. An initial fix (a hand-rolled `ansible.controller.project_update` pre_task, mirroring one briefly present in `aap-demo-multicloud-snapshots`) was replaced with a cleaner native fix: `ansible.controller.project` (called by the existing `controller_projects` role on every apply) has a built-in `update_project: true` parameter — "force project to update after changes", used with `wait`/`interval`/`timeout` — so setting `update_project: true` and `wait: true` directly on the project definition in `group_vars/all/projects.yml` forces the sync with no extra task, role, or collection needed. **Not yet confirmed** via a live re-run.
- **2026-07-20**: Added four new preliminary check job templates (`Azure - Permissions check (dry run)`, `AWS - Permissions check (dry run)`, `Network - Connectivity path check (dry run)`, `Notify - SMTP preflight check (dry run)`) plus their playbooks and the `files/smtp_auth_check.py` helper. None have been run yet — the `AWS - Permissions check` template additionally requires `iam:SimulatePrincipalPolicy` on the caller's own ARN (see docs/setup.md), which is not yet confirmed present on the demo's AWS IAM user.
- **2026-07-16**: Added `azure_auth_mode` (Service Principal / Managed Identity) and `demo_manage_infrastructure` (deployment modes) support, plus four new dry-run job templates. This reset several previously-`Pass` rows to `Not tested` (see Status summary above) because the underlying playbooks changed; re-verify the default `service_principal` / `demo_manage_infrastructure: true` path end-to-end before considering this a regression risk. `msi` mode and `demo_manage_infrastructure: false` have not been tested at all yet.
- **Fixed 2026-06-25**: `02_aws_setup.yml` and `02_aws_teardown.yml` — replaced deprecated `create_instance_profile`/`delete_instance_profile` options on `amazon.aws.iam_role` with explicit `amazon.aws.iam_instance_profile` tasks. Teardown now deletes the instance profile before the role (required ordering). The `assume_role_policy_document_raw` return value deprecation and residual `delete_instance_profile` warning on `state: absent` are upstream collection behavior, not suppressible at playbook level without disabling all warnings.


- **Fixed 2026-06-23**: `01_azure_teardown.yml` and `01_azure_setup.yml` lacked the Azure credential resolution pre_task present in the demo playbooks. When run as AAP job templates, the controller injects Azure credentials as environment variables (`AZURE_TENANT`, `AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_SUBSCRIPTION_ID`) rather than Ansible variables; without the fallback the token request failed with a censored fatal error. Added the same `set_fact` resolution pre_task to both setup playbooks.
- **Fixed 2026-06-23**: `01_azure_teardown.yml` did not clean up the Azure Automation schedule and job schedule link created by `azure_runbook_schedule.yml` in bring-your-own mode. Added explicit DELETE tasks for the job schedule link and schedule (with 404 handling) before the runbook deletion. In create-from-scratch mode the Automation Account deletion cascades these objects anyway.


- **Fixed 2026-06-20**: Azure Automation Account ARM body used wrong structure for API `2024-10-23` (`sku` was at top level, must be inside `properties`) and invalid SKU value (`Free` → `Basic`). Fixed in `01_azure_setup.yml`.
- **Fixed 2026-06-22**: `02_aws_setup.yml` now passes (create-from-scratch, local run). Four fixes applied: (1) `key_name` omitted when `CHANGE_ME`; (2) IAM instance profile propagation pause after role creation; (3) `assign_public_ip: true` explicitly set in create-from-scratch mode; (4) `user_data` bootstrap uses direct S3 RPM URL instead of `dnf install amazon-ssm-agent` (package not in standard RHEL repos). Outputs copied to `demo_variables.yml`.
- **Fixed 2026-06-22**: `aap_config.yml` now passes. Two CasC fixes: (1) Azure credential inputs renamed to AAP field names (`subscription_id`→`subscription`, `client_id`→`client`, `client_secret`→`secret`); (2) `workflow_templates.yml` rewritten from `workflow_nodes` dict format to `simplified_workflow_nodes` string format to avoid `KeyError: 'type'` in the `ansible.controller` module.
