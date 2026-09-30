"""
base.py (analysis)
==================
Common interface for all evaluations (Template-Method pattern).

Hierarchy
---------
AnalysisResult (dataclass)
Analysis (ABC)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

import pandas as pd

from ..core.test_rig import TestRig


@dataclass
class AnalysisResult:
    analysis: str
    op_id: str
    scalars: Dict[str, float] = field(default_factory=dict)     # tabular key figures
    arrays: Dict[str, Any] = field(default_factory=dict)        # distributions, spectra, ...
    warnings: List[str] = field(default_factory=list)

    def to_series(self) -> pd.Series:
        return pd.Series(self.scalars, name=self.op_id)


class Analysis(ABC):
    name: str = "analysis"

    def __init__(self, rig: TestRig) -> None:
        self.rig = rig

    def run(self, op_id: str) -> AnalysisResult:
        self.validate(op_id)
        return self._evaluate(op_id)

    def run_all(self, op_ids: Iterable[str]) -> pd.DataFrame:
        """Evaluate several OPs and return a table (rows = OPs, columns = key figures)."""
        return pd.DataFrame([self.run(op).to_series() for op in op_ids])

    def validate(self, op_id: str) -> None:
        """Hook: check that all required data is available. Override if needed."""

    @abstractmethod
    def _evaluate(self, op_id: str) -> AnalysisResult: ...
