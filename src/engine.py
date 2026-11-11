"""Decision engine: eligibility -> HP -> cost split -> quota allotment."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from rules import CostSplit, check_eligibility, cost_split, permitted_hp

ALLOTTED, WAITLISTED, INELIGIBLE = "ALLOTTED", "WAITLISTED", "INELIGIBLE"


@dataclass(frozen=True)
class Application:
    app_id: str
    farmer_id: str
    district: str
    land: Decimal
    category: str
    grid_pump: bool
    requested_hp: Decimal
    vendor: str
    applied_on: date


@dataclass
class Decision:
    app: Application
    status: str
    reason: str = "OK"
    permitted_hp: Optional[Decimal] = None
    hp: Optional[Decimal] = None
    split: Optional[CostSplit] = None


def decide_all(apps, district_quota: dict, vendor_price: dict) -> list:
    """BR-01..BR-09. Processed in (date, application_id) order, which decides
    both the duplicate-farmer winner and who gets the last quota slot. Only
    eligible applications consume quota. One reason per ineligible application:
    DUPLICATE_FARMER, then LAND_OUT_OF_RANGE, then GRID_PUMP_EXISTS (DL-02)."""
    seen_farmers, used, out = set(), defaultdict(int), []
    for app in sorted(apps, key=lambda a: (a.applied_on, a.app_id)):
        if app.farmer_id in seen_farmers:                       # BR-03
            out.append(Decision(app, INELIGIBLE, "DUPLICATE_FARMER")); continue
        seen_farmers.add(app.farmer_id)
        reasons = check_eligibility(app.land, app.grid_pump)    # BR-01/02
        if reasons:
            out.append(Decision(app, INELIGIBLE, reasons[0])); continue
        permitted = permitted_hp(app.land)                      # BR-04
        hp = min(app.requested_hp, permitted)                   # BR-05
        split = cost_split(hp, app.category, vendor_price[app.vendor])
        if used[app.district] < district_quota[app.district]:   # BR-09
            used[app.district] += 1
            status = ALLOTTED
        else:
            status = WAITLISTED
        out.append(Decision(app, status, "OK", permitted, hp, split))
    return out
