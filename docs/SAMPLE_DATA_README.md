# ECE-030 – Solar Agricultural Pump Subsidy Eligibility and Disbursement Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E038.

This pack is the input for a PM-KUSUM style solar pump subsidy engine: 4 districts, 5 vendors, 180 applications (Apr–Jun 2026) and milestone events up to Oct 2026.

Pack conventions where the brief is silent: the vendor quote for a job = quote_per_hp x approved HP. If the quote is at or above benchmark, central and state shares are taken on the benchmark and the farmer pays the rest of the quote. If the quote is below benchmark, the same percentages are applied to the quote (this reduces all three shares proportionally). Amounts are rounded to 2 decimals. For one farmer_id with two applications, the earlier one (by application_date, then application_id) is evaluated and the later one is ineligible. Milestones are processed in file order; a PERFORMANCE event before INSPECTION_PASSED, an INSPECTION_PASSED before FARMER_DEPOSIT, or any event for an application that is not ALLOTTED is rejected. A PERFORMANCE_PASSED after a PERFORMANCE_FAILED releases the held second 50%.

## Files
| File | What it holds | Rows |
|---|---|---|
| districts.csv | Districts with annual pump quota | 4 |
| vendors.csv | Empanelled vendors and their price per HP | 5 |
| applications.csv | Farmer applications | 180 |
| milestones.csv | Deposit, inspection and performance-check events | 136 |
| commands.txt | Load, evaluate, milestone and summary commands | 7 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### districts.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| district_id | string | DST-nn | DST-01 … DST-04 | Primary key |
| district_name | string | - |  |  |
| annual_quota | integer | pumps | 20–40 |  |

### vendors.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| vendor_id | string | VEN-nn | VEN-01 … VEN-05 | Primary key |
| vendor_name | string | - |  |  |
| quote_per_hp | decimal | Rs per HP |  | Same rate for every pump size |

### applications.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| application_id | string | APP-nnnn | unique | Numbered in application_date order |
| farmer_id | string | FRM-nnnnn |  | One application per farmer |
| farmer_name | string | - |  |  |
| gender | string | - | M, F | Not used by any rule |
| district_id | string | DST-nn | must exist in districts.csv |  |
| land_acres | decimal | acres, 2 decimals |  | Eligible 0.50–5.00 inclusive |
| category | string | - | GENERAL, SC_ST |  |
| existing_grid_pump | string | - | YES, NO | YES = ineligible |
| requested_hp | decimal | HP | 3, 5, 7.5 | Reduced to permitted HP if higher |
| vendor_id | string | VEN-nn | must exist in vendors.csv |  |
| application_date | date | YYYY-MM-DD |  | Allotment order: date, then application_id |

### milestones.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| event_id | string | EV-nnnn | unique |  |
| application_id | string | APP-nnnn | must exist in applications.csv |  |
| event_type | string | - | FARMER_DEPOSIT, INSPECTION_PASSED, PERFORMANCE_PASSED, PERFORMANCE_FAILED | Inspection releases 50% of subsidy; performance pass releases the other 50% |
| event_date | date | YYYY-MM-DD |  |  |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_DISTRICTS | file | Load districts.csv |
| LOAD_VENDORS | file | Load vendors.csv |
| LOAD_APPLICATIONS | file | Load applications.csv |
| EVALUATE | (none) | Eligibility, HP, cost split and allotment for every application |
| LOAD_MILESTONES | file | Load milestones.csv |
| PROCESS_MILESTONES | (none) | Apply milestone events in file order and write disbursements |
| SUMMARY | (none) | District-wise allotment and disbursement summary |

reason is `OK` for eligible applications, otherwise one of LAND_OUT_OF_RANGE, GRID_PUMP_EXISTS, DUPLICATE_FARMER. For ineligible rows put 0 in the HP and money columns.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Land exactly 0.5, 1.0, 2.5 and 5.0 acres** — applications.csv line 119 (APP-0118) 0.50 acres → eligible, 3 HP; applications.csv line 164 (APP-0163) 1.00 acres → 3 HP; applications.csv line 100 (APP-0099) 2.50 acres → 5 HP; applications.csv line 24 (APP-0023) 5.00 acres → eligible, 7.5 HP. Compare applications.csv line 140 (APP-0139) 0.49 and applications.csv line 127 (APP-0126) 5.01 (both ineligible) and applications.csv line 79 (APP-0078) 1.01 acres (5 HP).
- **Two applications on the same date competing for the last quota slot** — DST-02 quota is 30. applications.csv line 144 (APP-0143) and applications.csv line 145 (APP-0144) are both eligible and both dated 2026-06-13; they compete for the last slot. The lower application ID (APP-0143) is ALLOTTED and APP-0144 is WAITLISTED.
- **Vendor quote exactly equal to benchmark** — applications.csv line 169 (APP-0168) 5 HP from VEN-01 at Rs 100000.00 per HP = Rs 500000.00, exactly the benchmark: central 150000.00, state 150000.00, farmer 200000.00.
- **SC_ST farmer with a vendor quote above benchmark** — applications.csv line 28 (APP-0027) SC_ST, 5 HP from VEN-04 at Rs 110000.00 per HP: quote 550000.00 vs benchmark 500000.00. Central 30% = 150000.00, state 40% = 200000.00, farmer 30% = 150000.00 + the full 50000.00 excess = 200000.00.
- **Performance check event arriving before the installation inspection** — milestones.csv line 39 (EV-0038) PERFORMANCE_PASSED for APP-0038 arrives before its INSPECTION_PASSED (milestones.csv line 41 (EV-0040)); reject it with an error line and release nothing.

Extra traps (realistic things your validation should catch):

- **Inspection without deposit** — milestones.csv line 5 (EV-0004) INSPECTION_PASSED for APP-0006 comes before its FARMER_DEPOSIT, so it is rejected; the later deposit and inspection for the same application are valid.
- **Failed check then re-check** — milestones.csv line 92 (EV-0091) PERFORMANCE_FAILED holds the 2nd release for APP-0052; the re-check milestones.csv line 120 (EV-0119) PERFORMANCE_PASSED then releases it (pack convention).
- **Duplicate farmer** — applications.csv line 109 (APP-0108) uses farmer FRM-64909 who already applied on applications.csv line 99 (APP-0098); the later application is ineligible (one application per farmer).
- **Existing grid pump** — applications.csv line 149 (APP-0148) declares existing_grid_pump YES, so ineligible even though land is fine.
- **SC_ST with quote below benchmark** — applications.csv line 46 (APP-0045) 7.5 HP from VEN-05 at Rs 92000.00 per HP = 690000.00 < benchmark 712500.00: every share is reduced in the same proportion (central 30%, state 40%, farmer 30% of 690000.00).
- **Event for a waitlisted application** — milestones.csv line 87 (EV-0086) is for APP-0120, which is WAITLISTED; reject it.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-08). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### decisions.csv
One row per application in application_id order. status is ALLOTTED, WAITLISTED or INELIGIBLE.

Columns in order: `application_id`, `farmer_id`, `district_id`, `status`, `reason`, `permitted_hp`, `approved_hp`, `benchmark_cost`, `vendor_quote`, `central_subsidy`, `state_subsidy`, `farmer_share`

### disbursements.csv
One row per release, in event order. stage is 1 (inspection) or 2 (performance).

Columns in order: `vendor_id`, `application_id`, `event_id`, `event_date`, `stage`, `amount`

### district_summary.csv
One row per district.

Columns in order: `district_id`, `quota`, `applications`, `ineligible`, `allotted`, `waitlisted`, `subsidy_committed`, `subsidy_released`

### errors.csv
Rejected milestone events.

Columns in order: `event_id`, `line_no`, `reason`
