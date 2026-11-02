# COVID-19 Data Sources - Quick Reference

## Official OWID Documentation
- **Main Docs**: https://docs.owid.io/projects/covid/en/latest/dataset.html
- **GitHub Repo**: https://github.com/owid/covid-19-data
- **Data Catalog**: https://catalog.ourworldindata.org/
- **License**: Creative Commons BY 4.0 (completely open access)

## Available Datasets

### 1. Complete Historical Dataset (Required for Time Series Analysis) - RECOMMENDED
- **NEW URL**: https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv
- **Size**: ~50-70 MB (compact format)
- **Content**: Full historical time series data from start of pandemic
- **Format**: CSV with 1 row per location per date
- **Use Case**: Required for dynasir package and forecasting models
- **Column Changes**: Uses `country` column instead of `iso_code`, but also includes `code` column with ISO codes

### 2. Legacy Dataset (May be deprecated)
- **OLD URL**: https://covid.ourworldindata.org/data/owid-covid-data.csv
- **Status**: This URL may no longer be maintained or available
- **Note**: The dynasir package now uses the new catalog URL by default
- **Alternative Formats** (legacy):
  - XLSX: https://covid.ourworldindata.org/data/owid-covid-data.xlsx
  - JSON: https://covid.ourworldindata.org/data/owid-covid-data.json

### 3. Latest Values Only (Not Suitable for Time Series)
- **URL**: https://covid.ourworldindata.org/data/latest/owid-covid-latest.csv
- **Size**: ~2 MB
- **Content**: Only latest values within 2 weeks
- **Use Case**: Quick testing, current statistics only
- **Limitation**: Cannot be used for historical forecasting

## Required Columns for DynaSIR

The package expects these columns from OWID:
- `country` or `code`: Country identifier (use `country="World"` or `iso_code="OWID_WRL"` for global data)
- `date`: Date in YYYY-MM-DD format
- `total_cases`: Cumulative confirmed COVID-19 cases
- `total_deaths`: Cumulative deaths attributed to COVID-19
- `population`: Population (latest available values)

**Note**: The new catalog format uses `country` names (e.g., "World", "United States", "Mexico")
instead of ISO codes, but also includes a `code` column with standard ISO codes (e.g., "OWID_WRL", "USA", "MEX").

## Data Sources (OWID Attribution)

- **Cases & Deaths**: JHU CSSE COVID-19 Data Repository (Johns Hopkins University)
- **Vaccinations**: Official reports collected by Our World in Data team
- **Testing**: Official sources (no longer updated as of June 23, 2022)
- **Hospital/ICU**: Official sources and ECDC
- **Demographics**: UN, World Bank, OECD, IHME, etc.

## Download Methods

### Method 1: Helper Script (Recommended)
```bash
# Complete historical dataset
python examples/download_data.py

# Latest values only (for testing)
python examples/download_data.py --latest
```

### Method 2: Manual Browser Download
1. Visit: https://covid.ourworldindata.org/data/owid-covid-data.csv
2. Save as: `examples/data/owid-covid-data.csv`

### Method 3: Command Line (PowerShell)
```powershell
# Using the NEW catalog URL (recommended)
Invoke-WebRequest -Uri "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv" `
    -OutFile "examples/data/owid-covid-data.csv"

# Using curl (if available)
curl -o examples/data/owid-covid-data.csv `
    https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv
```

### Method 4: Python (Alternative to download_data.py)
```python
import pandas as pd

# New catalog URL (recommended)
url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
data = pd.read_csv(url)
data.to_csv("examples/data/owid-covid-data.csv", index=False)
```

## Network Troubleshooting

If downloads fail with `[Errno 11001] getaddrinfo failed`:

1. **Check DNS Resolution**:
   ```powershell
   nslookup covid.ourworldindata.org
   ```

2. **Test Connectivity**:
   ```powershell
   Test-NetConnection covid.ourworldindata.org -Port 443
   ```

3. **Try Alternative DNS**: Set DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare)

4. **Check Proxy**: If behind corporate proxy, configure environment:
   ```powershell
   $env:HTTP_PROXY = "http://proxy.company.com:8080"
   $env:HTTPS_PROXY = "http://proxy.company.com:8080"
   ```

5. **Use Browser**: If Python fails but browser works, download manually

## Data Structure

### Country Names and ISO Codes

The new catalog format supports both country names and ISO codes:

**Country Names** (use with `country` parameter):
- `World`: Global aggregated data
- `United States`, `Mexico`, `United Kingdom`, etc.

**ISO Codes** (use with `iso_code` parameter or `code` column):
- `OWID_WRL`: World (global aggregated data)
- `OWID_AFR`: Africa
- `OWID_ASI`: Asia
- `OWID_EUR`: Europe
- `OWID_NAM`: North America
- `OWID_SAM`: South America
- `OWID_OCE`: Oceania
- Country codes: Standard ISO 3166-1 alpha-3 (e.g., `USA`, `MEX`, `GBR`)

**Usage Examples**:
```python
# Using country name (new format)
data = process_data_from_owid(country="World")
data = process_data_from_owid(country="United States")

# Using ISO code (backward compatible)
data = process_data_from_owid(iso_code="OWID_WRL")
data = process_data_from_owid(iso_code="MEX")
```

### Date Format
- Format: YYYY-MM-DD (e.g., 2020-03-01)
- Frequency: Daily
- Note: JHU data is by report date, not test/death date

### Data Quality Notes
- Negative daily changes set to NA (data corrections)
- Rolling metrics (7-day averages) handle missing data
- Population estimates from UN World Population Prospects
- Names standardized to OWID standard entity names

## Citations

### For Vaccination Data:
> Mathieu, E., Ritchie, H., Ortiz-Ospina, E. et al. A global database of COVID-19 vaccinations. 
> Nat Hum Behav (2021). https://doi.org/10.1038/s41562-021-01122-8

### For Testing Data:
> Hasell, J., Mathieu, E., Beltekian, D. et al. A cross-country database of COVID-19 testing. 
> Sci Data 7, 345 (2020). https://doi.org/10.1038/s41597-020-00688-8

### For General Use:
> Our World in Data COVID-19 Dataset
> https://covid.ourworldindata.org/data/owid-covid-data.csv
> Licensed under CC BY 4.0

## Updates & Maintenance

- **Dataset Updates**: Daily (when fresh data available from sources)
- **Vaccination Updates**: Weekdays only (Monday-Friday) since March 29, 2022
- **Testing Data**: No longer updated as of June 23, 2022
- **Data Pipeline**: https://docs.owid.io/projects/covid/en/latest/data-pipeline.html

## Related Resources

- **Vaccinations-only dataset**: https://github.com/owid/covid-19-data/tree/master/public/data/vaccinations
- **Excess mortality**: https://github.com/owid/covid-19-data/tree/master/public/data/excess_mortality
- **Hospitalizations**: https://github.com/owid/covid-19-data/tree/master/public/data/hospitalizations
- **Complete codebook**: https://github.com/owid/covid-19-data/tree/master/public/data/owid-covid-codebook.csv

## Quick Start (When You Have Internet)

```bash
# Navigate to examples directory
cd examples

# Download the data
python download_data.py

# Verify download
ls data/owid-covid-data.csv

# Run the notebook
jupyter notebook global_forecasting.ipynb
```

## File Size Reference

| Dataset | Size | Rows | Columns | Download Time (10 Mbps) |
|---------|------|------|---------|-------------------------|
| Complete CSV | ~250 MB | ~400k | ~65 | ~3 minutes |
| Latest CSV | ~2 MB | ~250 | ~65 | ~2 seconds |
| Complete JSON | ~400 MB | - | - | ~5 minutes |
| Complete XLSX | ~180 MB | ~400k | ~65 | ~2 minutes |

## Support

- **OWID Issues**: https://github.com/owid/covid-19-data/issues
- **DynaSIR Issues**: https://github.com/julihocc/dynasir/issues
- **OWID Team**: Cameron Appel, Diana Beltekian, Daniel Gavrilov, Charlie Giattino, Joe Hasell, 
  Bobbie Macdonald, Edouard Mathieu, Esteban Ortiz-Ospina, Hannah Ritchie, Lucas Rodés-Guirao, Max Roser
