"""CSV loading with row-level validation: bad rows are reported, not fatal.
Every loader returns (rows, errors); errors are (physical_line_no, message)."""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from engine import Application
from ledger import EVENT_TYPES, Event
from rules import CATEGORIES

DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y")


def parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"bad date '{text}'")


def parse_decimal(text, name, allow_zero=False):
    try:
        v = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(f"{name} '{text}' is not a number")
    if not v.is_finite() or v < 0 or (v == 0 and not allow_zero):
        raise ValueError(f"{name} '{text}' must be positive")
    return v


def _rows(path, required):
    """Yield (line_no, row). Raises ValueError for missing columns."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        rd.fieldnames = [h.strip().lower() for h in (rd.fieldnames or [])]
        missing = [c for c in required if c not in rd.fieldnames]
        if missing:
            raise ValueError(f"{path}: missing columns {missing}")
        for row in rd:
            yield rd.line_num, {k: (v or "").strip() for k, v in row.items()
                                if k is not None}


def _load(path, required, build, key=None):
    out, errors, seen = [], [], set()
    for line, r in _rows(path, required):
        try:
            if any(not r[c] for c in required):
                raise ValueError("empty field")
            r["_line"] = line
            item = build(r)
            if key:
                k = key(item)
                if k in seen:
                    raise ValueError(f"duplicate id {k}")
                seen.add(k)
            out.append(item)
        except ValueError as e:
            errors.append((line, str(e), r))
    return out, errors


def load_districts(path):
    return _load(path, ["district_id", "annual_quota"], lambda r: (
        r["district_id"].upper(),
        int(parse_decimal(r["annual_quota"], "annual_quota", True))),
        key=lambda t: t[0])


def load_vendors(path):
    return _load(path, ["vendor_id", "quote_per_hp"], lambda r: (
        r["vendor_id"].upper(), parse_decimal(r["quote_per_hp"], "quote_per_hp")),
        key=lambda t: t[0])


def _application(r):
    cat = r["category"].upper()
    if cat not in CATEGORIES:
        raise ValueError(f"category '{r['category']}' invalid")
    grid = r["existing_grid_pump"].upper()
    if grid not in ("YES", "NO"):
        raise ValueError("existing_grid_pump must be YES or NO")
    return Application(
        r["application_id"].upper(), r["farmer_id"].upper(),
        r["district_id"].upper(), parse_decimal(r["land_acres"], "land_acres"),
        cat, grid == "YES", parse_decimal(r["requested_hp"], "requested_hp"),
        r["vendor_id"].upper(), parse_date(r["application_date"]))


APP_COLS = ["application_id", "farmer_id", "district_id", "land_acres",
            "category", "existing_grid_pump", "requested_hp", "vendor_id",
            "application_date"]


def load_applications(path):
    return _load(path, APP_COLS, _application, key=lambda a: a.app_id)


def load_milestones(path):
    """Events carry their physical line number (header = line 1). Malformed
    rows come back in errors with the raw row so the event_id can be reported."""
    def build(r):
        kind = r["event_type"].upper()
        if kind not in EVENT_TYPES:
            raise ValueError(f"unknown event_type '{r['event_type']}'")
        return Event(r["event_id"].upper(), r["application_id"].upper(), kind,
                     parse_date(r["event_date"]), r["_line"])
    cols = ["event_id", "application_id", "event_type", "event_date"]
    return _load(path, cols, build, key=lambda e: e.event_id)
