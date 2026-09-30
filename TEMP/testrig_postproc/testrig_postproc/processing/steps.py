"""
steps.py
========
Signal processing steps applied to DataRecords (Pipeline / Chain-of-Responsibility pattern).

Hierarchy
---------
ProcessingStep (ABC)
 ├── CalibrationStep
 ├── UnitConversionStep
 ├── OutlierRemoval
 ├── TimeAveraging                – TimeSeriesRecord -> SteadyStateRecord
 └── SignalFilter (ABC)           – TimeSeriesRecord only
      ├── MovingAverageFilter
      └── LowPassFilter           – Butterworth, zero phase

ProcessingPipeline                – ordered list of steps
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

import numpy as np
from scipy import signal as sps

from ..core.data import DataRecord, SteadyStateRecord, TimeSeriesRecord
from ..core.measurement_point import MeasurementPoint
from ..core.sensor import Calibration


class ProcessingStep(ABC):
    @abstractmethod
    def apply(self, record: DataRecord) -> DataRecord: ...

    def __call__(self, record: DataRecord) -> DataRecord:
        return self.apply(record)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class CalibrationStep(ProcessingStep):
    """Converts raw values with a calibration; output unit must be given."""

    def __init__(self, calibration: Calibration, output_unit: str) -> None:
        self.calibration = calibration
        self.output_unit = output_unit

    def apply(self, record: DataRecord) -> DataRecord:
        if isinstance(record, TimeSeriesRecord):
            return TimeSeriesRecord(record.time, self.calibration.apply(record.values), self.output_unit)
        return SteadyStateRecord(float(self.calibration.apply(record.mean)), self.output_unit,
                                 record.std, record.n_samples)


class UnitConversionStep(ProcessingStep):
    def __init__(self, target_unit: str) -> None:
        self.target_unit = target_unit

    def apply(self, record: DataRecord) -> DataRecord:
        return record.convert_to(self.target_unit)


class OutlierRemoval(ProcessingStep):
    """Removes samples outside mean ± n_sigma * std (time series only)."""

    def __init__(self, n_sigma: float = 3.0) -> None:
        self.n_sigma = n_sigma

    def apply(self, record: DataRecord) -> DataRecord:
        if not isinstance(record, TimeSeriesRecord):
            return record
        mask = np.abs(record.values - record.mean) <= self.n_sigma * record.std
        return TimeSeriesRecord(record.time[mask], record.values[mask], record.unit)


class TimeAveraging(ProcessingStep):
    def __init__(self, t_start: Optional[float] = None, t_end: Optional[float] = None) -> None:
        self.t_start, self.t_end = t_start, t_end

    def apply(self, record: DataRecord) -> DataRecord:
        if isinstance(record, TimeSeriesRecord):
            return record.slice(self.t_start, self.t_end).to_steady()
        return record


class SignalFilter(ProcessingStep, ABC):
    def apply(self, record: DataRecord) -> DataRecord:
        if not isinstance(record, TimeSeriesRecord):
            return record
        return TimeSeriesRecord(record.time, self._filter(record.values, record.sample_rate), record.unit)

    @abstractmethod
    def _filter(self, values: np.ndarray, fs: float) -> np.ndarray: ...


class MovingAverageFilter(SignalFilter):
    def __init__(self, window: int = 10) -> None:
        self.window = window

    def _filter(self, values, fs):
        kernel = np.ones(self.window) / self.window
        return np.convolve(values, kernel, mode="same")


class LowPassFilter(SignalFilter):
    def __init__(self, cutoff_hz: float, order: int = 4) -> None:
        self.cutoff_hz = cutoff_hz
        self.order = order

    def _filter(self, values, fs):
        b, a = sps.butter(self.order, self.cutoff_hz, btype="low", fs=fs)
        return sps.filtfilt(b, a, values)


class ProcessingPipeline:
    """Ordered sequence of ProcessingSteps."""

    def __init__(self, steps: Optional[Iterable[ProcessingStep]] = None) -> None:
        self.steps: List[ProcessingStep] = list(steps or [])

    def add(self, step: ProcessingStep) -> "ProcessingPipeline":
        self.steps.append(step)
        return self

    def apply(self, record: DataRecord) -> DataRecord:
        for step in self.steps:
            record = step(record)
        return record

    def apply_to_points(self, points: Iterable[MeasurementPoint], op_ids: Optional[Iterable[str]] = None,
                        in_place: bool = True) -> dict:
        """Process records of several points. Returns {(point_id, op_id): record}."""
        out = {}
        for p in points:
            for op in (op_ids or p.operating_points):
                if not p.has_record(op):
                    continue
                rec = self.apply(p.record(op))
                if in_place:
                    p.add_record(op, rec)
                out[(p.id, op)] = rec
        return out

    def __repr__(self) -> str:
        return " -> ".join(map(repr, self.steps)) or "ProcessingPipeline(empty)"
