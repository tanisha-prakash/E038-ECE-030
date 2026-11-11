# Business Rule Register – E038 / ECE-030

| ID | Rule | Code | Tests |
|----|------|------|-------|
| BR-01 | Land must be 0.5–5.0 acres inclusive | `rules.check_eligibility` | `test_land_boundaries` |
| BR-02 | Farmer must have no existing grid-connected pump | `rules.check_eligibility` | `test_grid_pump_ineligible` |
| BR-03 | One application per farmer ID; earliest by (date, app ID) wins, later ones are INELIGIBLE / DUPLICATE_FARMER | `engine.decide_all` | `test_one_application_per_farmer` |
| BR-04 | Permitted HP: ≤1.0 ac → 3 HP, ≤2.5 → 5 HP, ≤5.0 → 7.5 HP | `rules.permitted_hp` | `test_permitted_hp` |
| BR-05 | Final HP = min(requested, permitted) | `rules.final_hp` | `test_oversize_request_reduced` |
| BR-06 | Benchmark = per-HP rate × HP (3 HP: 1,10,000; 5 HP: 1,00,000; 7.5 HP: 95,000) | `rules.benchmark_rate` | `test_benchmark_rates` |
| BR-07 | GENERAL: central 30 / state 30 / farmer 40. SC_ST: central 30 / state 40 / farmer 30 | `rules.cost_split` | quote-equal tests |
| BR-08 | Quote > benchmark: subsidies on benchmark, excess paid by farmer. Quote < benchmark: all shares on the quote. Equal: no change | `rules.cost_split` | above/below/equal/SC_ST tests |
| BR-09 | Eligible applications allotted in (date, app ID) order until district quota is full; rest WAITLISTED. Ineligible ones use no quota | `engine.decide_all` | tie-break, quota tests |
| BR-10 | Total subsidy = central + state; 50% after inspection, 50% after 30-day performance check | `ledger.Ledger`, `rules.release_amounts` | `test_two_stage_release` |
| BR-11 | Farmer deposit required before inspection; otherwise the inspection event is rejected | `ledger.Ledger` | `test_inspection_without_deposit_rejected`, sample pack EV-0004 |
| BR-12 | Performance check before inspection is rejected; a failed check holds the second release | `ledger.Ledger` | `test_performance_before_inspection_rejected` (EV-0038), `test_failed_check_then_recheck_releases` (APP-0052) |

## Quote vs benchmark (viva explanation)
`basis = min(quote, benchmark)`, `excess = max(0, quote - benchmark)`.
central = 30% × basis, state = 30% (SC_ST 40%) × basis, farmer = quote − central − state
(= farmer % × basis + excess). Subsidy never increases because a vendor quotes higher.
