# Publish, merge, and release

Proceed only after reviewer `PASS` and an acceptance table with no blocking `fail` or missing
`S*` row. An allowed `skip` stays visible on the PR/MR; it does not become pass. Create or
update the PR/MR using the effective repository conventions, wait for required CI and platform
checks, and do not merge while they are failing or pending. Include the table in the PR/MR body.

Merge is the default-branch (or documented integration-branch) update. A local restart, serving
uncommitted files, or a passing test run on a dirty tree is not merge.

Use the project runbook as the sole source for environment, deployment, health verification, and
rollback. Production order is `merge → deploy/update service → health verification`. If deployment
or health verification fails, execute only the documented rollback and report the observed state.
If the project has no deployment stage, finish after merge and say so.
