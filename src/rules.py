"""Pure business rules (no file I/O). Every rule is tagged with its BR id."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
MIN_LAND, MAX_LAND = D("0.5"), D("5.0")            # BR-01
# (max land in acres, permitted HP, benchmark rate per HP)   BR-04, BR-06
SLABS = (
    (D("1.0"), D("3"), D("110000")),
    (D("2.5"), D("5"), D("100000")),
    (D("5.0"), D("7.5"), D("95000")),
)
CENTRAL_PCT = D("0.30")                              # BR-07
STATE_PCT = {"GENERAL": D("0.30"), "SC_ST": D("0.40")}   # BR-07 (SC_ST +10%)
CATEGORIES = tuple(STATE_PCT)


def money(x: Decimal) -> Decimal:
    """Round to paise, half-up (decision log DL-01)."""
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def check_eligibility(land: Decimal, has_grid_pump: bool) -> list:
    """BR-01, BR-02. Returns a list of reason codes; empty list = eligible."""
    reasons = []
    if not (MIN_LAND <= land <= MAX_LAND):
        reasons.append("LAND_OUT_OF_RANGE")
    if has_grid_pump:
        reasons.append("GRID_PUMP_EXISTS")
    return reasons


def permitted_hp(land: Decimal) -> Decimal:
    """BR-04: <=1.0 ac -> 3 HP, <=2.5 -> 5 HP, <=5.0 -> 7.5 HP."""
    if not (MIN_LAND <= land <= MAX_LAND):
        raise ValueError(f"land {land} outside eligible range")
    for max_land, hp, _ in SLABS:
        if land <= max_land:
            return hp


def final_hp(requested: Decimal, land: Decimal) -> Decimal:
    """BR-05: requested HP is capped at the permitted HP."""
    return min(requested, permitted_hp(land))


def benchmark_rate(hp: Decimal) -> Decimal:
    """BR-06: rate of the smallest slab that covers this HP (DL-04)."""
    for _, slab_hp, rate in SLABS:
        if hp <= slab_hp:
            return rate
    raise ValueError(f"no benchmark slab for {hp} HP")


@dataclass(frozen=True)
class CostSplit:
    benchmark_total: Decimal
    quote_total: Decimal
    excess: Decimal
    central: Decimal
    state: Decimal
    farmer: Decimal

    @property
    def subsidy(self) -> Decimal:
        return self.central + self.state


def cost_split(hp: Decimal, category: str, quote_per_hp: Decimal) -> CostSplit:
    """BR-07, BR-08.

    basis  = min(quote, benchmark)   -> subsidies are a % of the basis
    excess = max(0, quote-benchmark) -> paid fully by the farmer
    farmer = quote - central - state (so the three shares always add up
             exactly to the quote, whatever the rounding).
    """
    benchmark = money(benchmark_rate(hp) * hp)
    quote = money(quote_per_hp * hp)
    basis = min(benchmark, quote)
    central = money(basis * CENTRAL_PCT)
    state = money(basis * STATE_PCT[category])
    return CostSplit(benchmark, quote, max(D(0), quote - benchmark),
                     central, state, quote - central - state)


def release_amounts(subsidy: Decimal):
    """BR-10: 50% after inspection, remainder after performance check."""
    first = money(subsidy / 2)
    return first, subsidy - first
