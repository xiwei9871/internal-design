---
name: repo-artifact-boundary
description: Use when reviewing repository contents, Git status, generated files, or source-boundary policy.
---

# Repository Artifact Boundary

Classify every path as SOURCE, AUTHORITATIVE_BINARY, REFERENCE_EXTERNAL, GENERATED_ARTIFACT, or CACHE_TEMP. SOURCE includes scripts, contracts, manifests, and human decision records. Authority binaries are hash-checked and never auto-staged. Reference files are evidence, not generated source.

Exclude from ordinary source review: \`renders/**\`, 4K/8K texture payloads, \`*.blend1\`, retries, proxies, contact sheets, raw exports, logs, API responses, and Python caches. Keep them accessible on disk. Do not delete or move them. Use exact paths and shallow metadata scans; do not recursively inspect artifact trees unless requested.
