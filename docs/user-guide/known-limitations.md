# Known Limitations

## Annual Incidence Forecasts

Annual incidence data is supported natively. A successful fit, however, does
not guarantee a useful forecast.

Short annual series (including series with a few dozen observations) may not
contain enough information to estimate stable dynamics. The median infected
forecast can remain flat while the scenario range grows, and reproduction
numbers can be unstable. There is no universal observation-count threshold
that guarantees adequate forecast skill.

When using annual incidence data:

- Validate at the intended forecast horizon with rolling-origin evaluation and
  compare with simple baselines.
- Inspect the median and individual scenario range; `generate_result()` warns
  when the median infected forecast is flat despite historical variation.
- Treat scenario combinations as scenarios, not calibrated probability
  samples. Do not interpret their share above a threshold as an outbreak
  probability without separate calibration.
- Do not infer transmission or importation parameters from annual case counts
  alone. Use external evidence for `importation_rate`, and report sensitivity
  analyses when its value is uncertain.

See the [Annual Surveillance Data section in the user guide](../USER_GUIDE.md#annual-surveillance-data)
for an example workflow and validation recommendations.

## What the Rates Mean for Annual and Monthly Incidence

With a recovery lag of at most one period (annual 14/365, monthly 14/30),
incidence data is modelled as period cohorts. The cases of period t are the
infectious group for the step to t+1, and all of them leave `I` by then:

- `alpha_t = A_t * I_(t+1) / (I_t * S_t)` is new cases in the next period per
  case, scaled by the susceptible share. It can exceed 1 and is forecast on the
  log scale (`log_alpha`).
- `gamma_t` is the share of the next period's cases that die, and
  `beta = 1 - gamma` is derived rather than forecast.
- `calculate_R0()` equals alpha, which is close to the growth ratio
  `I_(t+1)/I_t`. With annual counts this is a ratio between successive years,
  not a per-generation reproduction number; measles generations are about two
  weeks long.
- `results["I"]` is the simulated incidence of each period, comparable with
  the input `I`.
- Beta does not enter the cohort simulation, so the 27 SIRD scenarios contain
  9 distinct results (alpha by gamma), each repeated for the three beta
  levels. Medians and ranges are not affected. `forecast_R0()` returns alpha
  in every scenario.

The rate in row t describes the step from t to t+1. `Model(stop=...)` rebuilds
the features from the data up to `stop`, so backtests do not use later
observations, and the last training date is not used for fitting.

With deaths near zero, gamma is nearly constant. Constant rates are held
fixed in the forecast and named in a warning, so a typical annual measles
model forecasts `log_alpha` alone with a univariate autoregression.

In DynaSIR 1.0.0 and earlier these rates were different: alpha was clipped to a constant,
R0 tracked `I_t/I_(t+1)` (R0 > 1 before declines), the last training rate used
the first forecast period, and scenarios coincided at the first step
(#162-#166).

## Zero-Case Periods

Rates divide by case counts, so periods with zero incident cases (common for
eliminated diseases) make some rates undefined. `DataContainer` warns, lists
the dates, and carries those rates forward from the previous period. Pass
`incidence_offset` (for example 1) to add a constant to the case counts inside
the rate formulas instead; the compartments are not changed. Report the offset
used, since it affects the estimated rates (#167).

## Scenario Ranges Widen Quickly

The scenarios combine the lower, point and upper forecast of each rate, and
the cohort simulation multiplies the infection rate from step to step. The
range between the lowest and highest scenario therefore grows roughly
geometrically with the horizon, and the upper scenarios can reach implausible
values within a few years. Report the median together with the range at each
horizon, and do not read the extremes as plausible bounds.

## Daily and Weekly Incidence Data

For a recovery lag longer than one period (daily data, lag 14; business-day
data, lag 10; weekly data, lag 2), incidence mode keeps `I` as the period
incidence and adds `I_active = C - C_lagged`, the cases of the last
recovery-lag periods. The rates divide by `I_active`, `R = C_lagged - D` and
`C = I_active + R + D`; the forecast reports `results["I"]` as incidence
(comparable with the input) and `results["I_active"]` as the stock (#178).
Weekly counts stay on the weekly index (#177). Alpha is forecast on the log
scale, including when it exceeds 1, without treating the series as a
one-period cohort (#185).

- Beta is about one over the lag (for example 1/14 per day), because each
  case stays in `I_active` for about `recovery_lag` periods.
- In the first lag periods `C_lagged` is still zero, so `R` is negative and
  the rates are extreme there. Those warm-up rows are left out of fitting
  (#184).
- With deaths reported as whole numbers, gamma is often zero and clipped.
- Unlike annual and monthly cohorts, `R` is not clipped at zero, so that
  `C = I_active + R + D` holds exactly.
