# Exporte les paramètres des scénarios S1 à S5 de la campagne corrigée
# (build_five_case_studies_v2) vers scenarios/scenarios_S1_S5.csv.
# Le code reste la seule source : ce fichier se régénère à chaque appel.
#
# Usage (depuis la racine du dépôt) :
#     PYTHONPATH=src python -m scripts.export_scenarios

import csv
from pathlib import Path

from physec_dm.case_studies import build_five_case_studies_v2

OUTPUT = Path("scenarios") / "scenarios_S1_S5.csv"


def _speed_text(value):
    if isinstance(value, tuple):
        return f"rampe {value[1]:.1f} -> {value[2]:.1f} m/s"
    return f"{value:.1f}"


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario_id", "scenario_name", "separation_mallory",
            "cost_profile", "phase_index", "phase_name",
            "start_fraction", "end_fraction", "mean_snr_db",
            "shadowing_std_db", "mallory_attempt_probability",
            "effective_speed", "criticality_forced",
        ])
        for case in build_five_case_studies_v2():
            for index, phase in enumerate(case["phases"], start=1):
                writer.writerow([
                    case["scenario_id"],
                    case["scenario_name"],
                    case["v2_mallory_separation"],
                    case["v2_cost_profile_id"],
                    index,
                    phase["phase_name"],
                    phase["start_fraction"],
                    phase["end_fraction"],
                    phase["mean_snr_db"],
                    phase["shadowing_std_db"],
                    phase["mallory_attempt_probability"],
                    _speed_text(phase["effective_speed_m_s"]),
                    "" if phase["criticality_forced"] is None else phase["criticality_forced"],
                ])
    print(OUTPUT)


if __name__ == "__main__":
    main()
