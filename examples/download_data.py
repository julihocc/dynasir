"""
Helper script to download OWID COVID-19 data for offline use.

This script downloads the complete historical COVID-19 data from Our World in Data
and saves it locally for use with the dynasir package when internet
connectivity is unavailable.

Data source documentation: https://docs.owid.io/projects/covid/en/latest/dataset.html
"""

import pandas as pd
import os
from pathlib import Path


def download_owid_data(full_dataset=True):
    """
    Download OWID COVID-19 data and save locally.

    Args:
        full_dataset: If True, download complete historical dataset (~50-70MB compact format).
                     If False, download latest values only (~2MB, last 2 weeks).

    Returns:
        bool: True if download successful, False otherwise.
    """
    data_dir = Path(__file__).parent / "data"

    if full_dataset:
        # Complete historical dataset - required for time series analysis
        # Using new catalog URL (compact format, smaller file size)
        url = (
            "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
        )
        output_path = data_dir / "owid-covid-data.csv"
        print(f"Downloading COMPLETE historical dataset from {url}...")
        print("This file is ~50-70MB (compact format) and should download quickly...")
    else:
        # Latest values only - useful for quick testing
        url = "https://covid.ourworldindata.org/data/latest/owid-covid-latest.csv"
        output_path = data_dir / "owid-covid-latest.csv"
        print(f"Downloading LATEST values from {url}...")
        print("This file is ~2MB and downloads quickly...")

    try:
        data = pd.read_csv(url)

        # Create data directory if it doesn't exist
        data_dir.mkdir(exist_ok=True)

        # Save the data
        data.to_csv(output_path, index=False)

        print(f"SUCCESS: Downloaded {len(data):,} rows")
        print(f"SUCCESS: Data saved to: {output_path}")
        print(f"File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

        if not full_dataset:
            print("\nWARNING: You downloaded LATEST data only.")
            print(
                "  For time series analysis in the notebook, you need the FULL dataset."
            )
            print(
                "  Run this script again without arguments to download complete data."
            )

        return True

    except Exception as e:
        print(f"ERROR: Could not download data: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Check your internet connection")
        print("2. Try downloading manually from:")
        print(f"   {url}")
        print(f"3. Save the file to: {output_path}")
        print("4. If behind a proxy/firewall, configure your network settings")
        return False


if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--latest":
        print("Mode: Latest data only (for testing)\n")
        success = download_owid_data(full_dataset=False)
    else:
        print("Mode: Complete historical dataset (default)\n")
        success = download_owid_data(full_dataset=True)

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Data download complete!")
        print("=" * 60)
        print("\nYou can now run the notebook. The data will be loaded automatically.")
    else:
        print("\n" + "=" * 60)
        print("FAILED: Could not download data")
        print("=" * 60)
        print("\nPlease follow the troubleshooting steps above.")
