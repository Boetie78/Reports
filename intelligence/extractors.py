"""Helpers for reading validated values from report_brief.json.

This module deliberately does not infer or repair values. It only extracts values
already present in a validated report brief and returns data references that can
be traced back to the source document.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Evidence:
    """A traceable value from report_brief.json."""

    data_ref: str
    label: str
    value: Any
    unit: str = ""
    evidence_status: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {"data_ref": self.data_ref, "label": self.label, "value": self.value}
        if self.unit:
            data["unit"] = self.unit
        if self.evidence_status is not None:
            data["evidence_status"] = self.evidence_status
        return data


def iter_kpis(doc: dict[str, Any]) -> Iterable[tuple[dict[str, Any], dict[str, Any], int]]:
    """Yield KPI sections with each KPI and its index."""

    for section in doc.get("sections", []):
        if section.get("type") != "kpi_strip":
            continue
        for idx, kpi in enumerate(section.get("kpis", [])):
            yield section, kpi, idx


def iter_breakdowns(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield sections that contain a breakdown object."""

    for section in doc.get("sections", []):
        if section.get("breakdown"):
            yield section


def iter_bar_charts(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for section in doc.get("sections", []):
        if section.get("bar_chart"):
            yield section


def iter_time_series(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for section in doc.get("sections", []):
        if section.get("time_series"):
            yield section


def kpi_evidence(section: dict[str, Any], kpi: dict[str, Any], idx: int) -> Evidence:
    label = kpi.get("label", kpi.get("id", f"KPI {idx + 1}"))
    return Evidence(
        data_ref=f"sections[{section['_index']}].kpis[{idx}].value",
        label=label,
        value=kpi.get("value"),
        unit=kpi.get("unit", ""),
        evidence_status=kpi.get("evidence_status"),
    )


def with_section_indexes(doc: dict[str, Any]) -> dict[str, Any]:
    """Return doc after adding transient _index keys to section dictionaries.

    The keys are used only while generating source references. They are not
    written back to report_brief.json.
    """

    for idx, section in enumerate(doc.get("sections", [])):
        section["_index"] = idx
    return doc


def pct(part: float, total: float) -> float | None:
    if total == 0:
        return None
    return round(part / total * 100, 2)


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.replace("%", "").replace(",", "").strip()
        try:
            return float(stripped)
        except ValueError:
            return None
    return None
