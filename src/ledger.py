"""Milestone state machine + vendor disbursement ledger (BR-10..BR-12)."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from engine import ALLOTTED
from rules import release_amounts

DEPOSIT = "FARMER_DEPOSIT"
INSPECTION = "INSPECTION_PASSED"
PERF_PASS = "PERFORMANCE_PASSED"
PERF_FAIL = "PERFORMANCE_FAILED"
EVENT_TYPES = (DEPOSIT, INSPECTION, PERF_PASS, PERF_FAIL)


@dataclass(frozen=True)
class Event:
    event_id: str
    app_id: str
    kind: str
    on: date
    line_no: int = 0


@dataclass(frozen=True)
class Release:
    vendor: str
    district: str
    app_id: str
    event_id: str
    on: date
    stage: int                      # 1 = inspection, 2 = performance
    amount: Decimal


class Ledger:
    def __init__(self, decisions: list):
        self.decisions = {d.app.app_id: d for d in decisions}
        self.state = defaultdict(lambda: dict(
            deposit=False, inspected=False, paid2=False, held=False))
        self.releases: list = []
        self.errors: list = []      # (event_id, line_no, reason)

    def apply(self, ev: Event):
        ok, code = self._apply(ev)
        if not ok:
            self.errors.append((ev.event_id, ev.line_no, code))
        return ok, code

    def _apply(self, ev: Event):
        dec = self.decisions.get(ev.app_id)
        if dec is None:
            return False, "UNKNOWN_APPLICATION"
        if dec.status != ALLOTTED:
            return False, "APPLICATION_NOT_ALLOTTED"
        st = self.state[ev.app_id]
        first, second = release_amounts(dec.split.subsidy)

        if ev.kind == DEPOSIT:
            if st["deposit"]:
                return False, "DUPLICATE_DEPOSIT"
            st["deposit"] = True
            return True, "DEPOSIT_RECORDED"

        if ev.kind == INSPECTION:
            if not st["deposit"]:                               # BR-11
                return False, "INSPECTION_BEFORE_DEPOSIT"
            if st["inspected"]:
                return False, "DUPLICATE_INSPECTION"
            st["inspected"] = True
            self._release(dec, ev, 1, first)                    # BR-10
            return True, "STAGE1_RELEASED"

        if ev.kind in (PERF_PASS, PERF_FAIL):
            if not st["inspected"]:                             # BR-12
                return False, "PERFORMANCE_BEFORE_INSPECTION"
            if st["paid2"]:
                return False, "PERFORMANCE_ALREADY_RELEASED"
            if ev.kind == PERF_FAIL:
                st["held"] = True
                return True, "STAGE2_HELD"
            st["paid2"], st["held"] = True, False               # re-check pass
            self._release(dec, ev, 2, second)
            return True, "STAGE2_RELEASED"
        return False, "UNKNOWN_EVENT_TYPE"

    def _release(self, dec, ev, stage, amount):
        self.releases.append(Release(dec.app.vendor, dec.app.district,
                                     dec.app.app_id, ev.event_id, ev.on,
                                     stage, amount))

    def held_amount(self, app_id) -> Decimal:
        st = self.state[app_id]
        if st["held"] and not st["paid2"]:
            return release_amounts(self.decisions[app_id].split.subsidy)[1]
        return Decimal(0)
