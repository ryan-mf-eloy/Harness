# Scripts/harness/secure/

Two complementary patterns live here. Neither ever stores or prints a secret
value — that principle is non-negotiable (see `AGENTS.md`).

The read-only wrapper pattern below (pattern 1) generalizes beyond
secret-adjacent services — it's the same mechanism for safe, autonomous,
read-only access to any external CLI, including infrastructure providers
(AWS, GCP, Azure, Firebase, Supabase) and infra-as-code/orchestration tools
(Terraform, kubectl). See `principles/PRINCIPLES.md`'s "Non-negotiable
safety rules" and the `infra-cli-check` skill for when a mutating action
against one of these needs explicit approval instead of running
autonomously.

## 1. Read-only wrapper per external service (primary pattern)

For any service reachable through its own already-authenticated CLI (`gh`,
`aws`, `gcloud`, etc.): a thin wrapper script with a **hardcoded allowlist**
of safe, read-only subcommands, which delegates real authentication entirely
to that CLI's own native auth (already established outside this repo, e.g.
via `gh auth login` or `aws sso login`). The wrapper never touches a
credential directly — it just restricts *what* an agent can invoke.

`github_readonly.sh` in this folder is the reference template. To add
another service, copy its shape: one `case` branch per safe read operation,
a catch-all that exits non-zero for anything else.

## 2. Keychain-backed label (secondary pattern)

For a bespoke credential with no CLI of its own (e.g. a raw API key for an
internal service) — use `get_secret.sh`, which wraps `security
find-generic-password`. Store the value once, by hand:

```bash
security add-generic-password -a "$USER" -s "<label>" -w
```

Then any script retrieves it by label, never by value:

```bash
TOKEN="$(Scripts/harness/secure/get_secret.sh <label>)"
```

`get_secret.sh` fails loudly (exit 1, clear stderr message) if the label
isn't found — it does not silently return an empty string, since a script
downstream treating an empty credential as valid is worse than a script that
stops immediately.

## The guardrail, stated plainly

A secret's value flows Keychain/native-CLI-auth → a subprocess's environment
or argument list, and stops there. It never passes through the model's
context window: the agent invokes a script by name/label and reads its
exit code and non-secret output, never the raw value.
