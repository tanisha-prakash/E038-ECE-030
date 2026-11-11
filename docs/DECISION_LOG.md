# Decision Log

## Resolved by the official sample-data pack (docs/SAMPLE_DATA_README.md)
| ID | Question | Resolution |
|----|----------|------------|
| DL-01 | Rounding | 2 decimals, half-up (`Decimal`). Farmer share = quote − central − state, so shares always sum to the quote |
| DL-03 | Duplicate / ineligible applications and quota | Only eligible applications use quota |
| DL-05 | Events for WAITLISTED / INELIGIBLE applications | Rejected (APPLICATION_NOT_ALLOTTED) |
| DL-06 | Deposit event format | `FARMER_DEPOSIT` event in milestones.csv (no amount field) |
| DL-07 | Re-check after a failed performance check | A later PERFORMANCE_PASSED releases the held 50% |
| DL-08 | Output layout | decisions / disbursements / district_summary / errors CSV, column order per README |
| DL-09 | Failed inspection | Not an event type in the pack, so not modelled |
| DL-10 | Application ID order | Plain string order; pack IDs are zero-padded (APP-0001) |
| DL-11 | Milestone order | File order |
| DL-12 | Duplicate farmer | Earliest by (date, application_id) is evaluated, later one is DUPLICATE_FARMER |

## Our own choices (not covered by the pack) – to confirm on the thread
| ID | Question | Current choice |
|----|----------|----------------|
| DL-13 | Reason when an application has several problems | One reason: DUPLICATE_FARMER, then LAND_OUT_OF_RANGE, then GRID_PUMP_EXISTS (no sample row has two) |
| DL-14 | errors.csv reason codes | Our own: INSPECTION_BEFORE_DEPOSIT, PERFORMANCE_BEFORE_INSPECTION, APPLICATION_NOT_ALLOTTED, UNKNOWN_APPLICATION, DUPLICATE_DEPOSIT, DUPLICATE_INSPECTION, PERFORMANCE_ALREADY_RELEASED, INVALID_ROW |
| DL-15 | "0 in HP and money columns" for ineligible rows | HP `0`, money `0.00` |
| DL-16 | HP number format | `3`, `5`, `7.5` (no trailing zeros) |
| DL-17 | WAITLISTED rows | Show full HP and cost split (they are eligible) |
| DL-18 | subsidy_committed | Sum of central + state for ALLOTTED applications only |
| DL-19 | Applications naming an unknown district/vendor | Reported as a row error and skipped (none in the pack) |
| DL-20 | Where outputs are written | `output/` (or the 2nd command-line argument) |
| DL-21 | Duplicate event for same step (second deposit etc.) | Rejected, logged in errors.csv |
