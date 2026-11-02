"""
Headless verification script for Scenario Analysis.
Mimics the logic in examples/scenario_analysis_measles.ipynb.
"""
import pandas as pd
import numpy as np
import logging
from dynasir import DataContainer, Model
from dynasir.analysis.visualization import compare_scenarios
import matplotlib.pyplot as plt

# Disable showing plots
plt.show = lambda: None

logging.basicConfig(level=logging.INFO)

def verify_scenarios():
    print("\n=== Verifying Scenario Analysis ===")
    
    # 1. Setup Data
    dates = pd.date_range(start="2020-01-01", periods=10, freq="YE")
    data = pd.DataFrame({
        "I": [10, 20, 40, 80, 160, 320, 50, 20, 10, 5],
        "N": [1000] * 10,
        "D": [0] * 10
    }, index=dates)
    container = DataContainer(data, mode="incidence")
    
    # 2. Baseline Model
    model = Model(container, importation_rate=0.01)
    model.create_model()
    model.fit_model(max_lag=1)
    model.forecast(steps=5)
    model.run_simulations(n_jobs=1)
    model.generate_result()
    
    baseline_last_I = model.results['I'].iloc[-1]['mean']
    print(f"Baseline I(T+5): {baseline_last_I:.2f}")

    # 3. Create Scenarios
    # Scenario 1: Reduce Beta (expect lower I)
    results_vax = model.create_scenario("Low Beta", {'beta': 0.5})
    vax_last_I = results_vax['I'].iloc[-1]['mean']
    print(f"Low Beta I(T+5): {vax_last_I:.2f}")
    
    assert vax_last_I < baseline_last_I, "Reducing beta should reduce infections"

    # Scenario 2: Increase Beta (expect higher I)
    results_risk = model.create_scenario("High Beta", {'beta': 1.5})
    risk_last_I = results_risk['I'].iloc[-1]['mean']
    print(f"High Beta I(T+5): {risk_last_I:.2f}")
    
    assert risk_last_I > baseline_last_I, "Increasing beta should increase infections"

    # 4. Visualization (ensure no crash)
    scenarios = {
        "Baseline": model.results,
        "Low Beta": results_vax,
        "High Beta": results_risk
    }
    compare_scenarios(scenarios, "I")
    print("✅ Visualization function ran without error")
    
    print("\n✅ All scenario verifications passed!")

if __name__ == "__main__":
    try:
        verify_scenarios()
    except Exception as e:
        print(f"\n❌ Scenario verification failed: {e}")
        import traceback
        traceback.print_exc()
        raise
