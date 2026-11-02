"""
Example: Using ModelReport for Publication-Ready Analysis

This script demonstrates how to use the new reporting tools to generate
comprehensive analysis reports suitable for academic publications.
"""

import pandas as pd
import numpy as np
from pathlib import Path

from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport, create_comparison_report


def create_sample_measles_data():
    """Create sample measles data for demonstration."""
    np.random.seed(42)
    dates = pd.date_range("2010", periods=15, freq="YE")

    # Incident cases (realistic Mexico measles pattern)
    incident_cases = np.array(
        [
            220,
            55,
            667,
            164,
            81,  # 2010-2014: sporadic
            34,
            12,
            0,
            0,
            4,  # 2015-2019: near elimination
            18,
            45,
            103,
            67,
            89,  # 2020-2024: reintroduction
        ]
    )

    # Cumulative deaths (CFR ~0.1%)
    incident_deaths = np.array([1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1])
    cumulative_deaths = np.cumsum(incident_deaths)

    # Population
    population = [120_000_000 + i * 2_000_000 for i in range(15)]

    return pd.DataFrame(
        {"I": incident_cases, "D": cumulative_deaths, "N": population}, index=dates
    )


def main():
    """Demonstrate reporting tools."""
    print("=" * 80)
    print("DynaSIR Reporting Tools - Demonstration")
    print("=" * 80)

    # Setup output directory
    output_dir = Path("examples/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample data
    print("\n1. Creating sample measles data...")
    data = create_sample_measles_data()
    print(f"   Data: {len(data)} years (2010-2024)")

    # Split train/test
    train_data = data.iloc[:10]  # 2010-2019
    test_data = data.iloc[10:]  # 2020-2024

    # Create and fit model
    print("\n2. Creating and fitting model...")
    container = DataContainer(train_data, mode="incidence", window=3)
    model = Model(container)
    model.create_model()
    model.fit_model(max_lag=2)
    model.forecast(steps=5)
    model.run_simulations(n_jobs=1)
    model.generate_result()
    print("   ✅ Model fitted and forecast generated")

    # Create ModelReport
    print("\n3. Generating comprehensive report...")
    report = ModelReport(
        results=model.results,
        testing_data=test_data,
        compartments=["I", "D"],
        model_name="Mexico Measles Forecast (2010-2024)",
    )

    # Generate summary statistics
    print("\n   Summary Statistics:")
    summary_df = report.generate_summary()
    print(summary_df.to_string(index=False))

    # Evaluate forecast accuracy
    print("\n   Evaluation Metrics:")
    eval_df = report.get_evaluation_summary()
    print(eval_df.to_string(index=False))

    # Create multi-panel figure
    print("\n4. Creating forecast visualization...")
    fig = report.plot_forecast_panel(
        figsize=(12, 6), save_path=output_dir / "measles_forecast_panel.png"
    )
    print(f"   ✅ Saved to {output_dir / 'measles_forecast_panel.png'}")

    # Export Markdown report
    print("\n5. Exporting Markdown report...")
    report.export_markdown(
        filepath=output_dir / "measles_report.md",
        include_summary=True,
        include_evaluation=True,
        include_figure=True,
    )

    # Export LaTeX tables
    print("\n6. Exporting LaTeX tables...")
    report.export_latex_table(
        filepath=output_dir / "summary_table.tex", table_type="summary"
    )
    report.export_latex_table(
        filepath=output_dir / "evaluation_table.tex", table_type="evaluation"
    )

    # Demonstrate model comparison
    print("\n7. Creating model comparison...")

    # Create a second model with different window
    container2 = DataContainer(train_data, mode="incidence", window=2)
    model2 = Model(container2)
    model2.create_model()
    model2.fit_model(max_lag=2)
    model2.forecast(steps=5)
    model2.run_simulations(n_jobs=1)
    model2.generate_result()

    # Compare models
    models = {"3-Year Window": model.results, "2-Year Window": model2.results}

    fig_comparison = create_comparison_report(
        models=models,
        testing_data=test_data,
        compartment="I",
        save_path=output_dir / "model_comparison.png",
    )
    print(f"   ✅ Saved to {output_dir / 'model_comparison.png'}")

    # Summary
    print("\n" + "=" * 80)
    print("REPORTING COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files in {output_dir}:")
    print("  📊 measles_forecast_panel.png - Multi-panel forecast visualization")
    print("  📊 model_comparison.png - Model comparison figure")
    print("  📄 measles_report.md - Comprehensive Markdown report")
    print("  📄 summary_table.tex - LaTeX summary statistics table")
    print("  📄 evaluation_table.tex - LaTeX evaluation metrics table")
    print("\n💡 Tip: Use these files directly in your publications!")
    print("=" * 80)


if __name__ == "__main__":
    main()
