"""
sector.py
=========
Measurement sector – circumferential segment of a measurement plane, containing points.

Hierarchy
---------
CompositeEntity[MeasurementPoint]
 └── MeasurementSector
"""
from __future__ import annotations

import warnings
from typing import List, Optional, Tuple, Type

import numpy as np

from .averaging import ArithmeticAverager, Averager
from .base import CompositeEntity
from .geometry import AngularRange
from .measurement_point import MeasurementPoint


class MeasurementSector(CompositeEntity[MeasurementPoint]):
    child_type = MeasurementPoint

    def __init__(self, name: str, angular_range: Optional[AngularRange] = None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.angular_range = angular_range or AngularRange(0.0, 360.0)

    def add(self, point: MeasurementPoint) -> MeasurementPoint:
        if not self.angular_range.contains(point.position.theta):
            warnings.warn(f"{point.id}: theta={point.position.theta:.1f} deg outside sector "
                          f"{self.id} [{self.angular_range.start_deg}, {self.angular_range.end_deg}]")
        return super().add(point)

    # ---- queries -----------------------------------------------------
    def points(self, point_type: Type[MeasurementPoint] = MeasurementPoint) -> List[MeasurementPoint]:
        return [p for p in self if isinstance(p, point_type)]

    def values(self, point_type: Type[MeasurementPoint], op_id: str,
               unit: Optional[str] = None) -> Tuple[List[MeasurementPoint], np.ndarray]:
        pts = [p for p in self.points(point_type) if p.has_record(op_id)]
        return pts, np.array([p.value(op_id, unit) for p in pts])

    def average(self, point_type: Type[MeasurementPoint], op_id: str, unit: Optional[str] = None,
                averager: Optional[Averager] = None) -> float:
        pts, vals = self.values(point_type, op_id, unit)
        return (averager or ArithmeticAverager())(vals, [p.position for p in pts])

    @property
    def plane(self):
        return self.parent
