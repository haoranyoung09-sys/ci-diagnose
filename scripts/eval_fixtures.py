#!/usr/bin/env python3
"""Score diagnose.py against fixture labels. Offline. Does not call gh.

Rows of the confusion matrix are the meta.json labels. Columns are the
categories the CLI predicted. The CLI does not read those labels while scoring.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = (
    "flake",
    "env",
    "test",
    "deps",
    "permissions",
    "infra",
    "unknown",
)


def load_report(fixtures_dir: str = "fixtures/gha") -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "diagnose.py"),
            "--fixtures-dir",
            fixtures_dir,
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in (0, 1):
        message = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(message or f"diagnose exited {completed.returncode}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"diagnose did not return JSON ({exc})") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("reports"), list):
        raise SystemExit("diagnose JSON has no reports")
    return payload


def confusion(reports: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    matrix = {expected: {predicted: 0 for predicted in CATEGORIES} for expected in CATEGORIES}
    for report in reports:
        expected = str(report.get("expected_label") or "")
        predicted = str(report.get("category") or "")
        if expected not in matrix or predicted not in matrix[expected]:
            raise SystemExit(f"label outside taxonomy: {expected!r} -> {predicted!r}")
        matrix[expected][predicted] += 1
    return matrix


def summarize(matrix: dict[str, dict[str, int]]) -> dict[str, object]:
    total = sum(sum(row.values()) for row in matrix.values())
    correct = sum(matrix[label][label] for label in CATEGORIES)
    per_label: list[dict[str, object]] = []
    for label in CATEGORIES:
        support = sum(matrix[label].values())
        predicted_count = sum(matrix[expected][label] for expected in CATEGORIES)
        true_positive = matrix[label][label]
        recall = true_positive / support if support else 1.0
        precision = true_positive / predicted_count if predicted_count else 1.0
        per_label.append(
            {
                "label": label,
                "support": support,
                "predicted": predicted_count,
                "recall": recall,
                "precision": precision,
            }
        )
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "per_label": per_label,
    }


def format_summary(
    matrix: dict[str, dict[str, int]],
    summary: dict[str, object],
    reports: list[dict[str, object]],
) -> str:
    total = int(summary["total"])
    correct = int(summary["correct"])
    accuracy = float(summary["accuracy"])
    lines = [
        "ci-doctor eval",
        f"fixtures: {total}",
        f"accuracy: {correct}/{total} ({accuracy:.3f})",
        "offline: true",
        "",
        "confusion (row = expected label, column = predicted):",
    ]
    header = f"{'expected':<14}" + "".join(f"{label:>12}" for label in CATEGORIES)
    lines.append(header)
    for expected in CATEGORIES:
        row = f"{expected:<14}" + "".join(
            f"{matrix[expected][predicted]:>12d}" for predicted in CATEGORIES
        )
        lines.append(row)
    lines.append("")
    lines.append(f"{'label':<14}{'support':>8}{'pred':>8}{'recall':>10}{'precision':>12}")
    per_label = summary["per_label"]
    assert isinstance(per_label, list)
    for item in per_label:
        assert isinstance(item, dict)
        lines.append(
            f"{item['label']:<14}"
            f"{int(item['support']):>8d}"
            f"{int(item['predicted']):>8d}"
            f"{float(item['recall']):>10.3f}"
            f"{float(item['precision']):>12.3f}"
        )
    mismatches = [
        report
        for report in reports
        if report.get("label_match") is False
    ]
    lines.append("")
    if mismatches:
        lines.append("mismatches:")
        for report in mismatches:
            lines.append(
                f"  {report.get('id')}: predicted {report.get('category')}, "
                f"expected {report.get('expected_label')}"
            )
    else:
        lines.append("mismatches: 0")
    close = [
        report
        for report in reports
        if report.get("alternates") or float(report.get("confidence") or 0) < 0.8
    ]
    lines.append("")
    lines.append(f"not-high or has alternates: {len(close)}")
    for report in close:
        alternates = report.get("alternates") or []
        alternate_text = ",".join(str(item) for item in alternates) if alternates else "-"
        lines.append(
            f"  {report.get('id')}: {report.get('category')} "
            f"{float(report.get('confidence') or 0):.2f} "
            f"{report.get('confidence_level')} alternates={alternate_text}"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    fixtures_dir = "fixtures/gha"
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        fixtures_dir = argv[0]
    payload = load_report(fixtures_dir)
    reports = payload["reports"]
    assert isinstance(reports, list)
    typed = [report for report in reports if isinstance(report, dict)]
    if len(typed) != len(reports):
        raise SystemExit("a report was not an object")
    matrix = confusion(typed)
    summary = summarize(matrix)
    sys.stdout.write(format_summary(matrix, summary, typed))
    return 0 if summary["correct"] == summary["total"] and summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
