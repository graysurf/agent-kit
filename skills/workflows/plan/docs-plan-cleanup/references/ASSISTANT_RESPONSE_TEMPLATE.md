## Cleanup Result
- project: <repo-root-path>
- project_path_source: <PROJECT_PATH|--project-path|cwd>
- mode: <dry-run|execute>
- execution_status: <applied|skipped (dry-run)>

## Summary
total_plan_md: <number>
plan_md_to_keep: <number>
plan_md_to_clean: <number>
plan_related_md_to_clean: <number>
plan_related_md_kept_referenced_elsewhere: <number>
plan_related_md_to_rehome: <number>
plan_related_md_manual_review: <number>
non_docs_md_referencing_removed_plan: <number>

## plan_md_to_keep
- <docs/plans/... or none>

## plan_md_to_clean
- <docs/plans/... or none>

## plan_related_md_to_clean
- <docs/... or none>

## plan_related_md_kept_referenced_elsewhere
- <docs/... | referenced_by: <file[, file...]>>
- none

## plan_related_md_to_rehome
- <docs/specs/... or docs/runbooks/... or none>

## plan_related_md_manual_review
- <docs/... or none>

## non_docs_md_referencing_removed_plan
- <README.md or other .md outside docs/ or none>
