# Migration Guide: v0.5.x to v0.6.x API

**Target Audience**: Users upgrading from dynasir v0.5.x to v0.6.x

**Summary**: Version 0.6.0 introduced a simplified, more intuitive API for the Model class. The old API method names remain available with deprecation warnings to ensure backward compatibility.

---

## What Changed?

### API Simplification

The Model class methods have been renamed to use simpler, more intuitive names:

| Old Method (v0.5.x) | New Method (v0.6.x) | Status |
|---------------------|---------------------|--------|
| `create_logit_ratios_model()` | `create_model()` | Old deprecated in v0.6.0 |
| `fit_logit_ratios_model()` | `fit_model()` | Old deprecated in v0.6.0 |
| `forecast_logit_ratios()` | `forecast()` | Old deprecated in v0.6.0 |

### Why the Change?

1. **Simpler names**: Users don't need to think about the internal "logit ratios" implementation detail
2. **Better API design**: Method names reflect what they do, not how they do it
3. **Consistency**: Aligns with common patterns in scientific Python libraries
4. **Future-proof**: Allows internal implementation changes without API changes

---

## Deprecation Timeline

| Version | Status | Action Required |
|---------|--------|-----------------|
| **v0.5.x** | Old API only | No changes needed |
| **v0.6.x** | Both APIs work, old shows warnings | Update recommended |
| **v0.7.x** | Both APIs work, old shows warnings | Update recommended |
| **v0.8.0** | Old API removed | **Must update** |

**Recommendation**: Update your code now to avoid breaking changes in v0.8.0.

---

## Quick Migration

### Basic Workflow

**Before (v0.5.x):**
```python
from dynasir import DataContainer, Model, process_data_from_owid

# Load data
raw_data = process_data_from_owid(iso_code="OWID_WRL")
container = DataContainer(raw_data, window=7)

# Create and fit model
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_logit_ratios_model()
model.fit_logit_ratios_model(max_lag=10, ic="aic")

# Forecast
model.forecast_logit_ratios(steps=30)
model.run_simulations()
model.generate_result()
```

**After (v0.6.x):**
```python
from dynasir import DataContainer, Model, process_data_from_owid

# Load data
raw_data = process_data_from_owid(iso_code="OWID_WRL")
container = DataContainer(raw_data, window=7)

# Create and fit model
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_model()  # Simplified!
model.fit_model(max_lag=10, ic="aic")  # Simplified!

# Forecast
model.forecast(steps=30)  # Simplified!
model.run_simulations()
model.generate_result()
```

**Changes:**
- Line 9: `create_logit_ratios_model()` → `create_model()`
- Line 10: `fit_logit_ratios_model()` → `fit_model()`
- Line 13: `forecast_logit_ratios()` → `forecast()`

---

## Detailed Examples

### Example 1: Global COVID-19 Forecasting

**Before (v0.5.x):**
```python
# Setup
from dynasir import DataContainer, Model, process_data_from_owid

# Load global COVID-19 data
data = process_data_from_owid(iso_code="OWID_WRL")
container = DataContainer(data, window=7)

# Create model for 2020 data
model = Model(
    container,
    start="2020-03-01",
    stop="2020-12-31"
)

# Fit VAR model
model.create_logit_ratios_model()
model.fit_logit_ratios_model(max_lag=10, ic="aic")

# Generate 30-day forecast
model.forecast_logit_ratios(steps=30)
model.run_simulations()
model.generate_result()

# Calculate R0
R0_historical = model.calculate_R0()
R0_forecast = model.forecast_R0()
```

**After (v0.6.x):**
```python
# Setup
from dynasir import DataContainer, Model, process_data_from_owid

# Load global COVID-19 data
data = process_data_from_owid(iso_code="OWID_WRL")
container = DataContainer(data, window=7)

# Create model for 2020 data
model = Model(
    container,
    start="2020-03-01",
    stop="2020-12-31"
)

# Fit VAR model
model.create_model()  # Changed
model.fit_model(max_lag=10, ic="aic")  # Changed

# Generate 30-day forecast
model.forecast(steps=30)  # Changed
model.run_simulations()
model.generate_result()

# Calculate R0
R0_historical = model.calculate_R0()
R0_forecast = model.forecast_R0()
```

### Example 2: Model Evaluation

**Before (v0.5.x):**
```python
# Training period
model = Model(container, start="2020-03-01", stop="2020-09-30")
model.create_logit_ratios_model()
model.fit_logit_ratios_model()
model.forecast_logit_ratios(steps=30)
model.run_simulations()
model.generate_result()

# Evaluation
testing_data = container.data.loc[model.forecasting_interval]
evaluation = model.evaluate_forecast(testing_data)
```

**After (v0.6.x):**
```python
# Training period
model = Model(container, start="2020-03-01", stop="2020-09-30")
model.create_model()  # Changed
model.fit_model()  # Changed
model.forecast(steps=30)  # Changed
model.run_simulations()
model.generate_result()

# Evaluation
testing_data = container.data.loc[model.forecasting_interval]
evaluation = model.evaluate_forecast(testing_data)
```

### Example 3: Visualization

**Before (v0.5.x):**
```python
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_logit_ratios_model()
model.fit_logit_ratios_model(max_lag=10)
model.forecast_logit_ratios(steps=30)
model.run_simulations()
model.generate_result()

# Visualize results
testing_data = container.data.loc[model.forecasting_interval]
model.visualize_results("C", testing_data, log_response=True)
model.visualize_results("D", testing_data, log_response=True)
```

**After (v0.6.x):**
```python
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_model()  # Changed
model.fit_model(max_lag=10)  # Changed
model.forecast(steps=30)  # Changed
model.run_simulations()
model.generate_result()

# Visualize results (unchanged)
testing_data = container.data.loc[model.forecasting_interval]
model.visualize_results("C", testing_data, log_response=True)
model.visualize_results("D", testing_data, log_response=True)
```

---

## What Stayed the Same?

### No Changes Required For:

1. **Data loading and preprocessing**
   ```python
   from dynasir import process_data_from_owid, DataContainer
   data = process_data_from_owid(iso_code="OWID_WRL")
   container = DataContainer(data, window=7)
   ```

2. **Model initialization**
   ```python
   model = Model(container, start="2020-03-01", stop="2020-12-31")
   ```

3. **Simulation and results**
   ```python
   model.run_simulations()
   model.generate_result()
   ```

4. **R0 calculation** (new feature in v0.6.0)
   ```python
   R0 = model.calculate_R0()
   R0_forecast = model.forecast_R0()
   ```

5. **Visualization and evaluation**
   ```python
   model.visualize_results(compartment_code, testing_data)
   model.evaluate_forecast(testing_data)
   ```

6. **Constants and utilities**
   ```python
   from dynasir import COMPARTMENTS, RATIOS, FORECASTING_LEVELS
   from dynasir import prepare_for_logit_function
   ```

---

## Automated Migration

### Using Find and Replace

You can use find and replace in your editor or IDE:

1. **Find:** `create_logit_ratios_model()`
   **Replace:** `create_model()`

2. **Find:** `fit_logit_ratios_model(`
   **Replace:** `fit_model(`

3. **Find:** `forecast_logit_ratios(`
   **Replace:** `forecast(`

### Using sed (Linux/Mac)

```bash
# Backup your files first!
cp my_script.py my_script.py.backup

# Perform replacements
sed -i 's/create_logit_ratios_model()/create_model()/g' my_script.py
sed -i 's/fit_logit_ratios_model(/fit_model(/g' my_script.py
sed -i 's/forecast_logit_ratios(/forecast(/g' my_script.py
```

### Using Python Script

```python
import re
from pathlib import Path

def migrate_file(filepath):
    """Migrate a Python file to new API."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Perform replacements
    content = content.replace('create_logit_ratios_model()', 'create_model()')
    content = re.sub(r'fit_logit_ratios_model\(', 'fit_model(', content)
    content = re.sub(r'forecast_logit_ratios\(', 'forecast(', content)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Migrated: {filepath}")

# Example usage
# migrate_file('my_analysis.py')
```

---

## Handling Deprecation Warnings

### What You'll See

When using old API methods in v0.6.x:

```python
model.create_logit_ratios_model()
```

**Output:**
```
DeprecationWarning: create_logit_ratios_model() is deprecated and will be
removed in v0.8.0. Use create_model() instead.
```

### Suppressing Warnings (Not Recommended)

If you need to temporarily suppress warnings:

```python
import warnings

# Suppress deprecation warnings (not recommended for production)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    model.create_logit_ratios_model()
    model.fit_logit_ratios_model()
    model.forecast_logit_ratios(steps=30)
```

**Better approach:** Update your code to use the new API instead of suppressing warnings.

---

## Jupyter Notebook Migration

### Updating Existing Notebooks

For `.ipynb` files:

1. **Manual approach:**
   - Open notebook
   - Run "Find and Replace" in Jupyter
   - Replace old method names with new ones
   - Re-run all cells to verify

2. **Programmatic approach:**
   ```python
   import json
   from pathlib import Path

   def migrate_notebook(notebook_path):
       """Migrate a Jupyter notebook to new API."""
       with open(notebook_path, 'r') as f:
           notebook = json.load(f)

       for cell in notebook.get('cells', []):
           if cell['cell_type'] == 'code':
               source = ''.join(cell['source'])
               # Perform replacements
               source = source.replace('create_logit_ratios_model()', 'create_model()')
               source = source.replace('fit_logit_ratios_model(', 'fit_model(')
               source = source.replace('forecast_logit_ratios(', 'forecast(')
               cell['source'] = source.split('\n')

       with open(notebook_path, 'w') as f:
           json.dump(notebook, f, indent=1)

       print(f"Migrated notebook: {notebook_path}")
   ```

---

## Common Migration Issues

### Issue 1: Mixed Old and New API

**Problem:**
```python
model.create_model()  # New API
model.fit_logit_ratios_model()  # Old API - mixing styles
model.forecast(steps=30)  # New API
```

**Solution:** Use consistent API style (prefer new):
```python
model.create_model()
model.fit_model()
model.forecast(steps=30)
```

### Issue 2: Custom Wrappers

**Problem:** Custom wrapper functions using old API:
```python
def my_forecast_pipeline(container, start, stop):
    model = Model(container, start=start, stop=stop)
    model.create_logit_ratios_model()  # Old API
    model.fit_logit_ratios_model()
    model.forecast_logit_ratios(steps=30)
    return model
```

**Solution:** Update wrapper to use new API:
```python
def my_forecast_pipeline(container, start, stop):
    model = Model(container, start=start, stop=stop)
    model.create_model()  # New API
    model.fit_model()
    model.forecast(steps=30)
    return model
```

### Issue 3: Documentation Strings

**Problem:** Docstrings referencing old methods:
```python
def analyze_epidemic(data):
    """
    Analyze epidemic data.

    Uses model.create_logit_ratios_model() to create VAR model.
    """
    # Implementation
```

**Solution:** Update docstrings:
```python
def analyze_epidemic(data):
    """
    Analyze epidemic data.

    Uses model.create_model() to create VAR model.
    """
    # Implementation
```

---

## Testing Your Migration

### Verification Checklist

After migrating, verify your code:

- [ ] All `create_logit_ratios_model()` replaced with `create_model()`
- [ ] All `fit_logit_ratios_model()` replaced with `fit_model()`
- [ ] All `forecast_logit_ratios()` replaced with `forecast()`
- [ ] No deprecation warnings when running code
- [ ] All tests pass
- [ ] Results match previous version (numerical equivalence)
- [ ] Documentation/comments updated

### Testing Equivalence

Verify that results are identical:

```python
import numpy as np

# Old API (with warnings suppressed)
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    model_old = Model(container, start="2020-03-01", stop="2020-12-31")
    model_old.create_logit_ratios_model()
    model_old.fit_logit_ratios_model(max_lag=10)
    model_old.forecast_logit_ratios(steps=30)
    R0_old = model_old.forecast_R0()

# New API
model_new = Model(container, start="2020-03-01", stop="2020-12-31")
model_new.create_model()
model_new.fit_model(max_lag=10)
model_new.forecast(steps=30)
R0_new = model_new.forecast_R0()

# Verify equivalence
assert np.allclose(R0_old, R0_new), "Results should be identical!"
print("Migration verified: Results are identical")
```

---

## Getting Help

### Resources

- **Documentation**: See `CLAUDE.md` for development guide
- **Examples**: Check `examples/global_forecasting.ipynb` for updated examples
- **Tutorial**: See `TUTORIAL.md` for comprehensive walkthrough
- **Issues**: Report migration problems at https://github.com/julihocc/dynasir/issues

### Support

If you encounter issues during migration:

1. Check this guide for common issues
2. Review the deprecation warning messages
3. Test with a small dataset first
4. Open an issue on GitHub with:
   - Your dynasir version
   - Code example showing the problem
   - Full error message or unexpected behavior

---

## Summary

**Three simple changes:**

1. `create_logit_ratios_model()` → `create_model()`
2. `fit_logit_ratios_model()` → `fit_model()`
3. `forecast_logit_ratios()` → `forecast()`

**Timeline:** Old API works until v0.8.0 (at least 2 minor versions)

**Action:** Update now to avoid breaking changes in v0.8.0

---

*Last updated: November 26, 2025*
*For dynasir v0.6.1-dev*
