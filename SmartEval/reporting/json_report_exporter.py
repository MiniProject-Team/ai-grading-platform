from __future__ import annotations

import json
import logging
from pathlib import Path

from domain.entities.evaluation_report import EvaluationReport


class JsonReportExporter:
    def __init__(self, reports_directory: Path) -> None:
        self.reports_directory = reports_directory
        self.logger = logging.getLogger("smarteval")

    def export(self, report: EvaluationReport) -> Path:
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        output_path = self.reports_directory / f"{self._file_stem(report.report_id)}.json"
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(report.to_dict(), output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
        self.logger.info("JSON report exported: %s", output_path)
        return output_path

    @staticmethod
    def _file_stem(report_id: str) -> str:
        return report_id if report_id.startswith("evaluation_") else f"evaluation_{report_id}"
