"""
precompute.py

Run all six evolutionary scenarios and save the results to results.pkl.

Usage:
    python precompute.py

This takes ~10–20 seconds. The Streamlit app will call this automatically
on first launch if results.pkl does not yet exist.
"""

import pickle
import time
import os
import sys

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(__file__))

from ea.scenarios import SCENARIOS, run_scenario, ScenarioResult

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "results.pkl")

SCENARIO_ORDER = [
    "normal",
    "no_mutation",
    "small_pool",
    "random_mating",
    "no_migration",
    "equal_reproduction",
]


def run_all(seed: int = 42) -> dict[str, ScenarioResult]:
    """
    Run every scenario with a fixed random seed for reproducibility,
    then return a dict keyed by scenario key.
    """
    import random
    random.seed(seed)

    results: dict[str, ScenarioResult] = {}
    total = len(SCENARIO_ORDER)

    for i, key in enumerate(SCENARIO_ORDER, start=1):
        name = SCENARIOS[key]["name"]
        print(f"  [{i}/{total}] Running '{name}' ...", end="", flush=True)
        t0 = time.perf_counter()

        # Each scenario gets its own seed so they start with identical
        # random populations — this makes the comparison fair.
        random.seed(seed + i)
        result = run_scenario(key)

        elapsed = time.perf_counter() - t0
        final_fit = result.best_final_fitness
        print(f"  done in {elapsed:.1f}s  (best fitness: {final_fit:.3f})")
        results[key] = result

    return results


def save(results: dict[str, ScenarioResult], path: str = OUTPUT_PATH):
    with open(path, "wb") as f:
        pickle.dump(results, f)
    size_kb = os.path.getsize(path) / 1024
    print(f"\n  Saved {len(results)} scenarios to '{path}'  ({size_kb:.1f} KB)")


def load(path: str = OUTPUT_PATH) -> dict[str, ScenarioResult]:
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    print("\nPeppered Moth Evolution — Pre-computation\n" + "=" * 45)
    t_start = time.perf_counter()

    results = run_all()
    save(results)

    total_time = time.perf_counter() - t_start
    print(f"  Total time: {total_time:.1f}s\nDone.\n")
