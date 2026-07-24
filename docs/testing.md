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
| Azure-Resources-CloudNativeAutomation (source) | Not tested | — | |
| AWS-Resources-CloudNativeAutomation (source) | Not tested | — | |
| Demo-CloudNativeAutomation (parent) | Not tested | — | |

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
| Azure - Run Runbook and collect output | Partial | 2026-07-24 | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0`. Further changed 2026-07-23 (Error stream diagnostics) and 2026-07-24 (positional-to-named parameter resolution). Live run against bring-your-own Python runbook `crif-rb-patching-aks` failed (`declares 0 parameter(s)` — Python runbooks never expose declared parameters); fixed same day with `[PARAMETER N]` key resolution for Python — see Open issues. Not yet re-run |
| Azure - Schedule Runbook | Not tested | — | Logic changed for azure_auth_mode (SP/MSI token branch); default service_principal path not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0`. Further changed 2026-07-24 with the same positional-to-named parameter resolution as Azure - Run Runbook above, plus the same-day Python-runbook `[PARAMETER N]` fix (applied by analogy to the `jobSchedules` API, unverified); not yet run live — see Open issues |
| AWS - Run SSM document and collect output | Not tested | — | Logic changed 2026-07-22: aws_ssm_target_instance_id made optional (InstanceId now built via aws_ssm_all_parameters, combined with new aws_ssm_document_parameters); default instance-based path not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| AWS - Schedule SSM via maintenance window | Not tested | — | Logic changed 2026-07-22: --targets now conditional on aws_ssm_target_instance_id; new --task-invocation-parameters branch for aws_ssm_document_parameters is UNTESTED (AWS CLI shorthand syntax not yet verified against a live document). Last known-good run (pre-change): 2026-06-22, `failed=0 changed=1` |
| Notify - Email automation results | Not tested | — | Extended 2026-07-23 to include per-cloud status (`azure_runbook_status`, `aws_ssm_status`), Azure error stream details, and a dynamic SUCCESS/FAILURE subject; not yet run live — see Open issues |
| Azure - Connectivity check (dry run) | Not tested | — | New job template |
| Azure - Permissions check (dry run) | Not tested | — | New job template |
| Azure - Runbook preview (dry run) | Not tested | — | New job template. Extended 2026-07-24 to report the runbook's declared parameters (name/type/position/mandatory) and, when `azure_runbook_parameter_values` is set, preview the positional-to-name mapping without starting a job; further extended same day so Python runbooks report the `[PARAMETER N]` mapping instead of a misleading "none declared"; not yet run live — see Open issues |
| AWS - Connectivity check (dry run) | Not tested | — | New job template; logic also changed 2026-07-22 to skip the instance check when aws_ssm_target_instance_id is empty |
| AWS - Permissions check (dry run) | Not tested | — | New job template; requires iam:SimulatePrincipalPolicy on the caller's own ARN |
| AWS - SSM preview (dry run) | Not tested | — | New job template; logic also changed 2026-07-22 to skip the instance check and report aws_ssm_all_parameters when aws_ssm_target_instance_id is empty |
| Network - Connectivity path check (dry run) | Not tested | — | New job template |
| Notify - SMTP preflight check (dry run) | Not tested | — | Two bugs found and fixed while testing against a real relay: (1) the `ansible.builtin.script` `cmd` path was relative to `playbooks/demo/` instead of the artifact-root `files/` dir — fixed with an explicit `../../` prefix; (2) `smtp_auth_check.py` validated the server certificate hostname/CA strictly, while `notify_results.yml`'s actual `community.general.mail` send path never does — added a `smtp_validate_certs` flag (default `true`) so the precheck can be relaxed to match. Not yet confirmed end-to-end against the real relay after these fixes |

### Workflows

| Component | Status | Last tested | Notes |
|---|---|---|---|
| WF - Demo setup | Not tested | — | Depends on Setup - Azure runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0` |
| WF - Demo teardown | Not tested | — | Depends on Teardown - Azure runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-25, `failed=0` |
| WF - Azure Runbook execute and collect | Not tested | — | Depends on Azure - Run Runbook and collect output, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| WF - Azure Runbook schedule | Not tested | — | Depends on Azure - Schedule Runbook, whose logic changed for azure_auth_mode; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| WF - AWS SSM document execute and collect | Not tested | — | Depends on AWS - Run SSM document and collect output, whose logic changed 2026-07-22; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0` |
| WF - AWS SSM schedule via maintenance window | Not tested | — | Depends on AWS - Schedule SSM via maintenance window, whose logic changed 2026-07-22; not yet re-verified. Last known-good run (pre-change): 2026-06-22, `failed=0 changed=1` |

## Open issues

- **2026-07-24**: Found and fixed a Python-runbook gap in the positional-to-named parameter
  resolution added earlier the same day (see the entry directly below). Running
  `Azure - Run Runbook and collect output` against a real bring-your-own Python runbook
  (`crif-rb-patching-aks`) with `azure_runbook_parameter_values` set to 4 values failed at
  the "Validate positional value count matches the runbook's declared parameters" assert:
  `azure_runbook_parameter_values supplies 4 value(s), but runbook crif-rb-patching-aks
  declares 0 parameter(s)`. Root cause: Azure's ARM API never populates
  `properties.parameters` for Python runbooks (`runbookType: Python2`/`Python3`) —
  confirmed against Microsoft's own docs and a matching unresolved community report with
  the identical symptom (4 positional values, `parameters: {}`) — so the position-based
  name resolution (designed for PowerShell/Graphical runbooks) can never succeed for
  Python, regardless of how many `sys.argv` values the script actually expects. Fixed by
  adding a "Detect whether the target runbook is a Python runbook" task (keyed off
  `runbookType`) to `azure_runbook_run.yml`, `azure_runbook_schedule.yml`, and
  `azure_runbook_preview.yml`; when Python is detected, the playbooks now build literal
  `"[PARAMETER 1]"`, `"[PARAMETER 2]"`, ... keys instead of resolving real names — this is
  the exact key format used by Microsoft's own official REST sample
  (`azureautomation/runbooks` GitHub repo, `Utility/Python/sample_rest_call.py`) for
  starting a Python runbook job with positional `sys.argv` values via the raw ARM API.
  The preview playbook's report text was also updated so a Python runbook no longer shows
  the misleading "none declared" (it now explains that Azure does not expose declared
  parameter names for Python). **Verified against official Microsoft documentation and
  sample code, not yet against a second live run** — the original failing job has not
  been re-run since this fix landed. The `[PARAMETER N]` format is confirmed for the
  `jobs` API (`azure_runbook_run.yml`); its use in `azure_runbook_schedule.yml`
  (`jobSchedules` API) is applied by analogy only and explicitly flagged as unverified in
  that playbook's comments.
- **2026-07-24**: Added positional-to-named parameter resolution for Azure Automation runbook parameters. Azure's Job API always requires a name-keyed `parameters` dictionary (never a positional array); when the customer only supplies values in a fixed order without the exact parameter names, `azure_runbook_run.yml`, `azure_runbook_schedule.yml`, and `azure_runbook_preview.yml` now fetch the runbook's own definition (`properties.parameters`, which exposes each parameter's zero-based `position`), sort by position, and `zip()` the ordered `azure_runbook_parameter_values` list onto the real names — with a fatal assert if the value count does not match the declared parameter count. `azure_runbook_parameters` (explicit `{Name: Value}` dict) remains available as the alternative when the names are already known. `Azure - Runbook preview (dry run)` reports the declared parameters and previews the resolved mapping without ever starting a job. The position-sort/zip/dict logic and the summary-line Jinja formatting were unit-verified locally with mock parameter data outside of Ansible (including a whitespace/stringification bug in the first draft of the summary formatter, fixed by joining inside the same template instead of across two `set_fact` tasks), and all three playbooks pass `ansible-playbook --syntax-check`, but **no live run against a real Azure Automation Account with a parameterized runbook has confirmed this end-to-end yet**.
- **2026-07-23**: Added Error stream diagnostics to `azure_runbook_run.yml`: on a non-`Completed` job status, the playbook now lists the job's streams, fetches the text of any `Error`-type stream, and publishes it via `set_stats` (`azure_runbook_error_details`) before the fatal assert, whose `fail_msg` also includes the error text directly. `notify_results.yml` was extended to surface `azure_runbook_status`, `aws_ssm_status`, and `azure_runbook_error_details` in the notification body, with a dynamic `SUCCESS`/`FAILURE` subject line. **Not yet confirmed** against a live failed Azure runbook job or a live AWS SSM failure.
- **2026-07-22**: `Notify - SMTP preflight check (dry run)` failed with `Could not find or access 'files/smtp_auth_check.py'`. Root cause: the `ansible.builtin.script` task in `precheck_smtp.yml` referenced `files/smtp_auth_check.py`, a path Ansible resolves relative to the playbook's own directory (`playbooks/demo/`), not the artifact root where `files/` actually lives (sibling of `playbooks/`, per the standard layout). Fixed by changing `cmd` to `../../files/smtp_auth_check.py`; verified locally that the script is now found and executes. After that fix, the same job failed again against a real relay with `CERTIFICATE_VERIFY_FAILED: Hostname mismatch`. Root cause: `smtp_auth_check.py` used `ssl.create_default_context()` (strict hostname/CA verification), while `notify_results.yml`'s actual `community.general.mail` send path calls `smtp.starttls()` with no context, which per the module's source never validates hostname/CA — so the precheck was stricter than the real send and could fail on a mismatch that would not actually block the real notification. Added a `smtp_validate_certs` variable (default `true`) so operators facing a relay with an expected CN/SAN mismatch (e.g. reached through a load balancer or internal DNS alias) can relax the precheck to match the real send behavior. **Not yet confirmed** via a live re-run against the real relay.
- **2026-07-22**: Made `aws_ssm_target_instance_id` optional across `aws_ssm_preview.yml`, `aws_ssm_run_document.yml`, `aws_ssm_schedule_maintenance.yml`, `aws_precheck_connectivity.yml`, `job_templates.yml`, `groups.yml`/`hosts.yml`, and `aap_config.yml` (per-instance registration checks and CLI targets/parameters are now conditional), to support AWS SSM Automation documents that orchestrate AWS API calls directly against non-instance resources (e.g. an EKS cluster) instead of running commands on an SSM-managed instance. New `aws_ssm_document_parameters` variable (list of `"Key=Value"` strings) carries the document's real parameters in that case. All Jinja expressions were unit-verified locally with Jinja2 outside of Ansible (both the instance-based and non-instance-based branches), and the four edited playbooks pass `ansible-playbook --syntax-check`, but **no live AWS run has confirmed this end-to-end yet** — in particular the new `--task-invocation-parameters` branch in `aws_ssm_schedule_maintenance.yml` (used only when `aws_ssm_document_parameters` is set) has never been run against a real maintenance window.
- **2026-07-21**: `aap_config.yml` failed creating `Network - Connectivity path check (dry run)` with `Unable to create job_template ...: {'playbook': ['Playbook not found for project.']}`. Root cause: `infra.aap_configuration`'s `controller_projects` role only triggers a new SCM sync when `scm_url`/`scm_branch` change, so re-running `aap_config.yml` after pushing new playbook files to the same branch leaves the project's local checkout stale before `controller_job_templates` runs. An initial fix (a hand-rolled `ansible.controller.project_update` pre_task, mirroring one briefly present in `aap-demo-multicloud-snapshots`) was replaced with a cleaner native fix: `ansible.controller.project` (called by the existing `controller_projects` role on every apply) has a built-in `update_project: true` parameter — "force project to update after changes", used with `wait`/`interval`/`timeout` — so setting `update_project: true` and `wait: true` directly on the project definition in `group_vars/all/projects.yml` forces the sync with no extra task, role, or collection needed. **Not yet confirmed** via a live re-run.
- **2026-07-20**: Added four new preliminary check job templates (`Azure - Permissions check (dry run)`, `AWS - Permissions check (dry run)`, `Network - Connectivity path check (dry run)`, `Notify - SMTP preflight check (dry run)`) plus their playbooks and the `files/smtp_auth_check.py` helper. None have been run yet — the `AWS - Permissions check` template additionally requires `iam:SimulatePrincipalPolicy` on the caller's own ARN (see docs/setup.md), which is not yet confirmed present on the demo's AWS IAM user.
- **2026-07-16**: Added `azure_auth_mode` (Service Principal / Managed Identity) and `demo_manage_infrastructure` (deployment modes) support, plus four new dry-run job templates. This reset several previously-`Pass` rows to `Not tested` (see Status summary above) because the underlying playbooks changed; re-verify the default `service_principal` / `demo_manage_infrastructure: true` path end-to-end before considering this a regression risk. `msi` mode and `demo_manage_infrastructure: false` have not been tested at all yet.
- **Fixed 2026-06-25**: `02_aws_setup.yml` and `02_aws_teardown.yml` — replaced deprecated `create_instance_profile`/`delete_instance_profile` options on `amazon.aws.iam_role` with explicit `amazon.aws.iam_instance_profile` tasks. Teardown now deletes the instance profile before the role (required ordering). The `assume_role_policy_document_raw` return value deprecation and residual `delete_instance_profile` warning on `state: absent` are upstream collection behavior, not suppressible at playbook level without disabling all warnings.


- **Fixed 2026-06-23**: `01_azure_teardown.yml` and `01_azure_setup.yml` lacked the Azure credential resolution pre_task present in the demo playbooks. When run as AAP job templates, the controller injects Azure credentials as environment variables (`AZURE_TENANT`, `AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_SUBSCRIPTION_ID`) rather than Ansible variables; without the fallback the token request failed with a censored fatal error. Added the same `set_fact` resolution pre_task to both setup playbooks.
- **Fixed 2026-06-23**: `01_azure_teardown.yml` did not clean up the Azure Automation schedule and job schedule link created by `azure_runbook_schedule.yml` in bring-your-own mode. Added explicit DELETE tasks for the job schedule link and schedule (with 404 handling) before the runbook deletion. In create-from-scratch mode the Automation Account deletion cascades these objects anyway.


- **Fixed 2026-06-20**: Azure Automation Account ARM body used wrong structure for API `2024-10-23` (`sku` was at top level, must be inside `properties`) and invalid SKU value (`Free` → `Basic`). Fixed in `01_azure_setup.yml`.
- **Fixed 2026-06-22**: `02_aws_setup.yml` now passes (create-from-scratch, local run). Four fixes applied: (1) `key_name` omitted when `CHANGE_ME`; (2) IAM instance profile propagation pause after role creation; (3) `assign_public_ip: true` explicitly set in create-from-scratch mode; (4) `user_data` bootstrap uses direct S3 RPM URL instead of `dnf install amazon-ssm-agent` (package not in standard RHEL repos). Outputs copied to `demo_variables.yml`.
- **Fixed 2026-06-22**: `aap_config.yml` now passes. Two CasC fixes: (1) Azure credential inputs renamed to AAP field names (`subscription_id`→`subscription`, `client_id`→`client`, `client_secret`→`secret`); (2) `workflow_templates.yml` rewritten from `workflow_nodes` dict format to `simplified_workflow_nodes` string format to avoid `KeyError: 'type'` in the `ansible.controller` module.
