"""Report generator for scan results."""

import json
from typing import Optional
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from src.models import ScanResult, AccessibilityReport, WCAGCoverage
from src.core.wcag_mapper import (
    get_manual_testing_items,
    group_violations_by_criteria,
    get_conformance_status,
    get_criteria_description
)
from src.utils.config import get_templates_dir
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates accessibility reports in various formats."""

    def __init__(self):
        template_dir = get_templates_dir()
        if template_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
        else:
            self._env = None

    def generate_report(self, scan_result: ScanResult) -> AccessibilityReport:
        """
        Generate a complete accessibility report.

        Args:
            scan_result: Scan result to generate report from

        Returns:
            AccessibilityReport
        """
        # Calculate WCAG coverage
        coverage = WCAGCoverage(
            automatable_criteria=28,
            criteria_checked=len(set(
                c for v in scan_result.violations
                for c in v.wcag_criteria
            )),
            manual_review_needed=get_manual_testing_items()
        )

        return AccessibilityReport(
            scan_result=scan_result,
            wcag_coverage=coverage
        )

    def to_json(self, scan_result: ScanResult, pretty: bool = True) -> str:
        """
        Convert scan result to JSON.

        Args:
            scan_result: Scan result
            pretty: Whether to pretty-print

        Returns:
            JSON string
        """
        report = self.generate_report(scan_result)
        return report.model_dump_json(indent=2 if pretty else None)

    def to_html(self, scan_result: ScanResult) -> str:
        """
        Generate HTML report.

        Args:
            scan_result: Scan result

        Returns:
            HTML string
        """
        report = self.generate_report(scan_result)

        if self._env is None:
            # Fallback to simple HTML
            return self._generate_simple_html(report)

        try:
            template = self._env.get_template("report.html")
            return template.render(
                report=report,
                violations_by_criteria=group_violations_by_criteria(scan_result.violations),
                conformance=get_conformance_status(scan_result.violations),
                get_criteria_description=get_criteria_description
            )
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}, using simple HTML")
            return self._generate_simple_html(report)

    def _generate_simple_html(self, report: AccessibilityReport) -> str:
        """Generate a simple HTML report without templates."""
        result = report.scan_result

        violations_html = ""
        for v in result.violations:
            instances_html = ""
            for inst in v.instances[:5]:  # Limit instances
                instances_html += f"""
                    <div class="instance">
                        <code>{self._escape_html(inst.selector)}</code>
                        <pre>{self._escape_html(inst.html[:200])}</pre>
                        {f'<p class="fix">{self._escape_html(inst.fix_suggestion)}</p>' if inst.fix_suggestion else ''}
                    </div>
                """

            violations_html += f"""
                <div class="violation {v.impact.value}">
                    <h3>{self._escape_html(v.description)}</h3>
                    <div class="meta">
                        <span class="impact">{v.impact.value.upper()}</span>
                        <span class="wcag">WCAG: {', '.join(v.wcag_criteria) or 'N/A'}</span>
                        <span class="tools">Detected by: {', '.join(v.detected_by)}</span>
                    </div>
                    {f'<p>{self._escape_html(v.help_text)}</p>' if v.help_text else ''}
                    {f'<a href="{v.help_url}" target="_blank">Learn more</a>' if v.help_url else ''}
                    <div class="instances">
                        <h4>Affected Elements ({len(v.instances)})</h4>
                        {instances_html}
                    </div>
                </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Report - {self._escape_html(result.url)}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #1a1a2e; color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .header .url {{ color: #888; word-break: break-all; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary-card .value {{ font-size: 2.5em; font-weight: bold; }}
        .summary-card .label {{ color: #666; margin-top: 5px; }}
        .summary-card.score .value {{ color: {self._get_score_color(result.scores.overall)}; }}
        .summary-card.critical .value {{ color: #dc3545; }}
        .summary-card.serious .value {{ color: #fd7e14; }}
        .summary-card.moderate .value {{ color: #ffc107; }}
        .summary-card.minor .value {{ color: #28a745; }}
        .violations {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .violation {{ border-left: 4px solid #ccc; padding: 15px; margin-bottom: 15px; background: #fafafa; }}
        .violation.critical {{ border-color: #dc3545; }}
        .violation.serious {{ border-color: #fd7e14; }}
        .violation.moderate {{ border-color: #ffc107; }}
        .violation.minor {{ border-color: #28a745; }}
        .violation h3 {{ margin: 0 0 10px 0; }}
        .violation .meta {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 10px; font-size: 0.9em; }}
        .violation .meta span {{ background: #eee; padding: 2px 8px; border-radius: 4px; }}
        .violation .impact {{ font-weight: bold; text-transform: uppercase; }}
        .violation.critical .impact {{ background: #dc3545; color: white; }}
        .violation.serious .impact {{ background: #fd7e14; color: white; }}
        .violation.moderate .impact {{ background: #ffc107; }}
        .violation.minor .impact {{ background: #28a745; color: white; }}
        .instances {{ margin-top: 15px; }}
        .instance {{ background: #fff; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
        .instance code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; }}
        .instance pre {{ background: #f8f8f8; padding: 10px; overflow-x: auto; font-size: 0.85em; margin: 10px 0; }}
        .instance .fix {{ color: #28a745; font-style: italic; margin: 5px 0 0 0; }}
        .tools-info {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .tools-info h2 {{ margin-top: 0; }}
        .tool-status {{ display: inline-block; padding: 5px 10px; margin: 5px; border-radius: 4px; background: #e9ecef; }}
        .tool-status.success {{ background: #d4edda; }}
        .tool-status.error {{ background: #f8d7da; }}
        a {{ color: #007bff; }}
        @media (max-width: 600px) {{
            .summary {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Accessibility Report</h1>
            <p class="url">{self._escape_html(result.url)}</p>
            <p>Scanned: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')} | Duration: {result.duration_seconds or 0:.1f}s</p>
        </div>

        <div class="summary">
            <div class="summary-card score">
                <div class="value">{result.scores.overall:.0f}</div>
                <div class="label">Overall Score</div>
            </div>
            <div class="summary-card">
                <div class="value">{result.summary.total_violations}</div>
                <div class="label">Total Violations</div>
            </div>
            <div class="summary-card critical">
                <div class="value">{result.summary.by_impact.get('critical', 0)}</div>
                <div class="label">Critical</div>
            </div>
            <div class="summary-card serious">
                <div class="value">{result.summary.by_impact.get('serious', 0)}</div>
                <div class="label">Serious</div>
            </div>
            <div class="summary-card moderate">
                <div class="value">{result.summary.by_impact.get('moderate', 0)}</div>
                <div class="label">Moderate</div>
            </div>
            <div class="summary-card minor">
                <div class="value">{result.summary.by_impact.get('minor', 0)}</div>
                <div class="label">Minor</div>
            </div>
        </div>

        <div class="violations">
            <h2>Violations ({result.summary.total_violations})</h2>
            {violations_html if violations_html else '<p>No violations found!</p>'}
        </div>

        <div class="tools-info">
            <h2>Tools Used</h2>
            {''.join(f'<span class="tool-status {status.status}">{status.name} ({status.status}){f" - {status.duration_ms}ms" if status.duration_ms else ""}</span>' for status in result.tools_used.values())}
        </div>
    </div>
</body>
</html>"""

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _get_score_color(self, score: float) -> str:
        """Get color based on score."""
        if score >= 90:
            return "#28a745"
        elif score >= 70:
            return "#ffc107"
        elif score >= 50:
            return "#fd7e14"
        return "#dc3545"

    def save_report(
        self,
        scan_result: ScanResult,
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Save report to file.

        Args:
            scan_result: Scan result
            output_path: Output file path
            format: Output format (json, html)
        """
        path = Path(output_path)

        if format == "html":
            content = self.to_html(scan_result)
        else:
            content = self.to_json(scan_result)

        path.write_text(content)
        logger.info(f"Report saved to {path}")
