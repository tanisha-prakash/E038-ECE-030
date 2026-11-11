"""Output writers. File names and column order follow the official README."""
import csv
import os
from collections import defaultdict
from decimal import Decimal

from engine import ALLOTTED, INELIGIBLE, WAITLISTED

DECISION_COLS = ["application_id", "farmer_id", "district_id", "status", "reason",
                 "permitted_hp", "approved_hp", "benchmark_cost", "vendor_quote",
                 "central_subsidy", "state_subsidy", "farmer_share"]
DISBURSE_COLS = ["vendor_id", "application_id", "event_id", "event_date",
                 "stage", "amount"]
SUMMARY_COLS = ["district_id", "quota", "applications", "ineligible", "allotted",
                "waitlisted", "subsidy_committed", "subsidy_released"]
ERROR_COLS = ["event_id", "line_no", "reason"]


def hp(x):
    return "0" if not x else format(x.normalize(), "f")


def money(x):
    return f"{(x or Decimal(0)):.2f}"


def _write(out_dir, name, cols, rows):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)
    return path


def decision_rows(decisions):
    for d in sorted(decisions, key=lambda d: d.app.app_id):
        s = d.split
        yield [d.app.app_id, d.app.farmer_id, d.app.district, d.status, d.reason,
               hp(d.permitted_hp), hp(d.hp), money(s and s.benchmark_total),
               money(s and s.quote_total), money(s and s.central),
               money(s and s.state), money(s and s.farmer)]


def disbursement_rows(ledger):
    for r in ledger.releases:                     # event order
        yield [r.vendor, r.app_id, r.event_id, r.on.isoformat(), r.stage,
               money(r.amount)]


def summary_rows(decisions, quotas, ledger=None):
    by = defaultdict(list)
    for d in decisions:
        by[d.app.district].append(d)
    released = defaultdict(Decimal)
    for r in (ledger.releases if ledger else []):
        released[r.district] += r.amount
    for dist in sorted(quotas):
        ds = by[dist]
        n = lambda st: sum(1 for d in ds if d.status == st)
        committed = sum((d.split.subsidy for d in ds if d.status == ALLOTTED),
                        Decimal(0))
        yield [dist, quotas[dist], len(ds), n(INELIGIBLE), n(ALLOTTED),
               n(WAITLISTED), money(committed), money(released[dist])]


def write_decisions(out, decisions):
    return _write(out, "decisions.csv", DECISION_COLS, decision_rows(decisions))


def write_disbursements(out, ledger):
    return _write(out, "disbursements.csv", DISBURSE_COLS,
                  disbursement_rows(ledger))


def write_errors(out, errors):
    return _write(out, "errors.csv", ERROR_COLS, sorted(errors, key=lambda e: e[1]))


def write_summary(out, decisions, quotas, ledger):
    rows = list(summary_rows(decisions, quotas, ledger))
    return _write(out, "district_summary.csv", SUMMARY_COLS, rows), rows
