"""
units.py
========
Physical quantities and unit conversion.

Hierarchy
---------
Quantity (Enum)
Unit (frozen dataclass)
UnitRegistry
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union

import numpy as np

ArrayLike = Union[float, np.ndarray]


class Quantity(Enum):
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    ROTATIONAL_SPEED = "rotational_speed"
    DISPLACEMENT = "displacement"
    ACCELERATION = "acceleration"
    VELOCITY = "velocity"
    STRAIN = "strain"
    ANGLE = "angle"
    MASS_FLOW = "mass_flow"
    DIMENSIONLESS = "dimensionless"


@dataclass(frozen=True)
class Unit:
    """Linear unit: value_SI = value * scale + offset."""

    symbol: str
    quantity: Quantity
    scale: float = 1.0
    offset: float = 0.0

    def to_si(self, value: ArrayLike) -> ArrayLike:
        return np.asarray(value) * self.scale + self.offset

    def from_si(self, value: ArrayLike) -> ArrayLike:
        return (np.asarray(value) - self.offset) / self.scale


class UnitRegistry:
    """Central lookup of units and conversion between them."""

    def __init__(self) -> None:
        self._units: Dict[str, Unit] = {}

    def register(self, unit: Unit) -> None:
        self._units[unit.symbol] = unit

    def get(self, symbol: str) -> Unit:
        try:
            return self._units[symbol]
        except KeyError:
            raise KeyError(f"Unknown unit '{symbol}'") from None

    def convert(self, value: ArrayLike, from_unit: str, to_unit: str) -> ArrayLike:
        if from_unit == to_unit:
            return value
        u_from, u_to = self.get(from_unit), self.get(to_unit)
        if u_from.quantity is not u_to.quantity:
            raise ValueError(f"Cannot convert {from_unit} ({u_from.quantity.name}) "
                             f"to {to_unit} ({u_to.quantity.name})")
        return u_to.from_si(u_from.to_si(value))

    def __contains__(self, symbol: str) -> bool:
        return symbol in self._units


# ---------------------------------------------------------------------------
# Default registry
# ---------------------------------------------------------------------------
UNITS = UnitRegistry()
for _u in (
    # pressure (SI: Pa)
    Unit("Pa", Quantity.PRESSURE), Unit("kPa", Quantity.PRESSURE, 1e3),
    Unit("bar", Quantity.PRESSURE, 1e5), Unit("mbar", Quantity.PRESSURE, 1e2),
    Unit("psi", Quantity.PRESSURE, 6894.757293),
    # temperature (SI: K)
    Unit("K", Quantity.TEMPERATURE), Unit("degC", Quantity.TEMPERATURE, 1.0, 273.15),
    # rotational speed (SI: rad/s)
    Unit("rad/s", Quantity.ROTATIONAL_SPEED), Unit("rpm", Quantity.ROTATIONAL_SPEED, 2 * math.pi / 60),
    Unit("Hz_rot", Quantity.ROTATIONAL_SPEED, 2 * math.pi),
    # displacement (SI: m)
    Unit("m", Quantity.DISPLACEMENT), Unit("mm", Quantity.DISPLACEMENT, 1e-3),
    Unit("um", Quantity.DISPLACEMENT, 1e-6),
    # acceleration (SI: m/s^2)
    Unit("m/s2", Quantity.ACCELERATION), Unit("g", Quantity.ACCELERATION, 9.80665),
    # velocity (SI: m/s)
    Unit("m/s", Quantity.VELOCITY), Unit("mm/s", Quantity.VELOCITY, 1e-3),
    # strain (SI: m/m)
    Unit("m/m", Quantity.STRAIN), Unit("um/m", Quantity.STRAIN, 1e-6),
    # angle (SI: rad)
    Unit("rad", Quantity.ANGLE), Unit("deg", Quantity.ANGLE, math.pi / 180),
    # mass flow (SI: kg/s)
    Unit("kg/s", Quantity.MASS_FLOW), Unit("kg/h", Quantity.MASS_FLOW, 1 / 3600),
    # dimensionless
    Unit("-", Quantity.DIMENSIONLESS), Unit("%", Quantity.DIMENSIONLESS, 1e-2),
):
    UNITS.register(_u)
