"""
spectral.py
===========
Frequency analysis of time-resolved measurement points (vibration, dynamic pressure, strain).

Hierarchy
---------
Analysis
 └── SpectralAnalysis
      └── OrderAnalysis           – frequency axis normalised by rotor speed (engine orders)
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..core.data import TimeSeriesRecord
from ..core.measurement_point import MeasurementPoint
from ..core.test_rig import TestRig
from .base import Analysis, AnalysisResult


class SpectralAnalysis(Analysis):
    name = "spectral"

    def __init__(self, rig: TestRig, point: MeasurementPoint, window: str = "hann",
                 unit: Optional[str] = None) -> None:
        super().__init__(rig)
        self.point = point
        self.window = window
        self.unit = unit

    def validate(self, op_id: str) -> None:
        if not isinstance(self.point.record(op_id), TimeSeriesRecord):
            raise TypeError(f"{self.point.id}/{op_id}: spectral analysis requires a TimeSeriesRecord")

    def _spectrum(self, op_id: str):
        rec = self.point.record(op_id)
        if self.unit:
            rec = rec.convert_to(self.unit)
        x = rec.values - rec.mean
        n = x.size
        w = np.hanning(n) if self.window == "hann" else np.ones(n)
        amp = 2.0 * np.abs(np.fft.rfft(x * w)) / np.sum(w)   # single-sided amplitude
        freq = np.fft.rfftfreq(n, 1.0 / rec.sample_rate)
        return freq, amp, rec

    def _evaluate(self, op_id: str) -> AnalysisResult:
        freq, amp, rec = self._spectrum(op_id)
        i = int(np.argmax(amp[1:]) + 1)
        return AnalysisResult(self.name, op_id,
                              scalars=dict(dominant_frequency_Hz=float(freq[i]), dominant_amplitude=float(amp[i]),
                                           rms=rec.rms, sample_rate_Hz=rec.sample_rate),
                              arrays=dict(frequency=freq, amplitude=amp, unit=rec.unit))


class OrderAnalysis(SpectralAnalysis):
    name = "order"

    def _evaluate(self, op_id: str) -> AnalysisResult:
        res = super()._evaluate(op_id)
        f_rot = self.rig.rotor.rotational_frequency(op_id)
        res.arrays["order"] = res.arrays["frequency"] / f_rot
        res.scalars.update(rotational_frequency_Hz=f_rot,
                           dominant_order=res.scalars["dominant_frequency_Hz"] / f_rot)
        # amplitude at integer engine orders 1..4
        for eo in range(1, 5):
            j = int(np.argmin(np.abs(res.arrays["order"] - eo)))
            res.scalars[f"EO{eo}_amplitude"] = float(res.arrays["amplitude"][j])
        return res
