# E038-ECE-030 – Solar Agricultural Pump Subsidy Eligibility & Disbursement Engine

Team E038 (ECM B): Syeda Rushda Mehr Hussainy (1AT24UE075), Tanisha Prakash (1AT24UE076)
Python 3.10+, standard library only (pytest for tests).

## Run
```
python src/main.py data/commands.txt            # writes output/*.csv
python src/main.py data/commands.txt my_out     # custom output folder
python -m pytest -q
```
Command file (`NAME|arg`): LOAD_DISTRICTS, LOAD_VENDORS, LOAD_APPLICATIONS, EVALUATE,
LOAD_MILESTONES, PROCESS_MILESTONES, SUMMARY. CSV paths resolve next to the command file.
Outputs: `decisions.csv`, `disbursements.csv`, `district_summary.csv`, `errors.csv`.
Bad CSV rows and bad commands are reported and skipped, never fatal.

## Layout
`src/rules.py` pure rules · `src/engine.py` eligibility + allotment · `src/ledger.py` milestones + disbursement ·
`src/io_csv.py` validation · `src/report.py` output writers · `src/main.py` driver ·
`tests/` · `data/` official sample pack · `sample_output/` our output on it ·
`docs/BUSINESS_RULES.md` · `docs/DECISION_LOG.md`

## Status
**Done:** BR-01…BR-12, official file/column formats, validation, all planted scenarios (tests/test_sample_pack.py), 54 tests.
Result on sample pack: 180 applications → 125 allotted, 30 waitlisted, 25 ineligible; 12 oversize reduced; 83 releases; 3 events rejected.
**Pending:** design PDF, demo video, answers on decision-log items DL-13…DL-21, stretch goals.
