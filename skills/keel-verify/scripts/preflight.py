"""Read-only preflight of caller-declared acceptance evidence. Never writes or approves."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
ASSOC = ("object", "version", "export_sha256", "decision_id", "revision")
ASSOC_CLASS = {
    "object": "stale-association",
    "version": "stale-association",
    "export_sha256": "stale-association",
    "decision_id": "decision-mismatch",
    "revision": "decision-mismatch",
}


def require(ok, field):
    if not ok:
        raise ValueError(field)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def obj(value, field):
    require(isinstance(value, dict), field)
    return value


def names(value, field):
    require(isinstance(value, list), field)
    require(all(text(item) for item in value) and len(set(value)) == len(value), field)
    return value


def digest(path):
    hashed = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hashed.update(block)
    return hashed.hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate:" + key)
            result[key] = value
        return result

    require(path.is_file() and path.stat().st_size <= 1024 * 1024, "record")
    return obj(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda value: require(False, "number:" + value)), "record")


def check(acceptance_id, field, branch, kind, status, reason):
    return {
        "acceptance_id": acceptance_id,
        "field": field,
        "branch": branch,
        "class": kind,
        "status": status,
        "reason": reason,
    }


def association(row, evidence_path, evidence_sha, actual_sha):
    item = {"acceptance_id": row.get("id", ""), "task_id": row.get("task_id", ""),
            "branches": list(row.get("branches") or []), "entries": list(row.get("entries") or []),
            "evidence_path": evidence_path, "evidence_sha256": evidence_sha, "actual_sha256": actual_sha}
    for field in ASSOC:
        item[field] = row.get(field)
    return item


def binding(candidate, required_path, record_path, associations):
    payload = {"candidate_sha": candidate, "required_sha256": file_sha(required_path),
               "record_sha256": file_sha(record_path), "associations": associations}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def command(args):
    checks = []
    associations = []
    current_binding = ""
    issue = args.issue
    candidate = args.candidate
    try:
        require(type(issue) is int and issue > 0, "issue")
        require(isinstance(candidate, str) and SHA.fullmatch(candidate) is not None, "candidate")
        record_path = Path(args.record).expanduser().resolve()
        required_path = Path(args.required).expanduser().resolve()
        required = load(required_path)
        record = load(record_path)
        for label, data in (("required", required), ("record", record)):
            require(type(data.get("schema_version")) is int and data["schema_version"] == 1, label + ".schema_version")
            require(data.get("issue") == issue, label + ".issue")
            require(data.get("candidate_sha") == candidate, label + ".candidate_sha")
        task_id = required.get("task_id")
        require(text(task_id), "required.task_id")
        required_items = names_of(required.get("items"), "required.items", allow_empty=False)
        evidence_rows = {}
        for row in names_of(record.get("items"), "record.items", allow_empty=True):
            require(row["id"] not in evidence_rows, "record.items.id")
            evidence_rows[row["id"]] = row
        base = record_path.parent
        for item in required_items:
            aid = item["id"]
            row = evidence_rows.get(aid)
            if row is None:
                checks.append(check(aid, "id", "", "missing-id", "fail", "缺必需验收编号 " + aid))
                continue
            failed = False
            have_branches = set(names(row.get("branches"), "record.branches"))
            for branch in item["branches"]:
                if branch not in have_branches:
                    failed = True
                    checks.append(check(aid, "branches", branch, "missing-branch", "fail",
                                        f"验收编号 {aid} 缺必需分支 {branch}"))
            have_entries = set(names(row.get("entries"), "record.entries"))
            for entry in item["entries"]:
                if entry not in have_entries:
                    failed = True
                    checks.append(check(aid, "entries", "", "missing-entry", "fail",
                                        f"验收编号 {aid} 缺要求的入口 {entry}"))
            require(text(row.get("task_id")), "record.task_id")
            if row["task_id"] != task_id:
                failed = True
                checks.append(check(aid, "task_id", "", "cross-task", "fail",
                                    f"验收编号 {aid} 关联字段 task_id 与当前任务不一致"))
            for field in ASSOC:
                if field not in item:
                    continue
                expected = item[field]
                require(text(expected), "required." + field)
                if field == "export_sha256":
                    require(DIGEST.fullmatch(expected) is not None, "required.export_sha256")
                if row.get(field) != expected:
                    failed = True
                    checks.append(check(aid, field, "", ASSOC_CLASS[field], "fail",
                                        f"验收编号 {aid} 关联字段 {field} 与要求不一致"))
            evidence = obj(row.get("evidence"), "record.evidence")
            require(text(evidence.get("path")) and isinstance(evidence.get("sha256"), str)
                    and DIGEST.fullmatch(evidence["sha256"]) is not None, "record.evidence")
            target = Path(evidence["path"])
            if not target.is_absolute():
                target = base / target
            actual = digest(target) if target.is_file() else ""
            if actual == "" or actual != evidence["sha256"]:
                failed = True
                checks.append(check(aid, "evidence.sha256", "", "evidence-file", "fail",
                                    f"验收编号 {aid} 关联字段 evidence.sha256 的文件缺失或摘要不符"))
            associations.append(association(row, evidence["path"], evidence["sha256"], actual))
            if not failed:
                checks.append(check(aid, "id", "", "consistent", "pass",
                                    f"验收编号 {aid} 的编号、分支、入口和声明关联一致"))
        current_binding = binding(candidate, required_path, record_path, associations)
        if args.previous:
            previous_path = Path(args.previous).expanduser().resolve()
            previous = load(previous_path)
            previous_id = required_items[0]["id"]
            if previous.get("status") != "PASS":
                checks.append(check(previous_id, "previous", "", "previous", "pass",
                                    "旧结果不是通过，本次按当前输入重新判定"))
            elif previous.get("candidate_sha") != candidate or previous.get("binding") != current_binding:
                changed = diff_previous(previous, candidate, associations)
                checks.append(check(changed[0] or previous_id, changed[1], changed[2], "stale-pass", "fail",
                                    f"验收编号 {changed[0] or previous_id} 旧通过结果不可沿用；关联字段 {changed[1]} 已变化"))
            else:
                checks.append(check(previous_id, "binding", "", "previous", "pass",
                                    "旧通过结果仍对应当前候选和关联证据"))
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        checks = [check("", "input", "", "input", "fail", "输入无法核对：" + str(exc))]
        associations = []
        current_binding = ""
    passed = bool(checks) and all(item["status"] == "pass" for item in checks)
    report = {
        "schema_version": 1,
        "status": "PASS" if passed else "BLOCKED",
        "ready_for_review": passed,
        "product_acceptance": False,
        "issue": issue,
        "candidate_sha": candidate,
        "binding": current_binding,
        "associations": associations,
        "checks": checks,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["status"])
        print("本次可以交接" if passed else "本次不能交接")
        if passed:
            print("结构通过，只核对编号、分支、入口和声明关联")
        for item in checks:
            print(f'[{item["status"]}] acceptance_id={item["acceptance_id"]} field={item["field"]} '
                  f'branch={item["branch"]} class={item["class"]} — {item["reason"]}')
    return 0 if passed else 1


def names_of(value, field, allow_empty):
    require(isinstance(value, list) and (allow_empty or value), field)
    rows = []
    seen = set()
    for row in value:
        row = obj(row, field)
        require(text(row.get("id")) and row["id"] not in seen, field + ".id")
        seen.add(row["id"])
        if field.startswith("required"):
            row["branches"] = names(row.get("branches"), field + ".branches")
            row["entries"] = names(row.get("entries"), field + ".entries")
        rows.append(row)
    return rows


def diff_previous(previous, candidate, associations):
    if previous.get("candidate_sha") != candidate:
        aid = associations[0]["acceptance_id"] if associations else ""
        return aid, "candidate_sha", ""
    old_rows = {row.get("acceptance_id"): row for row in previous.get("associations") or []
                if isinstance(row, dict)}
    new_rows = {row["acceptance_id"]: row for row in associations}
    if set(old_rows) != set(new_rows):
        changed = sorted(set(old_rows) ^ set(new_rows))
        return (changed[0] if changed else ""), "id", ""
    fields = ("task_id", "branches", "entries", "object", "version", "export_sha256",
              "decision_id", "revision", "evidence_path", "evidence_sha256", "actual_sha256")
    for row in associations:
        old = old_rows[row["acceptance_id"]]
        for field in fields:
            if old.get(field) == row.get(field):
                continue
            branch = ""
            if field == "branches":
                delta = sorted(set(old.get("branches") or []) ^ set(row.get("branches") or []))
                branch = delta[0] if delta else ""
            named = "evidence.sha256" if field in ("evidence_sha256", "actual_sha256") else field
            return row["acceptance_id"], named, branch
    return (associations[0]["acceptance_id"] if associations else ""), "required", ""
