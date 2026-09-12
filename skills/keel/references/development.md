# Development and review

Implement only the accepted scope. Maintain traceability from acceptance criteria to tests. Run
focused checks during development and the project-required suite before review. Prefer the
project's existing instruments (named pytest nodes, suite script, in-process HTTP client). Do not
add an evidence file, screenshot factory, or extra E2E layer the project does not already use.

Before independent review, write an acceptance table for this SHA covering every Issue story
`S1…Sn` and any previously passing story this change can touch:

`S1: pass|fail|skip  <command>  <one-line result or skip reason>`

Implementer-run tests are the candidate gate, not acceptance. Fill the table from a fresh run on
the frozen candidate (clean tree). `skip` is not pass: it needs the environmental limit the
design already allows. Missing rows, `fail`, or a skip used as done block review and “complete”.
When continuing a task, read the latest table on the Issue or PR/MR before planning the next
increment; do not reconstruct status from the code alone.

Resolve the public `code-review` contract and freeze the review evidence as specified by the
Reviewer adapter, then delegate the newest exact diff to the host's independent read-only Reviewer.
The implementation agent owns all fixes. After each fix, rerun affected tests, refresh the
acceptance table, and request a fresh review of the new diff. Stop after three rounds if the
result is not `PASS`. Code review does not replace the table.

In **dev** mode, stop once implementation, the acceptance table, and independent review pass. Do
not create or merge a PR/MR or deploy unless separately requested or end-to-end mode is active.

In **end-to-end** mode, passing tests is not a terminal state. Continue to independent review,
then [release](release.md). A coding-goal plan that stops at tests is not a substitute.
