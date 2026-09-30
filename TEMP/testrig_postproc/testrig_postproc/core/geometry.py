"""
geometry.py
===========
Geometric descriptors for measurement locations.

Hierarchy
---------
ReferenceFrame (Enum)
Position (frozen dataclass)       – cylindrical coordinates (x, r, theta)
AngularRange (frozen dataclass)   – circumferential extent of a sector
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReferenceFrame(Enum):
    STATIONARY = "stationary"   # casing / stator mounted
    ROTATING = "rotating"       # rotor mounted (telemetry, slip ring)


@dataclass(frozen=True)
class Position:
    """Cylindrical position of a measurement point.

    axial          : axial coordinate x [m]
    radial         : radius r [m]
    circumferential: angle theta [deg], 0..360, counted in direction of rotation
    """

    axial: float = 0.0
    radial: float = 0.0
    circumferential: float = 0.0
    frame: ReferenceFrame = ReferenceFrame.STATIONARY

    @property
    def theta(self) -> float:
        return self.circumferential % 360.0


@dataclass(frozen=True)
class AngularRange:
    """Circumferential extent [deg] of a measurement sector (wrap-around allowed)."""

    start_deg: float
    end_deg: float

    @property
    def span(self) -> float:
        return (self.end_deg - self.start_deg) % 360.0 or 360.0

    @property
    def center(self) -> float:
        return (self.start_deg + self.span / 2.0) % 360.0

    def contains(self, theta_deg: float) -> bool:
        return ((theta_deg - self.start_deg) % 360.0) <= self.span
