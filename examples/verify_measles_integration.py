"""
Verification script for Measles Integration Extensions.
Tests:
1. Incidence Mode (loading, fitting)
2. Importation Rate parameter (impact on simulation)
"""
import pandas as pd
import numpy as np
import logging
from dynasir import DataContainer, Model

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_incidence_mode():
    print("\n=== Verifying Incidence Mode ===")
    # Create synthetic incidence data (sporadic outbreaks)
    # I: 10, 5, 0, 0, 20, 5 (reintroduction)
    I = [10, 5, 0, 0, 20, 5]
    N = [1000] * len(I)
    D = [0] * len(I)
    dates = pd.date_range(start="2020-01-01", periods=len(I), freq="YE")
    
    data = pd.DataFrame({"I": I, "N": N, "D": D}, index=dates)
    
    # 1. Initialize Container
    container = DataContainer(data, mode="incidence")
    print(f"Container Mode: {container.mode}")
    assert container.mode == "incidence"
    
    # 2. Initialize Model without importation
    model = Model(container)
    model.create_model()
    # Use max_lag=1 because we have very few data points
    model.fit_model(max_lag=1)
    model.forecast(steps=5)
    
    # 3. Simulate without importation
    model.run_simulations(n_jobs=1)
    model.generate_result()
    res_no_imp = model.results['I'].iloc[0]['mean']
    print(f"Simulated I (t+1) without importation: {res_no_imp:.4f}")
    
    # 4. Initialize Model WITH importation
    # If epsilon=0.01, S=1000 -> infection = 10 cases extra roughly
    
    model_imp = Model(container, importation_rate=0.01) # Small importation rate
    model_imp.create_model()
    model_imp.fit_model(max_lag=1)
    model_imp.forecast(steps=5)
    model_imp.run_simulations(n_jobs=1)
    model_imp.generate_result()
    res_imp = model_imp.results['I'].iloc[0]['mean']
    print(f"Simulated I (t+1) with importation (0.01): {res_imp:.4f}")
    
    diff = res_imp - res_no_imp
    print(f"Difference: {diff:.4f}")
    
    assert res_imp > res_no_imp, "Importation should increase cases"
    print("✅ Importation rate verified!")

if __name__ == "__main__":
    try:
        verify_incidence_mode()
        print("\nAll verifications passed successfully!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        # traceback
        import traceback
        traceback.print_exc()
