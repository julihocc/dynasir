# AI Manifest for DynaSIR

**Version**: 0.5.0
**Date**: 2025-09-12
**Type**: Epidemiological Modeling & Forecasting System

## AI Agent Capabilities

### Supported Tasks
- ✅ **Code Analysis**: Deep understanding of SIRD mathematical models and VAR time series
- ✅ **Data Pipeline**: OWID data processing, feature engineering, and validation
- ✅ **Model Development**: Logit transformations, rate calculations, and simulation workflows
- ✅ **Documentation**: Automated updates, version management, and technical writing
- ✅ **Debugging**: Rate bounds checking, missing data handling, and error diagnostics
- ✅ **Visualization**: Epidemic forecasting plots with uncertainty bands and central tendencies

### Domain Expertise Required
- **Mathematics**: Discrete SIRD models, logit functions, VAR time series analysis
- **Epidemiology**: Infection/recovery/mortality rates, basic reproduction number R₀
- **Python Ecosystem**: pandas, statsmodels, scipy, matplotlib, python-box
- **Data Science**: Time series forecasting, Monte Carlo simulation, model validation

## Instruction Files

### Primary Instructions
- **`.github/copilot-instructions.md`**: Comprehensive development guidance
- **`.github/prompts/commit.prompt.md`**: Git workflow management
- **`.github/prompts/update-documentation.prompt.md`**: Version and documentation updates

### Specialized Prompts
- **`.github/prompts/publish-to-pipy.prompt.md`**: PyPI publishing workflow
- **`.github/prompts/release-new-version.prompt.md`**: Release management
- **`.github/prompts/tag-new-version.prompt.md`**: Git tagging procedures

## Project Architecture

### Core Components
```
dynasir.py           # Single-file module with DataContainer and Model classes
├── DataContainer      # Data preprocessing, feature engineering, SIRD calculations
├── Model             # VAR modeling, forecasting, simulations
├── Constants         # ratios, logit_ratios, compartments, forecasting_levels
└── Utilities         # logit/logistic functions, validation, preprocessing
```

### Critical Dependencies
- **statsmodels**: VAR time series modeling
- **python-box**: Nested result containers
- **scipy.stats**: Geometric and harmonic mean calculations
- **pandas**: Time series operations with DatetimeIndex

## Development Patterns

### Data Flow
1. OWID CSV → DataContainer preprocessing → Feature engineering
2. Rate calculations → Logit transformation → VAR modeling
3. Forecasting → Inverse transform → Monte Carlo simulation
4. Results generation → Visualization → Model evaluation

### Key Constraints
- Rates must be in (0,1) bounds before logit transformation
- 14-day lag assumption for recovery calculations
- Forward-fill strategy for missing data
- 27-scenario simulation matrix (3³ confidence intervals)

## AI Integration Notes

### Best Practices
- Always validate data before processing
- Use predefined constants from the module
- Follow feature engineering sequence strictly
- Apply proper error handling patterns
- Generate uncertainty bands for forecasts

### Common Pitfalls
- Don't modify submodule content directly
- Ensure S(t) and I(t) > 0 for rate calculations
- Maintain rate bounds during transformations
- Use Box objects for nested result access
- Apply logarithmic scaling for visualizations

## Version History

### v0.5.0 (Current)
- AI-enhanced documentation and agent integration
- Comprehensive GitHub Copilot instructions
- Standardized prompt templates for development workflows
- Enhanced developer experience with automated processes

### Previous Versions
- v0.4.0: Core epidemiological modeling functionality
- v0.0.1: Initial release with basic SIRD implementation
