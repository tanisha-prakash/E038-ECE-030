"""Command-file driver.

Usage: python src/main.py <commands.txt> [output_dir]      (default: output/)

Command file: one `NAME|arg|...` per line, '#' comments, processed top-down:
  LOAD_DISTRICTS|file    LOAD_VENDORS|file    LOAD_APPLICATIONS|file
  EVALUATE               LOAD_MILESTONES|file PROCESS_MILESTONES    SUMMARY
Relative CSV paths are looked up next to the command file, then the cwd.
"""
import os
import sys

import report
from engine import decide_all
from io_csv import load_applications, load_districts, load_milestones, load_vendors
from ledger import Ledger


class Session:
    def __init__(self, base_dir=".", out_dir="output"):
        self.base, self.out = base_dir, out_dir
        self.quotas, self.vendors = {}, {}
        self.apps, self.decisions = [], None
        self.events, self.event_errors, self.ledger = [], [], None

    def _path(self, name):
        p = os.path.join(self.base, name)
        return p if os.path.exists(p) else name

    @staticmethod
    def _need(cond, msg):
        if not cond:
            raise ValueError(msg)

    @staticmethod
    def _show(path, errors):
        for line, msg, _ in errors:
            print(f"  ROW ERROR {os.path.basename(path)}:{line}: {msg}")

    def run(self, cmd, args):
        fn = getattr(self, "cmd_" + cmd.lower(), None)
        if fn is None:
            raise ValueError(f"unknown command {cmd}")
        fn(*args)

    def cmd_load_districts(self, file):
        rows, errs = load_districts(self._path(file)); self._show(file, errs)
        self.quotas.update(dict(rows))
        print(f"Loaded {len(rows)} districts")

    def cmd_load_vendors(self, file):
        rows, errs = load_vendors(self._path(file)); self._show(file, errs)
        self.vendors.update(dict(rows))
        print(f"Loaded {len(rows)} vendors")

    def cmd_load_applications(self, file):
        rows, errs = load_applications(self._path(file))
        good = []
        for a in rows:                      # references must exist in the masters
            if a.district not in self.quotas:
                errs.append((0, f"{a.app_id}: unknown district {a.district}", None))
            elif a.vendor not in self.vendors:
                errs.append((0, f"{a.app_id}: unknown vendor {a.vendor}", None))
            else:
                good.append(a)
        self._show(file, errs)
        self.apps += good
        print(f"Loaded {len(good)} applications ({len(errs)} rejected rows)")

    def cmd_evaluate(self):
        self._need(self.apps, "no applications loaded")
        self.decisions = decide_all(self.apps, self.quotas, self.vendors)
        report.write_decisions(self.out, self.decisions)
        count = lambda s: sum(d.status == s for d in self.decisions)
        print(f"Evaluated {len(self.decisions)}: {count('ALLOTTED')} allotted, "
              f"{count('WAITLISTED')} waitlisted, {count('INELIGIBLE')} ineligible")

    def cmd_load_milestones(self, file):
        rows, errs = load_milestones(self._path(file)); self._show(file, errs)
        self.events += rows
        for line, msg, raw in errs:         # malformed rows still reach errors.csv
            self.event_errors.append(((raw or {}).get("event_id", "").upper(),
                                      line, "INVALID_ROW"))
        print(f"Loaded {len(rows)} events ({len(errs)} malformed rows)")

    def cmd_process_milestones(self):
        self._need(self.decisions is not None, "run EVALUATE first")
        self.ledger = Ledger(self.decisions)
        for ev in self.events:              # strictly in file order
            self.ledger.apply(ev)
        report.write_disbursements(self.out, self.ledger)
        report.write_errors(self.out, self.ledger.errors + self.event_errors)
        print(f"Processed {len(self.events)} events: {len(self.ledger.releases)} "
              f"releases, {len(self.ledger.errors) + len(self.event_errors)} rejected")

    def cmd_summary(self):
        self._need(self.decisions is not None, "run EVALUATE first")
        _, rows = report.write_summary(self.out, self.decisions, self.quotas,
                                       self.ledger)
        print("\n" + ",".join(report.SUMMARY_COLS))
        for r in rows:
            print(",".join(map(str, r)))


def run_file(path, out_dir="output"):
    s = Session(os.path.dirname(os.path.abspath(path)), out_dir)
    with open(path, encoding="utf-8-sig") as f:
        for no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            try:
                s.run(parts[0].upper(), parts[1:])
            except (ValueError, TypeError, OSError) as e:
                print(f"COMMAND ERROR line {no}: {line!r}: {e}")
    return s


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    run_file(*sys.argv[1:])
