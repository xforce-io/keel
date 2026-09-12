# Reviewer adapters

Use the host's dedicated Reviewer path; do not run the review in the implementation context.

Before launching it, run `local-skill find code-review`, select the exact `code-review` match, and
read the returned `skill_file` completely. Pass that contract to the Reviewer. If the exact local
Skill cannot be resolved, return `BLOCKED`; do not substitute a remembered or host-specific format.

Resolve and freeze the newest exact review target before delegation. When the read-only Reviewer
cannot run Git commands, the parent must supply the complete diff, relevant file contents, test
results, and acceptance/design references in the review request. Missing evidence is `BLOCKED`, not
permission to guess or to ask the Reviewer to edit or fetch it.

- **Codex:** invoke native code review, which uses the configured `review_model`.
- **Pi:** invoke the `reviewer` subagent; its user override selects the complementary model.
- **Grok:** spawn `subagent_type: reviewer`; never substitute `general-purpose`, which inherits the
  implementation model.
- **OMP:** invoke the user `reviewer` agent definition.

Capture the effective model from runtime metadata when the host exposes it; do not rely only on the
model's self-report.
