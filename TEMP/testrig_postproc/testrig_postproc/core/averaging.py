"""
averaging.py
============
Strategies (Strategy pattern) to combine the values of several measurement points
into one representative value (sector / plane average).

Hierarchy
---------
Averager (ABC)
 ├── ArithmeticAverager
 ├── AreaWeightedAverager          – weighting with radius (annulus area element r*dr)
 └── CircumferentialAverager       – trapezoidal integral over 360 deg (non-uniform spacing)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from .geometry import Position


class Averager(ABC):
    @abstractmethod
    def average(self, values: Sequence[float], positions: Sequence[Position]) -> float: ...

    def __call__(self, values, positions) -> float:
        values = np.asarray(values, dtype=float)
        if values.size == 0:
            return float("nan")
        return self.average(values, positions)


class ArithmeticAverager(Averager):
    def average(self, values, positions) -> float:
        return float(np.nanmean(values))


class AreaWeightedAverager(Averager):
    """Radial area weighting: w_i ~ r_i (valid for equally spaced radial traverses)."""

    def average(self, values, positions) -> float:
        r = np.array([p.radial for p in positions], dtype=float)
        if np.allclose(r, 0.0):
            return float(np.nanmean(values))
        return float(np.nansum(values * r) / np.nansum(r))


class CircumferentialAverager(Averager):
    """Periodic trapezoidal integration over theta; robust to non-uniform probe spacing."""

    def average(self, values, positions) -> float:
        theta = np.array([p.theta for p in positions], dtype=float)
        order = np.argsort(theta)
        theta, v = theta[order], np.asarray(values, dtype=float)[order]
        if theta.size == 1:
            return float(v[0])
        theta_c = np.append(theta, theta[0] + 360.0)
        v_c = np.append(v, v[0])
        return float(np.trapz(v_c, theta_c) / 360.0)
