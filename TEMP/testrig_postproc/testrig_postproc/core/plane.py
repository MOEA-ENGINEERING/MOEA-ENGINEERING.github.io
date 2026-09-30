"""
plane.py
========
Measurement planes – axial stations of the rig, subdivided into sectors.

Hierarchy
---------
PlaneRole (Enum)

CompositeEntity[MeasurementSector]
 └── MeasurementPlane (ABC)
      ├── StationaryMeasurementPlane   – casing / stator mounted instrumentation
      └── RotatingMeasurementPlane     – rotor mounted instrumentation (telemetry)
"""
from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, List, Optional, Tuple, Type

import numpy as np
import pandas as pd

from .averaging import Averager, CircumferentialAverager
from .base import CompositeEntity
from .geometry import ReferenceFrame
from .measurement_point import MeasurementPoint
from .sector import MeasurementSector

if TYPE_CHECKING:
    from .rotor import Rotor


class PlaneRole(Enum):
    COMPRESSOR_INLET = "compressor_inlet"
    COMPRESSOR_OUTLET = "compressor_outlet"
    TURBINE_INLET = "turbine_inlet"
    TURBINE_OUTLET = "turbine_outlet"
    INTERSTAGE = "interstage"
    BEARING = "bearing"
    ROTOR = "rotor"
    OTHER = "other"


class MeasurementPlane(CompositeEntity[MeasurementSector], ABC):
    child_type = MeasurementSector
    reference_frame: ClassVar[ReferenceFrame]

    def __init__(
        self,
        name: str,
        axial_position: float = 0.0,
        role: PlaneRole = PlaneRole.OTHER,
        hub_radius: Optional[float] = None,
        tip_radius: Optional[float] = None,
        **kwargs,
    ) -> None:
        if type(self) is MeasurementPlane:
            raise TypeError("MeasurementPlane is abstract – use Stationary-/RotatingMeasurementPlane")
        super().__init__(name, **kwargs)
        self.axial_position = axial_position
        self.role = role
        self.hub_radius = hub_radius
        self.tip_radius = tip_radius

    # ---- structure ---------------------------------------------------
    @property
    def sectors(self) -> List[MeasurementSector]:
        return self.children

    @property
    def annulus_area(self) -> Optional[float]:
        if self.hub_radius is None or self.tip_radius is None:
            return None
        return float(np.pi * (self.tip_radius ** 2 - self.hub_radius ** 2))

    def points(self, point_type: Type[MeasurementPoint] = MeasurementPoint) -> List[MeasurementPoint]:
        return [p for s in self for p in s.points(point_type)]

    # ---- evaluation --------------------------------------------------
    def circumferential_distribution(self, point_type: Type[MeasurementPoint], op_id: str,
                                     unit: Optional[str] = None) -> pd.DataFrame:
        rows = [
            dict(sector=p.sector.id, point=p.id, theta=p.position.theta,
                 radius=p.position.radial, value=p.value(op_id, unit))
            for p in self.points(point_type) if p.has_record(op_id)
        ]
        return pd.DataFrame(rows).sort_values("theta").reset_index(drop=True) if rows else pd.DataFrame()

    def average(self, point_type: Type[MeasurementPoint], op_id: str, unit: Optional[str] = None,
                averager: Optional[Averager] = None) -> float:
        pts = [p for p in self.points(point_type) if p.has_record(op_id)]
        vals = [p.value(op_id, unit) for p in pts]
        return (averager or CircumferentialAverager())(vals, [p.position for p in pts])

    def sector_averages(self, point_type: Type[MeasurementPoint], op_id: str,
                        unit: Optional[str] = None) -> pd.Series:
        return pd.Series({s.id: s.average(point_type, op_id, unit) for s in self}, name=self.id)


class StationaryMeasurementPlane(MeasurementPlane):
    reference_frame = ReferenceFrame.STATIONARY


class RotatingMeasurementPlane(MeasurementPlane):
    reference_frame = ReferenceFrame.ROTATING

    def __init__(self, name: str, rotor: Optional["Rotor"] = None,
                 transmission: str = "telemetry", **kwargs) -> None:
        kwargs.setdefault("role", PlaneRole.ROTOR)
        super().__init__(name, **kwargs)
        self.rotor = rotor
        self.transmission = transmission  # "telemetry" | "slip_ring"
        if rotor is not None:
            rotor.attach_plane(self)
