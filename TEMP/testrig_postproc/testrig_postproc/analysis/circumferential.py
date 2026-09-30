"""
circumferential.py
==================
Circumferential non-uniformity of a quantity in one measurement plane.

Hierarchy
---------
Analysis
 └── CircumferentialAnalysis
"""
from __future__ import annotations

from typing import Optional, Type

import numpy as np

from ..core.measurement_point import MeasurementPoint
from ..core.plane import MeasurementPlane
from ..core.test_rig import TestRig
from .base import Analysis, AnalysisResult


class CircumferentialAnalysis(Analysis):
    """Mean, min/max, distortion index and circumferential harmonics (least squares)."""

    name = "circumferential"

    def __init__(self, rig: TestRig, plane: MeasurementPlane, point_type: Type[MeasurementPoint],
                 unit: Optional[str] = None, n_harmonics: int = 2) -> None:
        super().__init__(rig)
        self.plane = plane
        self.point_type = point_type
        self.unit = unit
        self.n_harmonics = n_harmonics

    def validate(self, op_id: str) -> None:
        if not any(p.has_record(op_id) for p in self.plane.points(self.point_type)):
            raise ValueError(f"No {self.point_type.__name__} data in {self.plane.id} for OP {op_id}")

    def _evaluate(self, op_id: str) -> AnalysisResult:
        df = self.plane.circumferential_distribution(self.point_type, op_id, self.unit)
        theta, v = np.deg2rad(df.theta.to_numpy()), df.value.to_numpy()
        mean = self.plane.average(self.point_type, op_id, self.unit)
        res = AnalysisResult(self.name, op_id, arrays={"distribution": df})
        res.scalars.update(mean=mean, min=v.min(), max=v.max(),
                           distortion_index=(v.max() - v.min()) / mean if mean else np.nan)

        n_max = min(self.n_harmonics, (len(v) - 1) // 2)
        if n_max < self.n_harmonics:
            res.warnings.append(f"Only {len(v)} points – harmonics limited to order {n_max}")
        if n_max >= 1:
            cols = [np.ones_like(theta)]
            for k in range(1, n_max + 1):
                cols += [np.cos(k * theta), np.sin(k * theta)]
            coef, *_ = np.linalg.lstsq(np.column_stack(cols), v, rcond=None)
            for k in range(1, n_max + 1):
                a, b = coef[2 * k - 1], coef[2 * k]
                res.scalars[f"H{k}_amplitude"] = float(np.hypot(a, b))
                res.scalars[f"H{k}_phase_deg"] = float(round(np.rad2deg(np.arctan2(b, a)), 6) % 360)
        return res
