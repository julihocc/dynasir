# Known Limitations

## Annual Incidence Forecasts

Annual incidence data with fractional recovery lags is supported from v0.10.0.
The older claim that annual incidence always fails during VAR fitting is no
longer current. A successful fit, however, does not guarantee a useful forecast.

Short annual series (including series with a few dozen observations) may not
contain enough information to estimate stable VAR dynamics. The median infected
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
