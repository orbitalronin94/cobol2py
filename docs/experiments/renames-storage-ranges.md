# 66-level RENAMES storage ranges

## Hypothesis
Resolve RENAMES as an alias for a contiguous range of existing storage, preserving byte offsets and shared mutation.

## Scope and regressions
- Rename a range of adjacent elementary items.
- Include group members and nested groups in a range.
- Read and write through the renamed range and verify shared storage.
- Reject or diagnose invalid/non-contiguous ranges consistently with GnuCOBOL.

## Acceptance
Add GnuCOBOL-backed fixtures and unit tests. Run the complete external 500-program corpus on the exact candidate SHA. Merge only if the comparable result strictly exceeds 242/500 with unchanged corpus checksum and exact stdout/return-code comparison.