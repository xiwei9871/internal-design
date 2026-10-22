# Whole-house rendering study V1 — production checkpoint

Use the user-designated source `projects/c_type_home/design/console_bath_mirrors_review/CONSOLE400_THREE_BATH_MIRRORS.blend`, revision `console400-three-bath-mirrors-review-1`. Frozen R4/B0 and this design source remain unchanged.

The approved camera registry is `renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json`. The production output is under `renders/whole_house_final_study_v1/production_batch_v1/`, excluded from source review. Do not replace approved cameras with the earlier numeric suggestion register.

Executable standard: `projects/c_type_home/render_config/WHOLE_HOUSE_RENDER_STANDARD_V1.json`. Cycles256 samples,1920×1080,OIDN,AgX Medium High Contrast, +0.5EV,5200K white balance; lighting adjusted uniformly after a living preview, no geometry edits. Same per-view camera for all3levels.

Production scripts: prepare_approved_batch_v1.py; render_approved_batch_v1.py; run_approved_image2_v1.py; update_render_review_gallery_v1.py; run_overnight_render_v1.py. Image2 invokes the user-installed persistent launcher, never a custom provider client. No credentials in this repository.

Checkpoint:75/75Faithful;50/75Designer;50/75Creative,175/225generated. Last5rooms each lack10AIimages. Image2 circuit stopped on401/503; two transient earlier failures recovered once, one new503retry stillfailed, authfailures were not retried. Do not relaunch an existing queue. `--resume-unattempted` only schedules previously unattempted jobs; failed jobs require individual review and remaining retry allowance after provider authorization is resolved.

AI native output1672×941 despite1920×1080requested; retained at native size. All15matrix files and3hero sheets were opened, but5matrices and2hero sheets remain incomplete. Counts do not imply visualPASS. Flagged: living creative03invented curved ceiling; bedroom bed-runner misread as rigid board; study creativeadded chair visibility. FlagJSON and room notes live in production00_MANIFEST. No style selected or promoted.

Task remainsPARTIAL_PROVIDER_BLOCKED. Final225reconciliation, remainingAIgeneration/QA and human design selection remain outstanding. Generated binaries/textures/images are not committed. Preserve all previous scenes and outputs. No automatic merge.
