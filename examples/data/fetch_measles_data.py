"""
Download measles-related datasets from Our World in Data.

This script downloads CSV data from Our World in Data's public API
and saves it to the examples/data/owid/ directory.
Adapted from julihocc/measles repository.
"""

import requests
from pathlib import Path
from datetime import datetime
import os

# Our World in Data measles datasets
OWID_DATASETS = {
    "reported_cases_measles": "https://ourworldindata.org/grapher/reported-cases-of-measles.csv",
    "measles_deaths": "https://ourworldindata.org/grapher/deaths-due-to-measles-gbd.csv",
    "measles_vaccination_mcv1": "https://ourworldindata.org/grapher/share-of-children-vaccinated-against-measles.csv",
    "measles_vaccination_mcv2": "https://ourworldindata.org/grapher/share-of-children-vaccinated-with-mcv2.csv",
    "measles_us_cases": "https://ourworldindata.org/grapher/number-of-measles-cases.csv",
    "measles_us_cases_deaths": "https://ourworldindata.org/grapher/measles-cases-and-death.csv",
}


def download_dataset(url: str, output_path: Path) -> None:
    """
    Download a dataset from URL and save to output path.

    Args:
        url: URL of the CSV dataset
        output_path: Path where the file should be saved
    """
    print(f"Downloading {output_path.name}...")

    response = requests.get(url)
    response.raise_for_status()

    output_path.write_text(response.text, encoding='utf-8')
    print(f"  Saved to {output_path}")


def main():
    """Download all Our World in Data measles datasets."""
    # Create output directory relative to this script or current working directory
    # Assuming script is run from project root, placing in examples/data/owid
    output_dir = Path("examples/data/owid")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add timestamp to track when data was downloaded
    timestamp = datetime.now().strftime("%Y%m%d")

    print("Downloading Our World in Data measles datasets...")
    print(f"Output directory: {output_dir.absolute()}\n")

    for name, url in OWID_DATASETS.items():
        # Save both with and without timestamp for easier loading
        output_file_timestamp = output_dir / f"{name}_{timestamp}.csv"
        output_file_latest = output_dir / f"{name}.csv"

        try:
            download_dataset(url, output_file_latest)
            # duplicate content to timestamped file
            output_file_timestamp.write_text(output_file_latest.read_text(encoding='utf-8'), encoding='utf-8')
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading {name}: {e}")

    print("\nDownload complete!")
    print(f"\nDatasets are licensed under Creative Commons BY 4.0")
    print("Citation: Our World in Data (2025) - https://ourworldindata.org")


if __name__ == "__main__":
    main()
