"""Resolve dataRef path strings (e.g. "sections[2].breakdown.components[0].value")
against a report_brief document, and collect every numeric leaf value in the
document for cross-checking narrative text against real data.
"""
import re

_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]")


def resolve_ref(doc, ref):
    """Walk a dotted/bracketed path from the document root. Raises ValueError
    with a clear message on any dangling reference instead of a bare KeyError."""
    node = doc
    consumed = []
    for name, index in _TOKEN_RE.findall(ref):
        try:
            if name:
                node = node[name]
                consumed.append(name)
            else:
                node = node[int(index)]
                consumed.append(f"[{index}]")
        except (KeyError, IndexError, TypeError) as e:
            path_so_far = ".".join(consumed) or "<root>"
            raise ValueError(
                f"dataRef '{ref}' is dangling: failed at '{path_so_far}' ({e})"
            )
    return node


def collect_numeric_leaves(doc):
    """Flatten every numeric value reachable anywhere in the document, plus
    derived percentages (component / parent_total * 100) for breakdowns.
    Used as the ground truth set for citation_check.py."""
    values = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            values.add(round(float(node), 2))

    walk(doc)

    for section in doc.get("sections", []):
        bd = section.get("breakdown")
        if bd:
            parent = bd["parent_total"]["value"]
            if parent:
                for c in bd["components"]:
                    values.add(round(c["value"] / parent * 100, 2))
        ts = section.get("time_series")
        if ts:
            values.add(len(ts.get("categories", [])))

    return values
