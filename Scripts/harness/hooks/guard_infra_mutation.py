#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash/Shell, plus a direct MCP-tool-name regex):
deny commands and MCP tool calls that mutate cloud/infrastructure state,
regardless of what the model decides. Read-only infra operations (list,
describe, get, show, plan, status) are unaffected — only mutation verbs are
matched.

Broader than block_destructive_bash.py on purpose: that script is scoped to
git/filesystem patterns; this one covers cloud CLIs, IaC/orchestration
tools, Kubernetes, container registries, PaaS/edge deploy platforms, and
infra-mutating MCP tools (Cloudflare/Supabase/Vercel). Complements the
advisory-only `infra-cli-check` skill rather than replacing it — a hook can
mechanically block a known pattern, but it can't verify the correct
profile/account is active or collect human approval for a classified
mutation, which is exactly what that skill still does. Same "defense in
depth, not a single point of failure" reasoning already documented for
block_destructive_bash.py vs. permissions.deny.

Deny mechanism: exit code 2 with the reason on stderr — the one convention
confirmed identical across Claude Code, Cursor, and Codex CLI (see
Scripts/harness/hooks/README.md's cross-provider section).

Heuristic, not a real shell parser: matches known mutation-verb patterns.
A deliberately obfuscated command can escape; a string literal that merely
mentions a mutating verb as prose can false-positive (see hooks/README.md's
"Known limitation" section). Fails open on any parse error.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

CLOUD_TOOLS = {"aws", "gcloud", "az", "oci", "ibmcloud", "aliyun", "gsutil", "bq", "doctl"}

MUTATION_PREFIXES = {
    "create", "delete", "update", "deploy", "set", "add", "remove", "put", "insert", "drop",
    "grant", "revoke", "rotate", "destroy", "run", "invoke", "publish", "push", "sync", "rsync",
    "cp", "mv", "rm", "modify", "terminate", "reboot", "associate", "disassociate", "register",
    "deregister", "tag", "untag", "send", "cancel", "execute", "kill", "mb", "rb", "write", "edit",
    "new", "launch", "provision", "apply", "scale", "start", "stop", "restart", "enable", "disable",
    "import", "patch", "replace", "reset", "attach", "detach", "assume", "migrate", "upload", "copy",
    "load", "make", "mk", "abort", "purge", "empty", "truncate", "wipe", "setmeta",
}
ALLOW_SUBCOMMANDS = {"config", "configure", "help", "version"}

EXPLICIT_MUTATION_RE = re.compile(
    r"\b("
    r"terraform\s+(apply|destroy|import|taint|state\s+(rm|mv|push|replace-provider)|workspace\s+(new|delete))"
    r"|terragrunt\s+(apply|destroy|import|run-all\s+(apply|destroy))"
    r"|pulumi\s+(up|destroy|import|stack\s+rm)"
    r"|cdk\s+(deploy|destroy|import|bootstrap)"
    r"|(serverless|sls)\s+(deploy|remove)"
    r"|sam\s+(deploy|sync|delete)"
    r"|helm\s+(install|upgrade|uninstall|delete|rollback)"
    r"|helmfile\s+(apply|sync|destroy)"
    r"|ansible-playbook\b"
    r"|kubectl\s+(apply|create|delete|edit|patch|replace|scale|rollout|drain|cordon|uncordon|taint|label|annotate|set|exec|cp|run|expose|autoscale|attach)"
    r"|eksctl\s+(create|delete|upgrade|scale)"
    r"|kops\s+(create|delete|update|rolling-update)"
    r"|(docker|podman|nerdctl)\s+push"
    r"|wrangler\s+(deploy|publish|delete|rollback)"
    r"|vercel\s+(deploy|promote|rollback|rm|remove|--prod)"
    r"|(fly|flyctl)\s+(deploy|launch|destroy|scale|secrets)"
    r"|netlify\s+deploy"
    r"|heroku\s+(create|destroy|run|config:set|ps:scale|releases:rollback|pg:)"
    r"|supabase\s+(db\s+push|functions\s+deploy|migration\s+up|link|branches\s+create)"
    r"|amplify\s+(push|publish)"
    r"|eb\s+(deploy|create|terminate)"
    r")\b",
    re.IGNORECASE,
)

MCP_INFRA_MUTATION_RE = re.compile(
    r"^mcp__.*?__("
    r"d1_database_(create|delete)|kv_namespace_(create|delete|update)|r2_bucket_(create|delete)"
    r"|hyperdrive_config_(create|edit|delete)"
    r"|apply_migration|execute_sql|deploy_edge_function|create_branch|delete_branch|merge_branch"
    r"|reset_branch|rebase_branch|create_project|pause_project|restore_project"
    r"|deploy_to_vercel"
    r")$",
    re.IGNORECASE,
)

REASON = (
    "Blocked by harness guardrail: matched an infrastructure-mutation pattern "
    "(cloud CLI, IaC/orchestration tool, Kubernetes, or an infra-mutating MCP "
    "call). Deploys and infra mutations should go through an approved "
    "pipeline, not directly from an agent session — see the infra-cli-check "
    "skill for the read-only-vs-mutating classification and approval flow. "
    "If this is genuinely a misclassified read-only operation, rewrite it as "
    "an explicit read/list/describe/get/show/plan/status command."
)


def command_has_cloud_cli_mutation(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    i = 0
    n = len(tokens)
    while i < n:
        if tokens[i].split("/")[-1].lower() in CLOUD_TOOLS:
            subcommand: list[str] = []
            j = i + 1
            while j < n:
                token = tokens[j]
                if token in {"|", "||", "&&", ";", "&"} or token[:1] in {"|", "&", ";", ">", "<"}:
                    break
                if not token.startswith("-"):
                    subcommand.append(token.lower())
                j += 1
            if subcommand and subcommand[0] not in ALLOW_SUBCOMMANDS:
                for word in subcommand:
                    segment = word.split("-", 1)[0].split(":", 1)[0]
                    if segment in MUTATION_PREFIXES:
                        return True
            i = j
        else:
            i += 1
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    tool_name = payload.get("tool_name", "")
    blocked = False

    if tool_name.startswith("mcp__"):
        blocked = bool(MCP_INFRA_MUTATION_RE.match(tool_name))
    else:
        tool_input = payload.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if isinstance(command, str):
            blocked = bool(EXPLICIT_MUTATION_RE.search(command) or command_has_cloud_cli_mutation(command))

    if not blocked:
        return 0

    print(REASON, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
