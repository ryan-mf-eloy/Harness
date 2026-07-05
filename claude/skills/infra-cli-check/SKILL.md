---
name: Infra CLI Check
description: Verifies CLI availability and the correct profile/account/project before any infrastructure-CLI action (AWS, GCP, Azure, Firebase, Supabase, Terraform, kubectl, or equivalent), classifies the action as read-only or mutating, and gates mutating actions on explicit approval. Use before running any command against a cloud provider, database platform, or infra-as-code tool.
when_to_use: Before invoking any CLI that reads or changes state in an external environment (cloud account, hosted database, Kubernetes cluster) — especially when the request names a specific environment (prod, staging, a named account/project).
argument-hint: "[optional: environment name and intended action]"
allowed-tools: Bash(which*), Bash(aws sts*), Bash(aws configure list*), Bash(gcloud config*), Bash(az account*), Bash(firebase projects:list*), Bash(firebase use*), Bash(supabase projects list*), Bash(supabase status*), Bash(terraform workspace*), Bash(kubectl config*), Bash(*/Scripts/harness/secure/*_readonly.sh*), Read, Grep, Glob
---

Run this checklist before any command that talks to an external
infrastructure CLI for $ARGUMENTS. Do not skip steps because the action
"looks read-only" — step 4 is exactly what makes that determination, don't
pre-judge it.

1. **Identify the CLI.** Determine which tool the request actually implies
   (`aws`, `gcloud`/`gsutil`, `az`, `firebase`, `supabase`, `terraform`,
   `kubectl`, or another) — don't guess a provider the request didn't name.

2. **Confirm it's installed before using it.** `which <cli>` (or the
   tool's own version flag). If it's missing, stop and say so — do not
   attempt to install it as a side effect of this check; installing tooling
   is its own explicit action requiring approval like any other change to
   the machine.

3. **Confirm/switch to the correct profile, account, or project for the
   named environment — never assume today's default context is right.**
   Run the CLI's own read-only identity/context command first, and compare
   its output against the environment the request actually named:
   - **AWS**: `aws sts get-caller-identity` (account/identity) and
     `aws configure list` (active profile). Switch with `--profile <name>`
     or `AWS_PROFILE=<name>`, never by editing credential files directly.
   - **GCP**: `gcloud config list` (active project/account). Switch with
     `gcloud config set project <id>` only after confirming the current
     value is wrong for the request — this itself is a state change to the
     local CLI config, so name it before running it.
   - **Azure**: `az account show` (active subscription). Switch with
     `az account set --subscription <id>`.
   - **Firebase**: `firebase projects:list` and `firebase use` (no args)
     to see the active alias. Switch with `firebase use <alias>`.
   - **Supabase**: `supabase projects list` (linked project) or
     `supabase status` for local dev state.
   - **Terraform**: `terraform workspace show` (current workspace) —
     verify it matches the intended environment before any `plan`/`apply`.
   - **kubectl**: `kubectl config current-context` — verify the context
     name matches the intended cluster/environment before any command,
     read or otherwise; a `kubectl get` against the wrong cluster is
     low-risk but still gives you information about (and normalizes
     casual access to) an environment you weren't asked to touch.
   If the active context doesn't match the requested environment, switch
   explicitly and re-verify — don't proceed on the assumption a switch
   command worked.

4. **Classify the action: read-only or mutating.** Read-only means it only
   ever returns information, with no state change possible as a side
   effect — `describe*`, `get*`, `list*`, `show*`, `status`, `logs`, a
   `plan` (not `apply`), a dry-run flag. Mutating means anything that
   creates, updates, deletes, or changes state — `create*`, `delete*`,
   `update*`, `put*`, `apply` (Terraform), `deploy`, `rm`, `scale`,
   `rollout restart`, a schema migration, or any command whose own
   `--help` describes it as changing something. When genuinely unsure
   which bucket a specific verb falls into, treat it as mutating — the
   cost of an unnecessary approval prompt is far lower than the cost of
   an unapproved state change.

5. **Read-only: proceed autonomously**, once steps 2–3 have confirmed CLI
   availability and correct environment targeting. Check whether an
   existing wrapper script already covers this operation first (see
   `Scripts/harness/secure/README.md` — `github_readonly.sh` is the
   reference template); if one exists, invoke it rather than the raw CLI
   verb directly. If no wrapper exists yet for this service, running the
   raw read-only CLI command directly is still fine — building a wrapper
   is worthwhile once a real, recurring need for that service exists, not
   speculatively (per "No speculative abstraction" in
   `principles/PRINCIPLES.md`); if this read is likely to recur, consider
   writing one following the existing shape (hardcoded case-statement
   allowlist, catch-all failure branch), but don't block the current task
   on building it.

6. **Mutating: stop and get explicit approval before running anything.**
   State, before proceeding:
   - **The exact action** (the literal command or API call about to run).
   - **The target**, including the environment/account/project confirmed
     in step 3 — this is the addition specific to infra CLIs: a mutating
     action's blast radius depends on *which* environment it hits, not
     only on what the command does.
   - **The blast radius** — what this affects and whether it's reversible.
   This is the same disclosure the "Non-negotiable safety rules" bullet on
   destructive actions in `principles/PRINCIPLES.md` already requires —
   this skill doesn't redefine that gate, it applies it to infra CLIs
   specifically. Once approved, run only the exact action described — do
   not broaden scope (e.g. an approved single-resource delete does not
   license a broader cleanup pass) without a fresh, separate approval.
