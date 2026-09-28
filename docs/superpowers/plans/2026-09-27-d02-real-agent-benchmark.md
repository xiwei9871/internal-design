# D0.2 Real Agent Residential CAD Skill Benchmark

> Approved execution design from the owner review. Stop at HUMAN_REVIEW.

**Goal:** Re-run the public-zone comparison with four independent Codex sessions whose furniture decisions are recorded as CAD commands rather than hard-coded runner coordinates.

**Architecture:** Prepare a common clean CAD base and method adapters. Each arm session owns a private session directory and must use the shared CAD tool to write INSERT/MOVE/ROTATE/DELETE commands, render its saved DXF, inspect its own render, and revise only after the first geometry/render evidence. A packaging step creates blind outputs without exposing arm mapping.

**Hard constraints:** The D0.2 CAD tool contains no arm layout coordinates or ARM_SPECS. D0.1 furniture coordinates and trial DXFs are prohibited inputs. Formal V02/V03/canonical CAD are never modified.
