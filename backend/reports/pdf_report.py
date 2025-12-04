from typing import Dict, Any

from reports.report_model import build_report_dict
from reports.report_builder import ReportBuilder


def generate_pdf_report(output_dir: str, context: Dict[str, Any]) -> str:
    """Generate a structured multi-page investor PDF.

    This function is a thin wrapper around the EV ReportBuilder v2
    pipeline, which consumes a unified report dictionary and renders
    each page via dedicated layout modules.
    """

    report = build_report_dict(context)
    builder = ReportBuilder(report)
    output_path = builder.build_pdf(output_dir)
    return output_path
