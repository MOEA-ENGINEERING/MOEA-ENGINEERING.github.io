"""
sensor.py
=========
Physical sensors (hardware) and their calibrations. A MeasurementPoint *uses* a Sensor.

Hierarchy
---------
Calibration (ABC)
 ├── IdentityCalibration
 ├── PolynomialCalibration
 └── LookupTableCalibration

Entity
 └── Sensor
      ├── PressureTransducer
      │    └── DynamicPressureTransducer
      ├── TemperatureSensor (ABC)
      │    ├── Thermocouple
      │    └── ResistanceThermometer
      ├── VibrationSensor (ABC)
      │    ├── ProximityProbe
      │    └── Accelerometer
      ├── StrainGauge
      └── SpeedPickup
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import ClassVar, Optional, Sequence, Tuple

import numpy as np

from .base import Entity
from .units import Quantity


# ---------------------------------------------------------------------------
# Calibrations
# ---------------------------------------------------------------------------
class Calibration(ABC):
    """Maps raw sensor output (e.g. mV, mA, counts) to the physical value."""

    def __init__(self, calibrated_on: Optional[date] = None, valid_until: Optional[date] = None,
                 certificate: str = "") -> None:
        self.calibrated_on = calibrated_on
        self.valid_until = valid_until
        self.certificate = certificate

    @abstractmethod
    def apply(self, raw: np.ndarray) -> np.ndarray: ...

    def is_valid(self, on: Optional[date] = None) -> bool:
        on = on or date.today()
        return self.valid_until is None or on <= self.valid_until


class IdentityCalibration(Calibration):
    def apply(self, raw: np.ndarray) -> np.ndarray:
        return np.asarray(raw, dtype=float)


class PolynomialCalibration(Calibration):
    """phys = c0 + c1*raw + c2*raw^2 + ..."""

    def __init__(self, coefficients: Sequence[float], **kwargs) -> None:
        super().__init__(**kwargs)
        self.coefficients = tuple(coefficients)

    def apply(self, raw: np.ndarray) -> np.ndarray:
        return np.polynomial.polynomial.polyval(np.asarray(raw, dtype=float), self.coefficients)


class LookupTableCalibration(Calibration):
    """Piece-wise linear interpolation in a calibration table."""

    def __init__(self, raw_points: Sequence[float], physical_points: Sequence[float], **kwargs) -> None:
        super().__init__(**kwargs)
        self.raw_points = np.asarray(raw_points, dtype=float)
        self.physical_points = np.asarray(physical_points, dtype=float)

    def apply(self, raw: np.ndarray) -> np.ndarray:
        return np.interp(np.asarray(raw, dtype=float), self.raw_points, self.physical_points)


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------
class Sensor(Entity):
    """Generic measuring device."""

    quantity: ClassVar[Quantity] = Quantity.DIMENSIONLESS

    def __init__(
        self,
        name: str,
        serial_number: str = "",
        manufacturer: str = "",
        model: str = "",
        measurement_range: Optional[Tuple[float, float]] = None,
        accuracy: Optional[float] = None,
        calibration: Optional[Calibration] = None,
        **kwargs,
    ) -> None:
        super().__init__(name, **kwargs)
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.model = model
        self.measurement_range = measurement_range
        self.accuracy = accuracy
        self.calibration: Calibration = calibration or IdentityCalibration()

    def convert_raw(self, raw: np.ndarray) -> np.ndarray:
        return self.calibration.apply(raw)


class PressureTransducer(Sensor):
    quantity = Quantity.PRESSURE

    def __init__(self, name: str, pressure_type: str = "absolute", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.pressure_type = pressure_type  # "absolute" | "gauge" | "differential"


class DynamicPressureTransducer(PressureTransducer):
    """High-frequency piezo-resistive / piezo-electric transducer (e.g. Kulite)."""

    def __init__(self, name: str, natural_frequency_hz: Optional[float] = None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.natural_frequency_hz = natural_frequency_hz


class TemperatureSensor(Sensor, ABC):
    quantity = Quantity.TEMPERATURE


class Thermocouple(TemperatureSensor):
    def __init__(self, name: str, tc_type: str = "K", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.tc_type = tc_type


class ResistanceThermometer(TemperatureSensor):
    def __init__(self, name: str, nominal_resistance: float = 100.0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.nominal_resistance = nominal_resistance  # e.g. Pt100


class VibrationSensor(Sensor, ABC):
    pass


class ProximityProbe(VibrationSensor):
    quantity = Quantity.DISPLACEMENT


class Accelerometer(VibrationSensor):
    quantity = Quantity.ACCELERATION

    def __init__(self, name: str, sensitivity_mv_per_g: Optional[float] = None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.sensitivity_mv_per_g = sensitivity_mv_per_g


class StrainGauge(Sensor):
    quantity = Quantity.STRAIN

    def __init__(self, name: str, gauge_factor: float = 2.0, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.gauge_factor = gauge_factor


class SpeedPickup(Sensor):
    quantity = Quantity.ROTATIONAL_SPEED

    def __init__(self, name: str, pulses_per_revolution: int = 1, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.pulses_per_revolution = pulses_per_revolution
