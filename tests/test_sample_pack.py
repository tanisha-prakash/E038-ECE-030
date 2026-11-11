"""End-to-end: runs the official sample pack and checks every planted scenario
from docs/SAMPLE_DATA_README.md."""
import csv, os
import pytest
from main import run_file

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = str(tmp_path_factory.mktemp("out"))
    run_file(os.path.join(DATA, "commands.txt"), d)
    read = lambda n: list(csv.DictReader(open(os.path.join(d, n))))
    return dict(
        dec={r["application_id"]: r for r in read("decisions.csv")},
        dis=read("disbursements.csv"), err={r["event_id"]: r for r in read("errors.csv")},
        summ={r["district_id"]: r for r in read("district_summary.csv")})

@pytest.mark.parametrize("app,hp", [("APP-0118", "3"), ("APP-0163", "3"),
        ("APP-0099", "5"), ("APP-0023", "7.5"), ("APP-0078", "5")])
def test_land_boundary_scenarios(out, app, hp):
    assert out["dec"][app]["reason"] == "OK" and out["dec"][app]["permitted_hp"] == hp

@pytest.mark.parametrize("app", ["APP-0139", "APP-0126"])
def test_land_just_outside(out, app):
    r = out["dec"][app]
    assert (r["status"], r["reason"], r["approved_hp"], r["central_subsidy"]) == (
        "INELIGIBLE", "LAND_OUT_OF_RANGE", "0", "0.00")

def test_same_date_last_quota_slot(out):
    assert out["dec"]["APP-0143"]["status"] == "ALLOTTED"
    assert out["dec"]["APP-0144"]["status"] == "WAITLISTED"

def split(out, app):
    r = out["dec"][app]
    return tuple(r[k] for k in ("central_subsidy", "state_subsidy", "farmer_share"))

def test_quote_equal_to_benchmark(out):
    assert split(out, "APP-0168") == ("150000.00", "150000.00", "200000.00")

def test_sc_st_quote_above_benchmark(out):
    assert out["dec"]["APP-0027"]["vendor_quote"] == "550000.00"
    assert split(out, "APP-0027") == ("150000.00", "200000.00", "200000.00")

def test_sc_st_quote_below_benchmark(out):
    assert out["dec"]["APP-0045"]["vendor_quote"] == "690000.00"
    assert split(out, "APP-0045") == ("207000.00", "276000.00", "207000.00")

def test_duplicate_farmer_and_grid_pump(out):
    assert out["dec"]["APP-0108"]["reason"] == "DUPLICATE_FARMER"
    assert out["dec"]["APP-0148"]["reason"] == "GRID_PUMP_EXISTS"

def test_milestone_rejections(out):
    assert out["err"]["EV-0038"]["line_no"] == "39"       # perf before inspection
    assert out["err"]["EV-0038"]["reason"] == "PERFORMANCE_BEFORE_INSPECTION"
    assert out["err"]["EV-0004"]["line_no"] == "5"        # inspection w/o deposit
    assert out["err"]["EV-0086"]["reason"] == "APPLICATION_NOT_ALLOTTED"

def test_failed_check_then_recheck(out):
    rel = [r for r in out["dis"] if r["application_id"] == "APP-0052"]
    assert [r["stage"] for r in rel] == ["1", "2"] and rel[1]["event_id"] == "EV-0119"
    assert "EV-0091" not in {r["event_id"] for r in out["dis"]}   # the failure itself

def test_internal_consistency(out):
    d = out["dec"]
    assert len(d) == 180
    for r in d.values():
        if r["status"] != "INELIGIBLE":
            assert (float(r["central_subsidy"]) + float(r["state_subsidy"])
                    + float(r["farmer_share"])) == pytest.approx(float(r["vendor_quote"]))
    for s in out["summ"].values():
        assert int(s["ineligible"]) + int(s["allotted"]) + int(s["waitlisted"]) == int(s["applications"])
        assert int(s["allotted"]) <= int(s["quota"])
        assert float(s["subsidy_released"]) <= float(s["subsidy_committed"])
