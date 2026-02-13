"""Report generation in multiple formats (HTML, JSON, CSV)."""

import json
import csv
import io
from typing import Dict, List, Any
from datetime import datetime
from jinja2 import Template

from wcag_backend.utils.logger import get_logger

logger = get_logger("report_generator")


class ReportGenerator:
    """Generate reports in HTML, JSON, and CSV formats."""

    def generate_html(self, scan: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
        """
        Generate HTML report.

        Args:
            scan: Scan dictionary
            issues: List of issue dictionaries

        Returns:
            HTML string
        """
        # Group issues by impact
        issues_by_impact = {
            "critical": [i for i in issues if i.get("impact") == "critical"],
            "serious": [i for i in issues if i.get("impact") == "serious"],
            "moderate": [i for i in issues if i.get("impact") == "moderate"],
            "minor": [i for i in issues if i.get("impact") == "minor"]
        }

        # HTML template
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WCAG Accessibility Report - {{ scan.url }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1f2937; border-bottom: 3px solid #6366f1; padding-bottom: 15px; }
        h2 { color: #374151; margin-top: 30px; }
        .score-card { display: flex; gap: 30px; margin: 20px 0; flex-wrap: wrap; }
        .score { text-align: center; padding: 20px; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border-radius: 12px; min-width: 150px; }
        .score-value { font-size: 3rem; font-weight: bold; }
        .stat { text-align: center; padding: 15px; background: #f3f4f6; border-radius: 8px; min-width: 100px; }
        .stat-value { font-size: 1.5rem; font-weight: bold; }
        .stat.critical .stat-value { color: #ef4444; }
        .stat.serious .stat-value { color: #f97316; }
        .stat.moderate .stat-value { color: #f59e0b; }
        .stat.minor .stat-value { color: #10b981; }
        .issue { background: #f9fafb; padding: 15px; margin: 10px 0; border-left: 4px solid #6366f1; border-radius: 4px; }
        .issue.critical { border-left-color: #ef4444; }
        .issue.serious { border-left-color: #f97316; }
        .issue.moderate { border-left-color: #f59e0b; }
        .issue.minor { border-left-color: #10b981; }
        .issue-title { font-weight: bold; color: #1f2937; }
        .issue-details { color: #6b7280; margin-top: 5px; font-size: 0.9rem; }
        .code { background: #1f2937; color: #f3f4f6; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 10px; font-family: monospace; font-size: 0.85rem; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 5px; }
        .badge.critical { background: #fee2e2; color: #991b1b; }
        .badge.serious { background: #ffedd5; color: #9a3412; }
        .badge.moderate { background: #fef3c7; color: #92400e; }
        .badge.minor { background: #d1fae5; color: #065f46; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WCAG Accessibility Report</h1>
        <p><strong>URL:</strong> {{ scan.url }}</p>
        <p><strong>Scan Date:</strong> {{ scan.completed_at }}</p>
        <p><strong>Scan ID:</strong> {{ scan._id }}</p>

        <div class="score-card">
            <div class="score">
                <div class="score-value">{{ scan.score or 0 }}%</div>
                <div>Overall Score</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ issues|length }}</div>
                <div>Total Issues</div>
            </div>
            <div class="stat critical">
                <div class="stat-value">{{ issues_by_impact.critical|length }}</div>
                <div>Critical</div>
            </div>
            <div class="stat serious">
                <div class="stat-value">{{ issues_by_impact.serious|length }}</div>
                <div>Serious</div>
            </div>
            <div class="stat moderate">
                <div class="stat-value">{{ issues_by_impact.moderate|length }}</div>
                <div>Moderate</div>
            </div>
            <div class="stat minor">
                <div class="stat-value">{{ issues_by_impact.minor|length }}</div>
                <div>Minor</div>
            </div>
        </div>

        {% if issues_by_impact.critical %}
        <h2>Critical Issues ({{ issues_by_impact.critical|length }})</h2>
        {% for issue in issues_by_impact.critical %}
        <div class="issue critical">
            <div class="issue-title">{{ issue.description }}</div>
            <div class="issue-details">
                <span class="badge critical">CRITICAL</span>
                {% if issue.wcagCriteria %}<span class="badge">WCAG {{ issue.wcagCriteria }}</span>{% endif %}
                {% if issue.selector %}<strong>Selector:</strong> {{ issue.selector }}{% endif %}
            </div>
            {% if issue.howToFix %}<p>{{ issue.howToFix }}</p>{% endif %}
            {% if issue.htmlSnippet %}<div class="code">{{ issue.htmlSnippet }}</div>{% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if issues_by_impact.serious %}
        <h2>Serious Issues ({{ issues_by_impact.serious|length }})</h2>
        {% for issue in issues_by_impact.serious %}
        <div class="issue serious">
            <div class="issue-title">{{ issue.description }}</div>
            <div class="issue-details">
                <span class="badge serious">SERIOUS</span>
                {% if issue.wcagCriteria %}<span class="badge">WCAG {{ issue.wcagCriteria }}</span>{% endif %}
                {% if issue.selector %}<strong>Selector:</strong> {{ issue.selector }}{% endif %}
            </div>
            {% if issue.howToFix %}<p>{{ issue.howToFix }}</p>{% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if issues_by_impact.moderate %}
        <h2>Moderate Issues ({{ issues_by_impact.moderate|length }})</h2>
        {% for issue in issues_by_impact.moderate %}
        <div class="issue moderate">
            <div class="issue-title">{{ issue.description }}</div>
            <div class="issue-details">
                <span class="badge moderate">MODERATE</span>
                {% if issue.wcagCriteria %}<span class="badge">WCAG {{ issue.wcagCriteria }}</span>{% endif %}
            </div>
        </div>
        {% endfor %}
        {% endif %}

        <p style="margin-top: 30px; color: #666; text-align: center;">
            Generated by WCAG Accessibility Scanner
        </p>
    </div>
</body>
</html>
        """

        template = Template(template_str)
        return template.render(scan=scan, issues=issues, issues_by_impact=issues_by_impact)

    def generate_json(self, scan: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
        """
        Generate JSON report.

        Args:
            scan: Scan dictionary
            issues: List of issue dictionaries

        Returns:
            JSON string
        """
        # Build report structure
        report = {
            "reportId": scan.get("_id"),
            "url": scan.get("url"),
            "score": scan.get("score"),
            "generatedAt": datetime.utcnow().isoformat(),
            "summary": {
                "critical": len([i for i in issues if i.get("impact") == "critical"]),
                "serious": len([i for i in issues if i.get("impact") == "serious"]),
                "moderate": len([i for i in issues if i.get("impact") == "moderate"]),
                "minor": len([i for i in issues if i.get("impact") == "minor"]),
                "totalIssues": len(issues)
            },
            "issues": issues
        }

        return json.dumps(report, indent=2, default=str)

    def generate_csv(self, issues: List[Dict[str, Any]]) -> str:
        """
        Generate CSV report.

        Args:
            issues: List of issue dictionaries

        Returns:
            CSV string
        """
        if not issues:
            return "No issues found"

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "description",
            "impact",
            "wcagCriteria",
            "wcagLevel",
            "selector",
            "howToFix",
            "status",
            "pageUrl"
        ])

        writer.writeheader()
        for issue in issues:
            writer.writerow({
                "description": issue.get("description", ""),
                "impact": issue.get("impact", ""),
                "wcagCriteria": issue.get("wcagCriteria", ""),
                "wcagLevel": issue.get("wcagLevel", ""),
                "selector": issue.get("selector", ""),
                "howToFix": issue.get("howToFix", ""),
                "status": issue.get("status", ""),
                "pageUrl": issue.get("pageUrl", "")
            })

        return output.getvalue()
