from datetime import date
from decimal import Decimal as D
from engine import Application, decide_all, ALLOTTED, WAITLISTED, INELIGIBLE
from ledger import Ledger, Event

def app(i, farmer, land="2.5", cat="GENERAL", grid=False, hp="5",
        vendor="V1", day=1, district="D1"):
    return Application(i, farmer, district, D(land), cat, grid, D(hp),
                       vendor, date(2026, 1, day))

QUOTAS, VENDORS = {"D1": 2}, {"V1": D("100000")}
status = lambda ds: {d.app.app_id: d.status for d in ds}

def test_same_date_tie_broken_by_app_id():             # BR-09
    ds = decide_all([app("A3", "F3"), app("A1", "F1"), app("A2", "F2")], QUOTAS, VENDORS)
    assert status(ds) == {"A1": ALLOTTED, "A2": ALLOTTED, "A3": WAITLISTED}

def test_earlier_date_beats_smaller_id():
    ds = decide_all([app("A1", "F1", day=5), app("A9", "F9", day=1),
                     app("A5", "F5", day=2)], QUOTAS, VENDORS)
    assert status(ds)["A1"] == WAITLISTED

def test_ineligible_does_not_consume_quota():
    ds = decide_all([app("A1", "F1", land="5.01"), app("A2", "F2"),
                     app("A3", "F3"), app("A4", "F4")], QUOTAS, VENDORS)
    assert status(ds) == {"A1": INELIGIBLE, "A2": ALLOTTED,
                          "A3": ALLOTTED, "A4": WAITLISTED}

def test_one_application_per_farmer():                 # BR-03
    ds = {d.app.app_id: d for d in decide_all(
        [app("A1", "F1", day=1), app("A2", "F1", day=2)], QUOTAS, VENDORS)}
    assert ds["A1"].status == ALLOTTED
    assert (ds["A2"].status, ds["A2"].reason) == (INELIGIBLE, "DUPLICATE_FARMER")

def test_ineligible_reasons_and_zero_fields():
    ds = decide_all([app("A1", "F1", land="0.49"), app("A2", "F2", grid=True)],
                    QUOTAS, VENDORS)
    assert [d.reason for d in ds] == ["LAND_OUT_OF_RANGE", "GRID_PUMP_EXISTS"]
    assert all(d.split is None for d in ds)

def _ledger(cat="GENERAL"):
    return Ledger(decide_all([app("A1", "F1", cat=cat)], QUOTAS, VENDORS))

def ev(kind, n=1, day=10, app_id="A1"):
    return Event(f"EV{n}", app_id, kind, date(2026, 2, day), n + 1)

def test_inspection_without_deposit_rejected():        # BR-11
    l = _ledger()
    assert l.apply(ev("INSPECTION_PASSED")) == (False, "INSPECTION_BEFORE_DEPOSIT")
    assert l.releases == [] and l.errors == [("EV1", 2, "INSPECTION_BEFORE_DEPOSIT")]

def test_deposit_then_inspection_after_rejection_is_valid():
    l = _ledger()
    l.apply(ev("INSPECTION_PASSED", 1)); l.apply(ev("FARMER_DEPOSIT", 2))
    assert l.apply(ev("INSPECTION_PASSED", 3))[0] and len(l.releases) == 1

def test_performance_before_inspection_rejected():     # BR-12
    l = _ledger(); l.apply(ev("FARMER_DEPOSIT", 1))
    assert l.apply(ev("PERFORMANCE_PASSED", 2)) == (False, "PERFORMANCE_BEFORE_INSPECTION")
    assert l.releases == []

def test_two_stage_release():                          # BR-10
    l = _ledger()                       # 5HP @100000: subsidy 300000
    l.apply(ev("FARMER_DEPOSIT", 1)); l.apply(ev("INSPECTION_PASSED", 2))
    assert [(r.stage, r.amount) for r in l.releases] == [(1, D("150000.00"))]
    l.apply(ev("PERFORMANCE_PASSED", 3))
    assert [(r.stage, r.amount) for r in l.releases][1] == (2, D("150000.00"))

def test_failed_check_holds_then_recheck_releases():
    l = _ledger()
    for n, k in enumerate(["FARMER_DEPOSIT", "INSPECTION_PASSED", "PERFORMANCE_FAILED"], 1):
        l.apply(ev(k, n))
    assert len(l.releases) == 1 and l.held_amount("A1") == D("150000.00")
    assert l.apply(ev("PERFORMANCE_PASSED", 4)) == (True, "STAGE2_RELEASED")
    assert len(l.releases) == 2 and l.held_amount("A1") == 0

def test_event_for_waitlisted_application_rejected():
    ds = decide_all([app("A1", "F1"), app("A2", "F2"), app("A3", "F3")], QUOTAS, VENDORS)
    assert Ledger(ds).apply(ev("FARMER_DEPOSIT", 1, app_id="A3")) == (
        False, "APPLICATION_NOT_ALLOTTED")

def test_unknown_application_rejected():
    assert _ledger().apply(ev("FARMER_DEPOSIT", 1, app_id="NOPE")) == (
        False, "UNKNOWN_APPLICATION")
