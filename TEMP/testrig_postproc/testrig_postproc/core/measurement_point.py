"""
measurement_point.py
====================
Measurement points – the leaves of the rig hierarchy. A point has a position, an
(optional) sensor, a DAQ channel and one DataRecord per operating point.

Hierarchy
---------
Entity
 └── MeasurementPoint (ABC)
      ├── PressurePoint (ABC)
      │    ├── StaticPressurePoint
      │    ├── TotalPressurePoint
      │    └── DynamicPressurePoint
      ├── TemperaturePoint (ABC)
      │    ├── StaticTemperaturePoint
      │    ├── TotalTemperaturePoint
      │    └── MetalTemperaturePoint
      ├── FlowAnglePoint
      ├── VibrationPoint (ABC)
      │    ├── DisplacementPoint
      │    └── AccelerationPoint
      ├── StrainPoint
      └── SpeedPoint
"""
from __future__ import annotations

from abc import ABC
from typing import ClassVar, Dict, List, Optional, Type

from .base import Entity
from .data import DataRecord
from .geometry import Position
from .sensor import Sensor
from .units import UNITS, Quantity


class MeasurementPoint(Entity, ABC):
    """Abstract measurement point. Concrete subclasses define ``quantity`` and ``default_unit``."""

    quantity: ClassVar[Quantity]
    default_unit: ClassVar[str]

    def __init__(
        self,
        name: str,
        position: Optional[Position] = None,
        sensor: Optional[Sensor] = None,
        channel: Optional[str] = None,
        unit: Optional[str] = None,
        **kwargs,
    ) -> None:
        if type(self) in _ABSTRACT_POINT_TYPES:
            raise TypeError(f"{type(self).__name__} is abstract – use a concrete subclass")
        super().__init__(name, **kwargs)
        self.position: Position = position or Position()
        self.sensor = sensor
        self.channel: str = channel or self.id
        self.unit: str = unit or self.default_unit
        self._check_unit(self.unit)
        if sensor is not None and sensor.quantity is not self.quantity:
            raise TypeError(f"Sensor {sensor.id} measures {sensor.quantity.name}, "
                            f"point {self.id} expects {self.quantity.name}")
        self._records: Dict[str, DataRecord] = {}

    # ---- data handling -----------------------------------------------
    def _check_unit(self, unit: str) -> None:
        if UNITS.get(unit).quantity is not self.quantity:
            raise ValueError(f"Unit '{unit}' is not a {self.quantity.name} unit")

    def add_record(self, operating_point_id: str, record: DataRecord) -> None:
        self._check_unit(record.unit)
        self._records[operating_point_id] = record

    def record(self, operating_point_id: str) -> DataRecord:
        try:
            return self._records[operating_point_id]
        except KeyError:
            raise KeyError(f"No data for OP '{operating_point_id}' at {self.path}") from None

    def has_record(self, operating_point_id: str) -> bool:
        return operating_point_id in self._records

    def value(self, operating_point_id: str, unit: Optional[str] = None) -> float:
        """Mean value at an operating point, optionally converted to ``unit``."""
        rec = self.record(operating_point_id)
        return float(UNITS.convert(rec.mean, rec.unit, unit or self.unit))

    @property
    def operating_points(self) -> List[str]:
        return list(self._records)

    # ---- hierarchy navigation ----------------------------------------
    @property
    def sector(self):
        return self.parent

    @property
    def plane(self):
        return self.parent.parent if self.parent else None

    def to_dict(self):
        d = super().to_dict()
        d.update(quantity=self.quantity.name, unit=self.unit, channel=self.channel,
                 x=self.position.axial, r=self.position.radial, theta=self.position.theta,
                 sensor=self.sensor.id if self.sensor else None)
        return d


# ---------------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------------
class PressurePoint(MeasurementPoint, ABC):
    quantity = Quantity.PRESSURE
    default_unit = "Pa"


class StaticPressurePoint(PressurePoint):
    """Wall tapping or static probe."""


class TotalPressurePoint(PressurePoint):
    """Pitot / Kiel probe."""


class DynamicPressurePoint(PressurePoint):
    """Time-resolved (unsteady) pressure, e.g. for surge / rotating stall detection."""


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------
class TemperaturePoint(MeasurementPoint, ABC):
    quantity = Quantity.TEMPERATURE
    default_unit = "K"


class StaticTemperaturePoint(TemperaturePoint):
    pass


class TotalTemperaturePoint(TemperaturePoint):
    def __init__(self, name: str, recovery_factor: float = 1.0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.recovery_factor = recovery_factor


class MetalTemperaturePoint(TemperaturePoint):
    """Component / wall temperature (casing, disc, bearing)."""


# ---------------------------------------------------------------------------
# Flow angle
# ---------------------------------------------------------------------------
class FlowAnglePoint(MeasurementPoint):
    quantity = Quantity.ANGLE
    default_unit = "deg"


# ---------------------------------------------------------------------------
# Vibration / rotor dynamics
# ---------------------------------------------------------------------------
class VibrationPoint(MeasurementPoint, ABC):
    def __init__(self, name: str, direction: str = "x", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.direction = direction  # "x", "y", "axial"


class DisplacementPoint(VibrationPoint):
    quantity = Quantity.DISPLACEMENT
    default_unit = "um"


class AccelerationPoint(VibrationPoint):
    quantity = Quantity.ACCELERATION
    default_unit = "m/s2"


# ---------------------------------------------------------------------------
# Structural / speed
# ---------------------------------------------------------------------------
class StrainPoint(MeasurementPoint):
    quantity = Quantity.STRAIN
    default_unit = "um/m"

    def __init__(self, name: str, orientation_deg: float = 0.0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.orientation_deg = orientation_deg


class SpeedPoint(MeasurementPoint):
    quantity = Quantity.ROTATIONAL_SPEED
    default_unit = "rpm"


# ---------------------------------------------------------------------------
_ABSTRACT_POINT_TYPES = {MeasurementPoint, PressurePoint, TemperaturePoint, VibrationPoint}


def _all_subclasses(cls: type) -> List[type]:
    out = []
    for sub in cls.__subclasses__():
        out.append(sub)
        out.extend(_all_subclasses(sub))
    return out


#: Registry of concrete point types by class name (used by readers / config files)
POINT_TYPES: Dict[str, Type[MeasurementPoint]] = {
    c.__name__: c for c in _all_subclasses(MeasurementPoint) if c not in _ABSTRACT_POINT_TYPES
}
