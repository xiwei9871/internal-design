#!/usr/bin/env python3
"""Deterministic query interface for the A1/A2 design knowledge base."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "knowledge/design_rules"
PREC_DIR = ROOT / "knowledge/precedents"

PRIORITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
HARD_TYPES = {"HARD_PROJECT_CONSTRAINT", "TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT"}
ALIASES = {
    "projector": ["projector-media", "non-tv-centric", "projector_or_laser_tv"],
    "media": ["projector-media"],
    "balcony": ["balcony-connected"],
    "elderly": ["aging-in-place", "elderly-bedroom"],
    "aging": ["aging-in-place"],
    "wheelchair": ["step-free-route", "future_wheelchair", "aging-in-place"],
    "walker": ["aging-in-place", "clear-circulation"],
    "ensuite": ["ensuite_or_night_route", "accessible-bathroom"],
    "child": ["child-friendly", "child_activity"],
    "storage": ["storage", "storage-zoning"],
    "route": ["clear-circulation"],
    "composition": ["spatial-composition"],
}


def load() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rules = json.loads((RULE_DIR / "design_rulebook_v01.json").read_text())["rules"]
    principles = json.loads((RULE_DIR / "project_design_principles.json").read_text())["principles"]
    precedents = json.loads((PREC_DIR / "precedent_index_v01.json").read_text())["precedents"]
    patterns = json.loads((PREC_DIR / "pattern_library_v01.json").read_text())["patterns"]
    return rules + principles, patterns, precedents


def normalize_tags(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        token = value.strip().lower().replace("_", "-")
        if not token:
            continue
        expanded = ALIASES.get(token, [token])
        for item in expanded:
            if item not in out:
                out.append(item)
    return out


def object_tags(obj: dict[str, Any]) -> set[str]:
    tags = set(obj.get("tags", []))
    tags.update(obj.get("applicable_when", []))
    tags.update(obj.get("to_verify", []))
    return {str(x).lower().replace("_", "-") for x in tags}


def room_match(obj: dict[str, Any], room: str | None) -> bool:
    if not room:
        return True
    wanted = room.lower().replace("-", "_")
    fields = {str(obj.get("category", "")).lower().replace("-", "_"), str(obj.get("room", "")).lower().replace("-", "_")}
    fields.update(str(x).lower().replace("-", "_") for x in obj.get("applicable_rooms", []))
    fields.update(str(x).lower().replace("-", "_") for x in obj.get("applies_to", []))
    return wanted in fields or (wanted == "bedroom" and "elderly-bedroom" in obj_tags_normalized(obj))


def obj_tags_normalized(obj: dict[str, Any]) -> set[str]:
    return {str(x).lower().replace("_", "-") for x in obj.get("tags", [])}


def score(obj: dict[str, Any], room: str | None, tags: list[str]) -> int:
    own = object_tags(obj)
    aliases = set(tags)
    overlap = len(own.intersection(aliases))
    room_bonus = 5 if room_match(obj, room) else 0
    priority_bonus = PRIORITY_RANK.get(obj.get("priority"), 0)
    if "relevance_score" in obj:
        relevance_bonus = round(float(obj["relevance_score"]) * 10)
    elif "relevance_to_c_type" in obj:
        relevance_bonus = round(float(obj["relevance_to_c_type"]) * 10)
    else:
        relevance_bonus = 0
    return overlap * 10 + room_bonus + priority_bonus + relevance_bonus


def filter_rules(objs: list[dict[str, Any]], room: str | None, tags: list[str], rule_type: str | None, hard_only: bool, top: int) -> list[dict[str, Any]]:
    rows = []
    for obj in objs:
        if "rule_id" not in obj and "principle_id" not in obj:
            continue
        if rule_type and obj.get("rule_type") != rule_type:
            continue
        if hard_only and obj.get("rule_type") not in HARD_TYPES:
            continue
        if not room_match(obj, room):
            continue
        s = score(obj, room, tags)
        if tags and s <= (5 + PRIORITY_RANK.get(obj.get("priority"), 0)):
            continue
        row = dict(obj)
        row["query_score"] = s
        row["trace"] = {"source_id": obj.get("source_id"), "source_url": obj.get("source_url")}
        rows.append(row)
    rows.sort(key=lambda x: (-x["query_score"], -PRIORITY_RANK.get(x.get("priority"), 0), x.get("rule_id", x.get("principle_id", ""))))
    return rows[:top]


def filter_patterns(patterns: list[dict[str, Any]], room: str | None, tags: list[str], top: int) -> list[dict[str, Any]]:
    rows = []
    for obj in patterns:
        if room and obj.get("room") != room.replace("_", "-") and obj.get("room") != room:
            continue
        s = score(obj, room, tags)
        if tags and s <= 5:
            continue
        row = dict(obj)
        row["query_score"] = s
        row["trace"] = {"precedent_ids": obj.get("precedent_ids", [])}
        rows.append(row)
    rows.sort(key=lambda x: (-x["query_score"], x["pattern_id"]))
    return rows[:top]


def filter_precedents(precedents: list[dict[str, Any]], room: str | None, tags: list[str], top: int, curation_level: str | None) -> list[dict[str, Any]]:
    rows = []
    for obj in precedents:
        if curation_level and obj.get("curation_level") != curation_level:
            continue
        text = (obj.get("project_name", "") + " " + obj.get("project_type", "")).lower()
        room_bonus = 5 if room and room.replace("_", "-") in obj_tags_normalized(obj) else 0
        s = score(obj, room, tags) + room_bonus
        if tags and s <= 5:
            continue
        row = dict(obj)
        row["query_score"] = s
        row["trace"] = {"precedent_id": obj.get("precedent_id"), "source": obj.get("source"), "url": obj.get("url")}
        rows.append(row)
    rows.sort(key=lambda x: (-x["query_score"], -float(x.get("relevance_score", x.get("relevance_to_c_type", 0))), x["precedent_id"]))
    return rows[:top]


def render_text(result: dict[str, Any]) -> str:
    q = result["query"]
    lines = [f"Query room={q.get('room') or '*'} tags={', '.join(q.get('tags') or []) or '*'}", "", "Applicable Rules"]
    for x in result["rules"]:
        rid = x.get("rule_id", x.get("principle_id"))
        lines.append(f"- {rid} [{x.get('rule_type')}] score={x['query_score']}: {x.get('statement')} (source {x.get('source_id')})")
    lines += ["", "Relevant Patterns"]
    for x in result["patterns"]:
        reasons = "; ".join(f"{e['precedent_id']}:{e.get('confidence')}" for e in x.get("evidence", []))
        lines.append(f"- {x['pattern_id']} {x['name']} score={x['query_score']} evidence={reasons}")
    lines += ["", "Relevant Precedents"]
    for x in result["precedents"]:
        lines.append(f"- {x['precedent_id']} [{x.get('curation_level')}] {x['project_name']} score={x['query_score']} relevance={x.get('relevance_score')} confidence={x.get('evidence_confidence')} plan={'yes' if x.get('floor_plan_available') else 'no'} url={x['url']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query residential design rules, patterns and precedents deterministically.")
    parser.add_argument("--room", help="room or topic, e.g. living or bedroom")
    parser.add_argument("--tags", nargs="*", default=[], help="space-separated controlled tags or aliases")
    parser.add_argument("--rule-type", choices=["HARD_PROJECT_CONSTRAINT", "TECHNICAL_GUIDELINE", "BEST_PRACTICE", "PROJECT_PREFERENCE", "TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT"])
    parser.add_argument("--hard-only", action="store_true", help="only hard project constraints and local-code checks")
    parser.add_argument("--precedents", action="store_true", help="include precedents; default output includes them")
    parser.add_argument("--patterns", action="store_true", help="include patterns; default output includes them")
    parser.add_argument("--curation-level", choices=["METADATA_ONLY", "CURATED_METADATA", "VERIFIED_PRECEDENT"], help="filter precedent level")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be >= 1")
    all_rules, patterns, precedents = load()
    tags = normalize_tags(args.tags)
    explicit_sections = args.precedents or args.patterns
    result = {
        "query": {"room": args.room, "tags": tags, "rule_type": args.rule_type, "hard_only": args.hard_only, "curation_level": args.curation_level, "top": args.top},
        "rules": filter_rules(all_rules, args.room, tags, args.rule_type, args.hard_only, args.top),
        "patterns": filter_patterns(patterns, args.room, tags, args.top) if (not explicit_sections or args.patterns) else [],
        "precedents": filter_precedents(precedents, args.room, tags, args.top, args.curation_level) if (not explicit_sections or args.precedents) else [],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
