from decimal import Decimal as D
import pytest
from rules import (check_eligibility, permitted_hp, final_hp, cost_split,
                   benchmark_rate, release_amounts)

@pytest.mark.parametrize("land,ok", [("0.49", False), ("0.5", True),
        ("1.0", True), ("2.5", True), ("5.0", True), ("5.01", False)])
def test_land_boundaries(land, ok):                    # BR-01
    assert (check_eligibility(D(land), False) == []) is ok

def test_grid_pump_ineligible():                       # BR-02
    assert check_eligibility(D("2"), True) == ["GRID_PUMP_EXISTS"]

@pytest.mark.parametrize("land,hp", [("0.5", "3"), ("1.0", "3"), ("1.01", "5"),
        ("2.5", "5"), ("2.51", "7.5"), ("5.0", "7.5")])
def test_permitted_hp(land, hp):                       # BR-04
    assert permitted_hp(D(land)) == D(hp)

def test_oversize_request_reduced():                   # BR-05
    assert final_hp(D("7.5"), D("1.0")) == D("3")
    assert final_hp(D("3"), D("5.0")) == D("3")

def test_benchmark_rates():                            # BR-06
    assert benchmark_rate(D("3")) * 3 == D("330000")
    assert benchmark_rate(D("5")) * 5 == D("500000")
    assert benchmark_rate(D("7.5")) * D("7.5") == D("712500")

def test_quote_equal_general():
    s = cost_split(D("5"), "GENERAL", D("100000"))
    assert (s.central, s.state, s.farmer, s.excess) == (
        D("150000"), D("150000"), D("200000"), D("0"))

def test_quote_equal_sc_st():
    s = cost_split(D("5"), "SC_ST", D("100000"))
    assert (s.central, s.state, s.farmer) == (D("150000"), D("200000"), D("150000"))

def test_quote_above_general():
    s = cost_split(D("5"), "GENERAL", D("110000"))
    assert s.excess == D("50000")
    assert (s.central, s.state, s.farmer) == (D("150000"), D("150000"), D("250000"))

def test_sc_st_quote_above():
    s = cost_split(D("5"), "SC_ST", D("110000"))
    assert (s.central, s.state, s.farmer) == (D("150000"), D("200000"), D("200000"))

def test_quote_below_shrinks_proportionally():
    s = cost_split(D("5"), "GENERAL", D("90000"))
    assert (s.central, s.state, s.farmer) == (D("135000"), D("135000"), D("180000"))

def test_shares_sum_to_quote():
    for q in ("87654.33", "100000", "123456.78"):
        for cat in ("GENERAL", "SC_ST"):
            s = cost_split(D("7.5"), cat, D(q))
            assert s.central + s.state + s.farmer == s.quote_total

def test_release_split_50_50():                        # BR-10
    assert release_amounts(D("100.01")) == (D("50.01"), D("50.00"))
