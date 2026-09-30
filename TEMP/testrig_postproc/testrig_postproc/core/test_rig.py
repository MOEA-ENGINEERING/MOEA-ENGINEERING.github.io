"""
test_rig.py
===========
Top level of the physical hierarchy: TestRig -> MeasurementPlane -> MeasurementSector -> MeasurementPoint.

Hierarchy
---------
CompositeEntity[MeasurementPlane]
 └── TestRig
      ├── CompressorTestRig
      ├── TurbineTestRig
      └── TurbochargerTestRig (CompressorTestRig, TurbineTestRig)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Type

import pandas as pd

from .base import CompositeEntity
from .measurement_point import MeasurementPoint
from .plane import MeasurementPlane, PlaneRole
from .rotor import Rotor


class TestRig(CompositeEntity[MeasurementPlane]):
    __test__ = False  # prevent pytest from collecting this class
    child_type = MeasurementPlane

    def __init__(self, name: str, location: str = "", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.location = location
        self._rotors: Dict[str, Rotor] = {}

    # ---- rotors ------------------------------------------------------
    def add_rotor(self, rotor: Rotor) -> Rotor:
        rotor.parent = self
        self._rotors[rotor.id] = rotor
        return rotor

    @property
    def rotors(self) -> List[Rotor]:
        return list(self._rotors.values())

    @property
    def rotor(self) -> Rotor:
        """Convenience accessor for single-rotor rigs."""
        if len(self._rotors) != 1:
            raise AttributeError(f"Rig has {len(self._rotors)} rotors – use rotors[...]")
        return next(iter(self._rotors.values()))

    # ---- planes & points ---------------------------------------------
    @property
    def planes(self) -> List[MeasurementPlane]:
        return sorted(self.children, key=lambda p: p.axial_position)

    def plane_by_role(self, role: PlaneRole) -> MeasurementPlane:
        hits = [p for p in self if p.role is role]
        if len(hits) != 1:
            raise LookupError(f"Expected exactly one plane with role {role.name}, found {len(hits)}")
        return hits[0]

    def points(self, point_type: Type[MeasurementPoint] = MeasurementPoint) -> List[MeasurementPoint]:
        pts = [p for plane in self for p in plane.points(point_type)]
        for rotor in self._rotors.values():
            if rotor.speed_point is not None and isinstance(rotor.speed_point, point_type):
                pts.append(rotor.speed_point)
        return pts

    def find_point(self, point_id: str) -> MeasurementPoint:
        for p in self.points():
            if p.id == point_id:
                return p
        raise KeyError(f"Point '{point_id}' not found in rig {self.id}")

    def point_by_channel(self, channel: str) -> Optional[MeasurementPoint]:
        return next((p for p in self.points() if p.channel == channel), None)

    def instrumentation_list(self) -> pd.DataFrame:
        """Tabular overview of all measurement points (instrumentation list)."""
        rows = []
        for p in self.points():
            d = p.to_dict()
            d["plane"] = p.plane.id if p.plane is not None and isinstance(p.plane, MeasurementPlane) else None
            d["sector"] = p.sector.id if p.plane is not None and isinstance(p.plane, MeasurementPlane) else None
            rows.append(d)
        cols = ["plane", "sector", "id", "type", "quantity", "unit", "channel", "x", "r", "theta", "sensor"]
        return pd.DataFrame(rows)[cols]


class CompressorTestRig(TestRig):
    @property
    def compressor_inlet(self) -> MeasurementPlane:
        return self.plane_by_role(PlaneRole.COMPRESSOR_INLET)

    @property
    def compressor_outlet(self) -> MeasurementPlane:
        return self.plane_by_role(PlaneRole.COMPRESSOR_OUTLET)


# class TurbineTestRig(TestRig):
#     @property
#     def turbine_inlet(self) -> MeasurementPlane:
#         return self.plane_by_role(PlaneRole.TURBINE_INLET)

#     @property
#     def turbine_outlet(self) -> MeasurementPlane:
#         return self.plane_by_role(PlaneRole.TURBINE_OUTLET)


# class TurbochargerTestRig(CompressorTestRig, TurbineTestRig):
#     """Rig with compressor and turbine stage on a common rotor."""
