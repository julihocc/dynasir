"""Debug script to understand the measles data and VAR fitting issues."""

import pandas as pd
from dynasir import DataContainer

# Create test data
measles_cases = [
    220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89,
    120, 45, 30, 15, 8, 50, 25, 10, 5, 12, 35, 60, 22, 8, 15
]

data = pd.DataFrame(
    {
        "I": measles_cases,
        "D": [0] * 30,
        "N": [110_000_000] * 30,
    },
    index=pd.date_range("2010", periods=30, freq="YE"),
)

# Create container
container = DataContainer(data, window=1, frequency="YE", mode="incidence")

# Display the engineered features
print("Feature Engineered Data:")
print("=" * 80)
print(container.data[["I", "C", "R", "D", "S", "alpha", "beta", "gamma"]])

print("\n\nLogit Ratios:")
print("=" * 80)
print(container.data[["logit_alpha", "logit_beta", "logit_gamma"]])

print("\n\nSummary Statistics for Logit Ratios:")
print("=" * 80)
print(container.data[["logit_alpha", "logit_beta", "logit_gamma"]].describe())

# Check for NaN or inf values
print("\n\nNaN/Inf Check:")
print("=" * 80)
logit_data = container.data[["logit_alpha", "logit_beta", "logit_gamma"]]
print(f"NaN count: {logit_data.isna().sum().sum()}")
print(f"Inf count: {(logit_data == float('inf')).sum().sum()}")
print(f"-Inf count: {(logit_data == float('-inf')).sum().sum()}")

# Check correlation matrix
print("\n\nCorrelation Matrix:")
print("=" * 80)
print(logit_data.corr())
