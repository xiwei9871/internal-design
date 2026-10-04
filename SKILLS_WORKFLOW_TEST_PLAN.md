# Skills Workflow Test Plan

These are routing tests, not design changes. Each should trigger the named skill and remain in HUMAN_REVIEW until its stated gate is approved.

## design-task-git-workflow

Should trigger:

1. “Create a task branch, stage only the source files, commit, push, and open a PR.”
2. “Review this substantial design change as a task-scoped Git diff.”
3. “Prepare the governance PR and stop before merge.”

Should not trigger:

1. “Explain what a Git commit is.”
2. “Show the current branch name.”

## ground-truth-guard

Should trigger:

1. “Modify the current R4 model while preserving its frozen hash.”
2. “Compare this candidate against the approved kitchen manifest.”
3. “Check whether generated geometry changed a registered door or window.”

Should not trigger:

1. “Rewrite this unrelated Markdown paragraph.”
2. “Sort a list of filenames without design files.”

## blender-preview-first

Should trigger:

1. “Study two Blender layout options before final materials.”
2. “Create a low-resolution Workbench preview for this room.”
3. “Render final Cycles images after human approval.”

Should not trigger:

1. “Explain a Blender Python syntax error without opening a scene.”
2. “Rename a non-Blender text file.”

## repo-artifact-boundary

Should trigger:

1. “Classify remaining untracked files into source and generated artifacts.”
2. “Explain why renders and 4K textures are polluting review.”
3. “Audit whether retries, proxies, logs, and blend1 files are ignored.”

Should not trigger:

1. “Review one explicitly named source Markdown file.”
2. “Calculate the SHA256 of one named authority file.”
