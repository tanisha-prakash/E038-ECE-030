# E038-ECE-030 – Solar Agricultural Pump Subsidy Eligibility & Disbursement Engine

Team E038 (Section ECM B): Syeda Rushda Mehr Hussainy (1AT24UE075), Tanisha Prakash (1AT24UE076)
Language: Python 3.10+, standard library only (pytest for tests).

**Demo video (5 min):** [[DEMO VIDEO LINK](https://drive.google.com/file/d/1_mUfp5jYsFMzgoEwOfe511MBfgPp6ddB/view?usp=drive_link)]
**Design document:** [docs/Design_Document.pdf](docs/Design_Document.pdf) · 
**Decision log:** [docs/DECISION_LOG.md](docs/DECISION_LOG.md) · 
**Rule register:** [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md)

## What it does
A command-file driven engine for a PM-KUSUM style solar pump scheme. It checks farmer eligibility, fixes the permitted pump size from land holding,
splits the cost between central subsidy, state subsidy and farmer share, allots applications against a district quota (rest WAITLISTED),
and releases vendor payments in two stages (50% after inspection, 50% after the 30-day performance check).

## Run
```
python src/main.py data/commands.txt            # writes output/*.csv
python src/main.py data/commands.txt my_out     # optional: custom output folder
python -m pytest -q                             # 54 tests
```
Windows PowerShell: use `src\main.py` and `data\commands.txt`. CSV paths in the command file resolve next to the command file.

## Command file (`NAME|arg`, `#` for comments, processed top to bottom)
`LOAD_DISTRICTS|file` · `LOAD_VENDORS|file` · `LOAD_APPLICATIONS|file` · `EVALUATE` · `LOAD_MILESTONES|file` · `PROCESS_MILESTONES` · `SUMMARY`

## Outputs (column order as specified in docs/SAMPLE_DATA_README.md)
`decisions.csv` · `disbursements.csv` · `district_summary.csv` · `errors.csv`

## Repository layout
| Path | Contents |
|---|---|
| `src/rules.py` | Pure business rules: eligibility, permitted HP, benchmark, cost split, rounding |
| `src/engine.py` | Duplicate-farmer check, quota allotment, decisions |
| `src/ledger.py` | Milestone state machine and vendor disbursements |
| `src/io_csv.py` | CSV loading with row-level validation |
| `src/report.py` | Output file writers |
| `src/main.py` | Command-file driver |
| `tests/` | 54 tests, including an end-to-end run of the sample pack (`test_sample_pack.py`) |
| `data/` | Official sample data pack |
| `sample_output/` | Our output on the sample pack |
| `docs/` | Design document (PDF), rule register, decision log, demo script, sample-pack README |

## Business rules
BR-01 to BR-12 are listed with their code location and tests in `docs/BUSINESS_RULES.md`.
Quote versus benchmark: subsidies are computed on `min(quote, benchmark)`; any excess over the benchmark is paid entirely by the farmer; a quote below the benchmark reduces all three shares proportionally.

## Results on the sample pack
180 applications → 125 allotted, 30 waitlisted, 25 ineligible; 12 oversize requests reduced; 136 milestone events → 83 releases, 3 rejected (EV-0004, EV-0038, EV-0086).
No expected-output file was supplied; correctness is shown by the test suite.

## Status
- **Done:** BR-01 to BR-12, official input and output formats, input validation, all edge cases from the brief and the planted sample scenarios, 54 tests, design document, decision log, demo video.
- **Not implemented:** optional stretch goals (grid-pump solarisation with net-metering; vendor performance score).
- **Open assumptions:** where the sample README is silent (error reason codes, zero and HP formatting, reason priority, waitlisted rows, `subsidy_committed`, output location) we made our own choices, listed as DL-13 to DL-21 in `docs/DECISION_LOG.md`. They were sent to 10 SECONDS for confirmation and no reply had been received at submission.
