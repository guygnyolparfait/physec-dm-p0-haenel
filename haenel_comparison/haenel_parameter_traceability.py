# Exporte haenel_config.PARAMETER_TRACEABILITY vers un CSV
# (colonnes : parameter, value, unit, source, paper_page_or_section,
# status, comment), comme demandé à l'Étape 6.

import csv
from pathlib import Path

from haenel_comparison.haenel_config import PARAMETER_TRACEABILITY

OUTPUT_PATH = Path(
    "results/haenel_comparison/haenel_parameter_traceability.csv"
)

FIELD_NAMES = [
    "parameter",
    "value",
    "unit",
    "source",
    "paper_page_or_section",
    "status",
    "used_in",
    "comment",
]


def export_parameter_traceability(output_path=OUTPUT_PATH):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(PARAMETER_TRACEABILITY)

    return output_path


if __name__ == "__main__":

    path = export_parameter_traceability()
    print(f"Traçabilité des paramètres écrite : {path}")
