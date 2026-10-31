"""Read-only checks for a caller-declared reverification plan; never runs it."""
from __future__ import annotations

import hashlib
import json
import math
import re
import stat
from pathlib import Path

SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
KINDS = {"check", "cli", "agent", "review"}
METRICS = ("elapsed_seconds", "model_calls", "cli_calls", "atomic_reads", "upstream_requests",
           "input_tokens", "cached_input_tokens", "output_tokens")
TOKENS = set(METRICS[-3:])
OPTIONAL_METRICS = TOKENS | {"atomic_reads", "upstream_requests"}


def require(ok, field):
    if not ok:
        raise ValueError(field)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def obj(value, field):
    require(isinstance(value, dict), field)
    return value


def array(value, field):
    require(isinstance(value, list), field)
    return value


def number(value, field):
    require((type(value) is int or type(value) is float and math.isfinite(value)) and value >= 0, field)
    if field.split(".")[-1] != "elapsed_seconds":
        require(type(value) is int, field)
    return value


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    require(path.stat().st_size <= 1024 * 1024, "record exceeds 1 MiB")
    return obj(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda value: require(False, "invalid number: " + value)), "record")


def metrics(value, field, kind):
    row = obj(value, field)
    require(set(row) == set(METRICS), field + ".fields")
    out = {k: None if row[k] is None and k in OPTIONAL_METRICS else number(row[k], field + "." + k) for k in METRICS}
    require(out["model_calls"] == (1 if kind in ("review", "agent") else 0), field + ".model_calls")
    # Some hosts report all-zero LLM usage when metering is unavailable.
    if kind in ("review", "agent") and all(out[k] == 0 for k in TOKENS):
        for k in TOKENS:
            out[k] = None
    if out["input_tokens"] is not None and out["cached_input_tokens"] is not None:
        require(out["cached_input_tokens"] <= out["input_tokens"], field + ".cached_input_tokens")
    return out


def command(args):
    path = Path(args.record).expanduser().resolve()
    actions = []
    totals = {}
    checks = []
    limits = None
    planned = None
    projected = None
    def evidence(value, field, base=path.parent):
        value = obj(value, field)
        require(text(value.get("path")) and isinstance(value.get("sha256"), str)
                and DIGEST.fullmatch(value["sha256"]), field)
        f = Path(value["path"])
        if not f.is_absolute():
            f = base / f
        require(f.is_file() and digest(f) == value["sha256"], field + ".sha256")
    def total(values, field):
        if any(v is None for v in values):
            return None
        try:
            value = sum(values)
            if type(value) is float and not math.isfinite(value):
                raise OverflowError(field)
            return value
        except OverflowError:
            checks.append({"status": "fail", "field": field + ".overflow",
                           "reason": "累计值不可有限表示；保留 null，不能补零或输出 Infinity"})
            return None
    try:
        require(SHA.fullmatch(args.candidate) is not None and SHA.fullmatch(args.baseline) is not None, "input.sha")
        require(text(args.task), "input.task")
        expected = args.items.split(",")
        required_checks = args.prechecks.split(",")
        for label, values in (("items", expected), ("prechecks", required_checks)):
            require(all(text(v) for v in values) and len(set(values)) == len(values), "input." + label)
        required_agents = set(args.require_agent)
        require(required_agents <= set(expected), "input.require-agent")
        data = load(path)
        require(type(data.get("schema_version")) is int and data["schema_version"] == 1, "schema_version")
        require(data.get("task_id") == args.task, "task_id")
        require(data.get("candidate_sha") == args.candidate, "candidate_sha")
        require(data.get("baseline_sha") == args.baseline, "baseline_sha")
        history = array(data.get("history"), "history")
        measured = []
        reviews = []
        ids = set()
        for row in history:
            row = obj(row, "history.row")
            require(text(row.get("id")) and row["id"] not in ids, "history.id")
            ids.add(row["id"])
            require(isinstance(row.get("candidate_sha"), str) and SHA.fullmatch(row["candidate_sha"]), "history.candidate")
            require(row.get("kind") in KINDS, "history.kind")
            measured.append(metrics(row.get("metrics"), "history.metrics", row["kind"]))
            if row["kind"] == "review":
                require(row.get("verdict") in ("PASS", "CHANGES_REQUESTED", "BLOCKED"), "history.verdict")
                reviews.append(row)
                if row["verdict"] != "PASS":
                    require(bool(array(row.get("failure_classes"), "history.failure_classes"))
                            and all(text(v) for v in row["failure_classes"]), "history.failure_classes")
        totals = {k: total([r[k] for r in measured], "cumulative." + k) for k in METRICS}
        budget = obj(data.get("budget"), "budget")
        raw_limits = obj(budget.get("limits"), "budget.limits")
        require({"elapsed_seconds", "model_calls"} <= set(raw_limits) <= set(METRICS), "budget.limits.fields")
        limits = {k: number(v, "budget.limits." + k) for k, v in raw_limits.items()}
        kind = data.get("next_kind")
        require(kind in KINDS, "next_kind")
        planned = metrics(budget.get("planned"), "budget.planned", kind)
        require(planned["elapsed_seconds"] > 0, "budget.planned.elapsed_seconds")
        projected = {k: total([totals[k], planned[k]], "budget.projected." + k) for k in METRICS}
        for k, limit in limits.items():
            require(projected[k] is not None, "budget.unknown." + k)
            require(projected[k] <= limit, "budget.exceeded." + k)
        old_extensions = []
        old_history = []
        previous_path = None
        if args.previous:
            previous_path = Path(args.previous).expanduser().resolve()
            previous = load(previous_path)
            require(type(previous.get("schema_version")) is int and previous["schema_version"] == 1, "previous.schema_version")
            for key in ("candidate_sha", "baseline_sha"):
                require(isinstance(previous.get(key), str) and SHA.fullmatch(previous[key]), "previous." + key)
            require(previous.get("task_id") == args.task, "previous.task_id")
            old_history = array(previous.get("history"), "previous.history")
            require(history[:len(old_history)] == old_history, "history.append-only")
            old_extensions = array(previous.get("extensions", []), "previous.extensions")
            extensions = array(data.get("extensions", []), "extensions")
            require(extensions[:len(old_extensions)] == old_extensions, "extensions.append-only")
            old_limits = obj(obj(previous.get("budget"), "previous.budget").get("limits"), "previous.limits")
            if any(k not in limits or limits[k] > v for k, v in old_limits.items()):
                auth = obj(data.get("budget_authorization"), "budget_authorization")
                require(text(auth.get("actor")), "budget_authorization.actor")
                evidence(auth.get("evidence"), "budget_authorization.evidence")
        elif args.adopt_history:
            require(bool(history) and bool(reviews), "adopt-history requires existing review history")
        else:
            require(not history, "initial plan must have empty history; use --previous")
        for index, row in enumerate(history):
            if row["kind"] != "review":
                continue
            if args.adopt_history or "evidence" in row:
                base = previous_path.parent if previous_path and index < len(old_history) else path.parent
                evidence(row.get("evidence"), "history.evidence", base)
        root = Path(args.root).expanduser().resolve()
        require(root.is_dir(), "root.directory")
        rows = array(data.get("items"), "items")
        require([obj(r, "item").get("id") for r in rows] == expected, "items.expected")
        covered = set()
        for row in rows:
            key = "items." + row["id"]
            require(row.get("method") in ("deterministic", "user-path", "agent"), key + ".method")
            require(text(row.get("reason")), key + ".reason")
            deps = array(row.get("dependencies"), key + ".dependencies")
            require(bool(deps), key + ".dependencies.empty")
            names = set()
            changed = False
            for dep in deps:
                dep = obj(dep, key + ".dependency")
                name = dep.get("path")
                require(text(name) and name not in names and not Path(name).is_absolute()
                        and ".." not in Path(name).parts, key + ".dependency.path")
                names.add(name); covered.add(name)
                f = root / name
                require(f.resolve().is_relative_to(root), key + ".dependency.root")
                for k in ("before", "after"):
                    require(dep.get(k) is None or isinstance(dep[k], str) and DIGEST.fullmatch(dep[k]), key + "." + k)
                require(dep.get("before") is not None or dep.get("after") is not None, key + ".dependency.absent")
                try:
                    info = f.stat()
                except FileNotFoundError:
                    # A dangling link (including an ancestor) is an existing entry, not deletion.
                    for entry in (f, *f.parents):
                        if entry == root:
                            break
                        if entry.is_symlink():
                            entry.resolve(strict=True)
                    actual = None
                else:
                    require(stat.S_ISREG(info.st_mode), key + ".dependency.file")
                    actual = digest(f)
                require(actual == dep.get("after"), key + ".dependency.current")
                changed |= dep.get("before") != dep.get("after")
            decision = row.get("decision")
            require(decision in ("rerun", "retain"), key + ".decision")
            must_agent = row["id"] in required_agents
            require(not must_agent or row["method"] == "agent", key + ".required-agent.method")
            old = row.get("old_evidence")
            if old is not None:
                require(isinstance(obj(old, key + ".old_evidence").get("candidate_sha"), str)
                        and SHA.fullmatch(old["candidate_sha"]), key + ".old_candidate")
                evidence(old.get("evidence"), key + ".old_evidence")
            if decision == "retain":
                require(not changed and not must_agent and old is not None, key + ".retain")
            elif row["method"] == "agent":
                require(changed or must_agent or old is None, key + ".redundant-agent")
            actions.append({"id": row["id"], "method": row["method"], "decision": decision,
                            "affected": changed, "reason": row["reason"], "executed": False})
        excluded = obj(data.get("out_of_scope", {}), "out_of_scope")
        require(all(text(k) and text(v) for k, v in excluded.items()), "out_of_scope.reason")
        require(not covered.intersection(excluded), "out_of_scope.overlap")
        require(set(args.changed_path) <= covered | set(excluded), "changed_paths.uncovered")
        prechecks = array(data.get("prechecks"), "prechecks")
        require([obj(r, "precheck").get("id") for r in prechecks] == required_checks, "prechecks.expected")
        for row in prechecks:
            key = "prechecks." + row["id"]
            require(row.get("status") == "pass" and row.get("candidate_sha") == args.candidate, key + ".status/candidate")
            evidence(row.get("evidence"), key + ".evidence")
        kind = data.get("next_kind")
        require(kind in KINDS, "next_kind")
        if reviews and reviews[-1]["verdict"] != "PASS" and kind in ("agent", "review"):
            retry = obj(data.get("retry"), "retry")
            require(all(text(retry.get(k)) for k in ("root_cause", "strategy_change", "exit_condition")), "retry.strategy")
        allowance = 3
        extension_proofs = set()
        for index, ext in enumerate(array(data.get("extensions", []), "extensions")):
            ext = obj(ext, "extension")
            require(type(ext.get("after_round")) is int and ext["after_round"] == allowance
                    and ext["after_round"] <= len(reviews), "extension.after_round")
            require(type(ext.get("additional_reviews")) is int and ext["additional_reviews"] > 0, "extension.additional_reviews")
            require(text(ext.get("actor")), "extension.actor")
            base = previous_path.parent if index < len(old_extensions) else path.parent
            evidence(ext.get("evidence"), "extension.evidence", base)
            proof = ext["evidence"]["sha256"]
            require(proof not in extension_proofs, "extension.evidence.reused")
            extension_proofs.add(proof)
            allowance += ext["additional_reviews"]
        require(kind not in ("agent", "review") or len(reviews) < allowance, "review.round_limit")
        checks.append({"status": "pass", "field": "plan", "reason": "声明与可读文件核对完成；不证明语义正确或已执行"})
    except (OSError, ValueError, TypeError, RuntimeError, KeyError, OverflowError) as exc:
        checks.append({"status": "fail", "field": str(exc), "reason": "修正声明或原始依据；不得以旧证据改版本或未知计量补零"})
    ready = all(c["status"] == "pass" for c in checks)
    report = {"schema_version": 1, "status": "READY" if ready else "BLOCKED", "task_id": args.task,
              "candidate_sha": args.candidate, "actions": actions, "cumulative": totals,
              "budget": {"limits": limits, "planned": planned, "projected": projected}, "checks": checks,
              "scope": "只读复验准备检查；不执行计划、不认证影响判断/授权来源、不签产品验收或发布 PASS"}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(report["status"])
        for a in actions:
            print(f'{a["id"]}: {a["decision"]} ({a["method"]}) — {a["reason"]}')
        print("cumulative: " + json.dumps(totals, ensure_ascii=False, allow_nan=False))
        print("budget: " + json.dumps(report["budget"], ensure_ascii=False, allow_nan=False))
        for c in checks:
            print(f'{c["status"]}: {c["field"]} — {c["reason"]}')
        print(report["scope"])
    return 0 if ready else 1
