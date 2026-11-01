---
name: china-residential-design-code
description: Look up current Chinese residential / interior-renovation code clauses for the C-Type home from a small verified register (docs/design_rules_poc_v01/RULE_REGISTER.json). Use when reviewing ceiling height, bathroom thresholds, slip resistance, stairs, lighting or bath electrical zones. Gives clause references for the owner's design team; never declares compliance.
---

# China Residential Design Code (lookup)

Owner context: this is the owner's own home. Drawings are a design-intent draft for the design and
construction team, who confirm code compliance. Keep reviews short; flag, don't adjudicate.

## Use

1. Read `docs/design_rules_poc_v01/RULE_REGISTER.json` and `STANDARD_REGISTER.csv`.
2. Quote `document` + `clause` + `requirement_type`. Say "宜/不宜" items are advice, "应/不应" items in
   mandatory codes are requirements.
3. Existing-dwelling renovation: JGJ 367-2015 applies directly. GB 55038-2025 new-build clauses
   (e.g. 4.1.2 heights) are reference only.
4. Lighting values (GB/T 50034-2024) are recommended and need photometric data; never judge
   compliance from lumen counts.
5. Anything not in the register: say it is not verified and point to the official announcement URL.
   Do not quote numbers from memory or from third-party skills (their China data predates 2021).

## Output

One line per finding: issue → clause → advice vs requirement → who confirms (designer / contractor / owner).
