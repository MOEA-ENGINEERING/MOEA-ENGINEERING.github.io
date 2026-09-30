"""
performance.py
==============
Thermodynamic stage performance (ideal gas, constant kappa).

Hierarchy
---------
Analysis
 └── PerformanceAnalysis (ABC)
      ├── CompressorPerformanceAnalysis
      └── TurbinePerformanceAnalysis
"""
from __future__ import annotations

from abc import ABC
from typing import Optional

import numpy as np

from ..core.averaging import Averager
from ..core.measurement_point import TotalPressurePoint, TotalTemperaturePoint
from ..core.plane import MeasurementPlane
from ..core.test_rig import TestRig
from .base import Analysis, AnalysisResult


class PerformanceAnalysis(Analysis, ABC):
    def __init__(self, rig: TestRig, inlet: MeasurementPlane, outlet: MeasurementPlane,
                 kappa: float = 1.4, averager: Optional[Averager] = None,
                 t_ref: float = 293.15, p_ref: float = 101325.0) -> None:
        super().__init__(rig)
        self.inlet, self.outlet = inlet, outlet
        self.kappa = kappa
        self.averager = averager
        self.t_ref, self.p_ref = t_ref, p_ref

    def _plane_totals(self, op_id: str):
        pt1 = self.inlet.average(TotalPressurePoint, op_id, "Pa", self.averager)
        tt1 = self.inlet.average(TotalTemperaturePoint, op_id, "K", self.averager)
        pt2 = self.outlet.average(TotalPressurePoint, op_id, "Pa", self.averager)
        tt2 = self.outlet.average(TotalTemperaturePoint, op_id, "K", self.averager)
        return pt1, tt1, pt2, tt2

    def _speed(self, op_id: str) -> float:
        try:
            return self.rig.rotor.speed(op_id, "rpm")
        except (AttributeError, KeyError):
            return float("nan")


class CompressorPerformanceAnalysis(PerformanceAnalysis):
    name = "compressor_performance"

    def _evaluate(self, op_id: str) -> AnalysisResult:
        pt1, tt1, pt2, tt2 = self._plane_totals(op_id)
        pi_tt = pt2 / pt1
        tau = tt2 / tt1
        k = (self.kappa - 1) / self.kappa
        eta_is = (pi_tt ** k - 1) / (tau - 1)
        n = self._speed(op_id)
        return AnalysisResult(self.name, op_id, scalars=dict(
            speed_rpm=n,
            corrected_speed_rpm=n / np.sqrt(tt1 / self.t_ref),
            pt_in_Pa=pt1, Tt_in_K=tt1, pt_out_Pa=pt2, Tt_out_K=tt2,
            pressure_ratio_tt=pi_tt, temperature_ratio_tt=tau, eta_is_tt=eta_is,
        ))


class TurbinePerformanceAnalysis(PerformanceAnalysis):
    name = "turbine_performance"

    def _evaluate(self, op_id: str) -> AnalysisResult:
        pt1, tt1, pt2, tt2 = self._plane_totals(op_id)
        pi_tt = pt1 / pt2
        k = (self.kappa - 1) / self.kappa
        eta_is = (1 - tt2 / tt1) / (1 - pi_tt ** (-k))
        n = self._speed(op_id)
        return AnalysisResult(self.name, op_id, scalars=dict(
            speed_rpm=n,
            corrected_speed_rpm=n / np.sqrt(tt1 / self.t_ref),
            pt_in_Pa=pt1, Tt_in_K=tt1, pt_out_Pa=pt2, Tt_out_K=tt2,
            expansion_ratio_tt=pi_tt, eta_is_tt=eta_is,
        ))
