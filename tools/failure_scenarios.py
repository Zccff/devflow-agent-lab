"""Produce deliberately failing CI logs without network access or external side effects."""

import os
import sys


def main() -> None:
    scenario = os.environ.get("LAB_SCENARIO") or (sys.argv[1] if len(sys.argv) > 1 else "")
    print(f"DEVFLOW_SYNTHETIC_FAILURE scenario={scenario}", flush=True)
    if scenario == "missing-dependency":
        raise ModuleNotFoundError("No module named 'lab_optional_gateway' (deliberate test fixture)")
    if scenario == "simulated-timeout":
        raise TimeoutError("Synthetic gateway request timed out after 30 seconds; no network request was sent")
    raise ValueError(f"Unknown lab scenario: {scenario}")


if __name__ == "__main__":
    main()
