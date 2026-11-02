# Network Issues Resolution Guide

## Problem
The `global_forecasting.ipynb` notebook encounters a network error when trying to download COVID-19 data from Our World in Data:
```
gaierror: [Errno 11001] getaddrinfo failed
URLError: <urlopen error [Errno 11001] getaddrinfo failed>
```

This error indicates that your system cannot resolve the domain name or connect to the internet.

## Solutions

### Solution 1: Download Data Manually (Recommended)

1. **When you have internet access**, visit this URL in your web browser:
   ```
   https://covid.ourworldindata.org/data/owid-covid-data.csv
   ```

2. **Save the file** to this location:
   ```
   k:\dynasir\dynasir.worktrees\dashboards\examples\data\owid-covid-data.csv
   ```

3. **Restart the notebook** and run all cells again.

The notebook will automatically detect and use the local data file.

### Solution 2: Use the Download Script

When you have internet connectivity:

```powershell
cd k:\dynasir\dynasir.worktrees\dashboards\examples
python download_data.py
```

This script will download the data and save it to the correct location automatically.

### Solution 3: Network Troubleshooting

If you believe you have internet connectivity, try these steps:

1. **Test your connection:**
   ```powershell
   Test-NetConnection covid.ourworldindata.org -Port 443
   ```

2. **Check DNS resolution:**
   ```powershell
   nslookup covid.ourworldindata.org
   ```

3. **Try with a different DNS server:**
   - Set DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare)

4. **Check firewall settings:**
   - Ensure Python is allowed through Windows Firewall
   - Check if corporate firewall is blocking HTTPS connections

5. **Check proxy settings:**
   - If you're behind a corporate proxy, you may need to configure Python to use it

6. **Try downloading from a browser:**
   - If the browser works but Python doesn't, it's likely a proxy or SSL certificate issue

### Solution 4: Use Alternative Data Source

If you have COVID-19 data from another source, you can modify the notebook:

1. Ensure your data has these columns:
   - `iso_code` (country identifier)
   - `date` (YYYY-MM-DD format)
   - `total_cases` (cumulative confirmed cases)
   - `total_deaths` (cumulative deaths)
   - `population` (total population)

2. Save it as `examples/data/owid-covid-data.csv`

3. The notebook will use it automatically

## What Was Fixed

### 1. Enhanced Error Handling in Notebook
The notebook cell now includes:
- Try-except block to catch network errors gracefully
- Automatic fallback to local data file
- Clear, actionable error messages with file paths
- Instructions for manual data download

### 2. Improved `process_data_from_owid()` Function
Updated `src/dynasir/dynasir.py` to:
- Catch network errors gracefully
- Attempt to use local fallback data
- Provide informative error messages

### 3. Helper Scripts and Documentation
Created:
- `download_data.py`: Script to download data when connected
- `data/README.md`: Data directory documentation
- `NETWORK_ISSUES.md`: This troubleshooting guide (you're reading it!)

## Technical Details

### Error Analysis
The error `gaierror: [Errno 11001] getaddrinfo failed` means:
- **11001**: Windows Socket Error Code for "Host not found"
- **getaddrinfo**: DNS lookup function failed
- **Common causes**:
  - No internet connectivity
  - DNS server not responding
  - Firewall blocking connections
  - Proxy configuration issues
  - Network adapter problems

### File Size Note
The OWID COVID-19 dataset is approximately 200-300 MB. Ensure you have sufficient disk space and patience when downloading.

### Data Update Frequency
The OWID data is updated daily. For the most current data, download fresh from the source when you have connectivity. For historical analysis (like the example notebook), older cached data works fine.

## Support

If you continue experiencing issues:

1. Check your network connectivity with other websites
2. Contact your IT department if on a corporate network
3. Open an issue on GitHub: https://github.com/julihocc/dynasir/issues
4. Include the full error traceback and output of:
   ```powershell
   Test-NetConnection covid.ourworldindata.org -Port 443
   nslookup covid.ourworldindata.org
   ```

## Quick Reference

| Action | Command |
|--------|---------|
| Download manually | Visit URL in browser, save to `examples/data/owid-covid-data.csv` |
| Download via script | `python examples/download_data.py` |
| Check network | `Test-NetConnection covid.ourworldindata.org -Port 443` |
| Check DNS | `nslookup covid.ourworldindata.org` |
| Verify file exists | `Test-Path examples/data/owid-covid-data.csv` |

## Next Steps

Once you have the data file in place:
1. Restart the Jupyter kernel
2. Run all cells from the beginning
3. The notebook should complete successfully

The notebook demonstrates adaptive COVID-19 forecasting using the SIRD model with time-varying parameters estimated via VAR time series analysis.
