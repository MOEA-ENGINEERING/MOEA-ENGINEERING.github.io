"""
rotor.py
========
Rotor and its components.

Hierarchy
---------
Entity
 └── RotorComponent (ABC)
      ├── Shaft
      └── Disc (ABC)
           ├── CompressorWheel
           └── TurbineWheel

CompositeEntity[RotorComponent]
 └── Rotor
"""
from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, List, Optional

import numpy as np

from .base import CompositeEntity, Entity
from .measurement_point import SpeedPoint

if TYPE_CHECKING:
    from .plane import RotatingMeasurementPlane


class RotorComponent(Entity, ABC):
    def __init__(self, name: str, axial_position: float = 0.0, material: str = "",
                 mass: Optional[float] = None, drawing_number: str = "", **kwargs) -> None:
        if type(self) in (RotorComponent, Disc):
            raise TypeError(f"{type(self).__name__} is abstract")
        super().__init__(name, **kwargs)
        self.axial_position = axial_position
        self.material = material
        self.mass = mass
        self.drawing_number = drawing_number


class Shaft(RotorComponent):
    def __init__(self, name: str, length: float = 0.0, diameter: float = 0.0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.length = length
        self.diameter = diameter


class Disc(RotorComponent, ABC):
    def __init__(self, name: str, outer_radius: float = 0.0, blade_count: int = 0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.outer_radius = outer_radius
        self.blade_count = blade_count


# class CompressorWheel(Disc):
#     def __init__(self, name: str, splitter_count: int = 0, **kwargs) -> None:
#         super().__init__(name, **kwargs)
#         self.splitter_count = splitter_count


# class TurbineWheel(Disc):
#     def __init__(self, name: str, turbine_type: str = "radial", **kwargs) -> None:
#         super().__init__(name, **kwargs)
#         self.turbine_type = turbine_type  # "radial" | "axial"


class Rotor(CompositeEntity[RotorComponent]):
    child_type = RotorComponent

    def __init__(self, name: str, speed_point: Optional[SpeedPoint] = None,
                 max_speed_rpm: Optional[float] = None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.speed_point = speed_point
        self.max_speed_rpm = max_speed_rpm
        self._planes: List["RotatingMeasurementPlane"] = []

    # ---- rotor-mounted measurement planes ----------------------------
    def attach_plane(self, plane: "RotatingMeasurementPlane") -> None:
        if plane not in self._planes:
            self._planes.append(plane)
        plane.rotor = self

    @property
    def rotating_planes(self) -> List["RotatingMeasurementPlane"]:
        return list(self._planes)

    # ---- evaluation --------------------------------------------------
    def speed(self, op_id: str, unit: str = "rpm") -> float:
        if self.speed_point is None:
            raise AttributeError(f"Rotor {self.id} has no speed point assigned")
        return self.speed_point.value(op_id, unit)

    def tip_speed(self, radius: float, op_id: str) -> float:
        """Circumferential speed u = omega * r [m/s]."""
        return self.speed(op_id, "rad/s") * radius

    def rotational_frequency(self, op_id: str) -> float:
        """1st engine order [Hz]."""
        return self.speed(op_id, "rad/s") / (2 * np.pi)
