"""
Publisher metadata used by the UI (logo colours + fonts) and by the
source-diversity / bias dashboard (political lean).
 
Lean is one of: "left" | "center" | "right". The breakdown is kept
deliberately coarse — it feeds the SourceBias arc on the dashboard
rather than any editorial judgement of individual stories.
"""
 
from __future__ import annotations
 
from typing import Dict, Any
 
 
PUBLISHER_META: Dict[str, Dict[str, Any]] = {
    # style block mirrors frontend/src/components/GlobalMap.jsx
    "BBC News":                  {"bg": "#f5a500", "color": "#000", "font": "Georgia, serif",       "lean": "center"},
    "Time Out London":           {"bg": "#000000", "color": "#fff", "font": "Arial, sans-serif",    "lean": "left"},
    "City of London":            {"bg": "#003057", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "House of Commons Library":  {"bg": "#006e46", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "Spectrum News NY1":         {"bg": "#003087", "color": "#fff", "font": "Arial, sans-serif",    "lean": "left"},
    "NYC.gov":                   {"bg": "#003087", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "Staffing Industry":         {"bg": "#1a1a1a", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "Travel and Tour World":     {"bg": "#0077cc", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "The Rio Times":             {"bg": "#006633", "color": "#fff", "font": "Georgia, serif",       "lean": "center"},
    "Indian Defence News":       {"bg": "#ff6600", "color": "#fff", "font": "Arial, sans-serif",    "lean": "right"},
    "Wego Travel Blog":          {"bg": "#00b4d8", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "MINDEF Singapore":          {"bg": "#cc0000", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "CBS News":                  {"bg": "#003876", "color": "#fff", "font": "Arial, sans-serif",    "lean": "left"},
    "NPR":                       {"bg": "#222222", "color": "#fff", "font": "Georgia, serif",       "lean": "left"},
    "CNN":                       {"bg": "#cc0000", "color": "#fff", "font": "Arial, sans-serif",    "lean": "left"},
    "Financial Times":           {"bg": "#fff1e5", "color": "#0d0d0d", "font": "Georgia, serif",    "lean": "center"},
    "Reuters":                   {"bg": "#fb8033", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "ESPN":                      {"bg": "#d50000", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "Associated Press":          {"bg": "#c0392b", "color": "#fff", "font": "Arial, sans-serif",    "lean": "center"},
    "Nature":                    {"bg": "#27a157", "color": "#fff", "font": "Georgia, serif",       "lean": "center"},
    "The New York Times":        {"bg": "#000000", "color": "#fff", "font": "Georgia, serif",       "lean": "left"},
    "Positive News":             {"bg": "#f6a623", "color": "#000", "font": "Arial, sans-serif",    "lean": "left"},
    "Bloomberg":                 {"bg": "#000000", "color": "#fa0",  "font": "Arial, sans-serif",   "lean": "center"},
    "Fox News":                  {"bg": "#1b3e88", "color": "#fff", "font": "Arial, sans-serif",    "lean": "right"},
    "Wall Street Journal":       {"bg": "#000000", "color": "#fff", "font": "Georgia, serif",       "lean": "right"},
}
 
 
UNKNOWN_PUBLISHER = {
    "bg": "#eeeeee",
    "color": "#333333",
    "font": "Arial, sans-serif",
    "lean": "center",
}
 
 
def publisher_style(publisher: str) -> Dict[str, Any]:
    """Return the brand-styling block for a publisher (falls back to neutral)."""
    return PUBLISHER_META.get(publisher, UNKNOWN_PUBLISHER)
 
 
def publisher_lean(publisher: str) -> str:
    return publisher_style(publisher)["lean"]