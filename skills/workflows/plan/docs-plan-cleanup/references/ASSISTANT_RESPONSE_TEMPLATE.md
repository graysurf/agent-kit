
## Cleanup Result

| field | value |
| --- | --- |
| project | `REPO_ROOT_PATH` |
| project_path_source | `PROJECT_PATH / --project-path / cwd` |
| mode | `dry-run / execute` |
| execution_status | `applied / skipped (dry-run)` |

## Summary

| metric | value |
| --- | --- |
| total_plan_md | `NUMBER` |
| plan_md_to_keep | `NUMBER` |
| plan_md_to_clean | `NUMBER` |
| plan_related_md_to_clean | `NUMBER` |
| plan_related_md_kept_referenced_elsewhere | `NUMBER` |
| plan_related_md_to_rehome | `NUMBER` |
| plan_related_md_manual_review | `NUMBER` |
| non_docs_md_referencing_removed_plan | `NUMBER` |

## plan_md_to_keep

| path |
| --- |
| `docs/plans/...` |
| none |

## plan_md_to_clean

| path |
| --- |
| `docs/plans/...` |
| none |

## plan_related_md_to_clean

| path |
| --- |
| `docs/...` |
| none |

## plan_related_md_kept_referenced_elsewhere

| path | referenced_by |
| --- | --- |
| `docs/...` | `file[, file...]` |
| none | - |

## plan_related_md_to_rehome

| path |
| --- |
| `docs/specs/...` or `docs/runbooks/...` |
| none |

## plan_related_md_manual_review

| path |
| --- |
| `docs/...` |
| none |

## non_docs_md_referencing_removed_plan

| path |
| --- |
| `README.md` or other `.md` outside `docs/` |
| none |
