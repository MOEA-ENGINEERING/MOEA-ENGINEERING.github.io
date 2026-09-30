"""
data.py
=======
Containers for recorded measurement data of one measurement point at one operating point.

Hierarchy
---------
DataRecord (ABC)
 ├── SteadyStateRecord   – averaged scalar value (+ std, sample count)
 └── TimeSeriesRecord    – sampled signal (time, values)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from .units import UNITS


class DataRecord(ABC):
    """One data set of one measurement point at one operating point."""

    def __init__(self, unit: str) -> None:
        if unit not in UNITS:
            raise KeyError(f"Unknown unit '{unit}'")
        self.unit = unit

    @property
    @abstractmethod
    def mean(self) -> float: ...

    @property
    @abstractmethod
    def std(self) -> float: ...

    @property
    @abstractmethod
    def n_samples(self) -> int: ...

    @abstractmethod
    def convert_to(self, unit: str) -> "DataRecord": ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(mean={self.mean:.6g} {self.unit}, n={self.n_samples})"


class SteadyStateRecord(DataRecord):
    """Time-averaged value as delivered by steady-state acquisition systems."""

    def __init__(self, value: float, unit: str, std: float = 0.0, n_samples: int = 1) -> None:
        super().__init__(unit)
        self._value = float(value)
        self._std = float(std)
        self._n = int(n_samples)

    @property
    def mean(self) -> float:
        return self._value

    @property
    def std(self) -> float:
        return self._std

    @property
    def n_samples(self) -> int:
        return self._n

    def convert_to(self, unit: str) -> "SteadyStateRecord":
        value = float(UNITS.convert(self._value, self.unit, unit))
        # std scales linearly (offset cancels)
        scale = UNITS.get(self.unit).scale / UNITS.get(unit).scale
        return SteadyStateRecord(value, unit, abs(self._std * scale), self._n)


class TimeSeriesRecord(DataRecord):
    """Time-resolved signal (e.g. dynamic pressure, vibration, strain)."""

    def __init__(self, time: np.ndarray, values: np.ndarray, unit: str) -> None:
        super().__init__(unit)
        self.time = np.asarray(time, dtype=float)
        self.values = np.asarray(values, dtype=float)
        if self.time.shape != self.values.shape:
            raise ValueError("time and values must have identical shape")

    # ---- statistics --------------------------------------------------
    @property
    def mean(self) -> float:
        return float(np.mean(self.values))

    @property
    def std(self) -> float:
        return float(np.std(self.values, ddof=1)) if self.values.size > 1 else 0.0

    @property
    def rms(self) -> float:
        return float(np.sqrt(np.mean(self.values ** 2)))

    @property
    def n_samples(self) -> int:
        return int(self.values.size)

    @property
    def sample_rate(self) -> float:
        return 1.0 / float(np.median(np.diff(self.time)))

    @property
    def duration(self) -> float:
        return float(self.time[-1] - self.time[0])

    # ---- manipulation ------------------------------------------------
    def slice(self, t_start: Optional[float] = None, t_end: Optional[float] = None) -> "TimeSeriesRecord":
        mask = np.ones_like(self.time, dtype=bool)
        if t_start is not None:
            mask &= self.time >= t_start
        if t_end is not None:
            mask &= self.time <= t_end
        return TimeSeriesRecord(self.time[mask], self.values[mask], self.unit)

    def convert_to(self, unit: str) -> "TimeSeriesRecord":
        return TimeSeriesRecord(self.time, UNITS.convert(self.values, self.unit, unit), unit)

    def to_steady(self) -> SteadyStateRecord:
        return SteadyStateRecord(self.mean, self.unit, self.std, self.n_samples)
