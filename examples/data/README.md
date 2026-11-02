# Data Directory

## OWID COVID-19 Data

This directory should contain the `owid-covid-data.csv` file from Our World in Data.

**Official Documentation**: https://docs.owid.io/projects/covid/en/latest/dataset.html

### Dataset Information

- **Complete Dataset**: ~200-300 MB, contains full historical time series data
- **Source**: JHU CSSE COVID-19 Data Repository via Our World in Data
- **Update Frequency**: Daily (when downloaded fresh)
- **License**: Creative Commons BY 4.0 (completely open access)

### How to Download

#### Option 1: Use the Download Script (Recommended)

When you have internet access, run:
```bash
python download_data.py
```

For quick testing with latest data only (not suitable for time series):
```bash
python download_data.py --latest
```

#### Option 2: Manual Download

1. **When you have internet access**, download the data from:
   ```
   https://covid.ourworldindata.org/data/owid-covid-data.csv
   ```

2. Save the file to this directory:
   ```
   examples/data/owid-covid-data.csv
   ```

### File Information

- **Source**: [Our World in Data - COVID-19 Dataset](https://ourworldindata.org/coronavirus)
- **Format**: CSV
- **Size**: ~200-300 MB
- **Update Frequency**: Daily (when downloaded fresh)

### Required Columns

The dynasir package expects these columns:
- `iso_code`: Country/region identifier
- `date`: Date in YYYY-MM-DD format
- `total_cases`: Cumulative confirmed cases
- `total_deaths`: Cumulative deaths
- `population`: Total population

### Workaround for Network Issues

If you cannot download the data due to network issues:

1. Try downloading from a different network or location
2. Ask someone with internet access to download it for you
3. Use a web browser to download manually if command-line tools fail
4. Check if your firewall or antivirus is blocking the connection
