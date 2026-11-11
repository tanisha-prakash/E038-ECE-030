import pytest
from io_csv import load_applications, load_districts, load_vendors, load_milestones

HDR = ("application_id,farmer_id,farmer_name,gender,district_id,land_acres,category,"
       "existing_grid_pump,requested_hp,vendor_id,application_date\n")

def write(tmp_path, text, name="f.csv"):
    p = tmp_path / name; p.write_text(text); return str(p)

def test_good_and_bad_application_rows_reported_not_fatal(tmp_path):
    p = write(tmp_path, HDR +
      "APP-1,FRM-1,x,M,DST-01,2.0,GENERAL,NO,5,VEN-01,2026-04-01\n"
      "APP-2,FRM-2,x,M,DST-01,abc,GENERAL,NO,5,VEN-01,2026-04-01\n"
      "APP-3,FRM-3,x,M,DST-01,2.0,OBC,NO,5,VEN-01,2026-04-01\n"
      "APP-4,FRM-4,x,M,DST-01,2.0,SC_ST,MAYBE,5,VEN-01,2026-04-01\n"
      "APP-5,FRM-5,x,M,DST-01,2.0,SC_ST,YES,5,VEN-01,31-31-2026\n"
      "APP-6,FRM-6,x,M,DST-01,2.0,SC_ST,YES,5,,2026-04-01\n"
      "APP-1,FRM-7,x,M,DST-01,2.0,SC_ST,YES,5,VEN-01,2026-04-01\n")
    apps, errs = load_applications(p)
    assert [a.app_id for a in apps] == ["APP-1"]
    assert [e[0] for e in errs] == [3, 4, 5, 6, 7, 8]      # physical line numbers

def test_missing_column_is_error(tmp_path):
    with pytest.raises(ValueError):
        load_applications(write(tmp_path, "application_id,farmer_id\nA,B\n"))

def test_negative_and_zero_values_rejected(tmp_path):
    _, e = load_vendors(write(tmp_path, "vendor_id,vendor_name,quote_per_hp\nV1,a,0\nV2,b,-5\nV3,c,1\n"))
    assert len(e) == 2

def test_districts_loaded(tmp_path):
    rows, e = load_districts(write(tmp_path, "district_id,district_name,annual_quota\nD1,a,20\nD1,b,5\n"))
    assert rows == [("D1", 20)] and len(e) == 1            # duplicate id rejected

def test_milestone_unknown_event_type_and_line_numbers(tmp_path):
    ev, e = load_milestones(write(tmp_path,
        "event_id,application_id,event_type,event_date\n"
        "EV-1,A,FARMER_DEPOSIT,2026-07-01\nEV-2,A,BOGUS,2026-07-01\n"))
    assert ev[0].line_no == 2 and e[0][0] == 3 and e[0][2]["event_id"] == "EV-2"
