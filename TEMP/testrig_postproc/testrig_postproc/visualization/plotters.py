"""
plotters.py
===========
Standard plots.

Hierarchy
---------
Plotter (ABC)
 ├── CircumferentialPlotter      – value vs. theta, one line per OP, sector boundaries
 ├── PerformanceMapPlotter       – e.g. pressure ratio vs. corrected speed / mass flow
 └── SpectrumPlotter             – amplitude vs. frequency or engine order
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Optional, Type, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ..analysis.base import AnalysisResult
from ..core.measurement_point import MeasurementPoint
from ..core.plane import MeasurementPlane


class Plotter(ABC):
    def __init__(self, title: str = "") -> None:
        self.title = title
        self.figure: Optional[plt.Figure] = None

    def plot(self, ax: Optional[plt.Axes] = None) -> plt.Figure:
        if ax is None:
            self.figure, ax = plt.subplots(figsize=(8, 4.5))
        else:
            self.figure = ax.figure
        self._draw(ax)
        ax.set_title(self.title)
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        return self.figure

    def save(self, path: Union[str, Path], dpi: int = 150) -> Path:
        if self.figure is None:
            self.plot()
        self.figure.savefig(path, dpi=dpi)
        return Path(path)

    @abstractmethod
    def _draw(self, ax: plt.Axes) -> None: ...


class CircumferentialPlotter(Plotter):
    def __init__(self, plane: MeasurementPlane, point_type: Type[MeasurementPoint],
                 op_ids: Iterable[str], unit: Optional[str] = None, **kwargs) -> None:
        super().__init__(kwargs.pop("title", f"{plane.name} – {point_type.__name__}"))
        self.plane, self.point_type, self.op_ids, self.unit = plane, point_type, list(op_ids), unit

    def _draw(self, ax):
        for op in self.op_ids:
            df = self.plane.circumferential_distribution(self.point_type, op, self.unit)
            ax.plot(df.theta, df.value, "o-", label=op)
        for s in self.plane.sectors:
            ax.axvline(s.angular_range.start_deg, color="grey", ls="--", lw=0.8)
        unit = self.unit or self.point_type.default_unit
        ax.set_xlabel("theta [deg]"); ax.set_ylabel(f"[{unit}]"); ax.set_xlim(0, 360)
        ax.legend(title="OP", fontsize=8, loc="best")


class PerformanceMapPlotter(Plotter):
    def __init__(self, results: pd.DataFrame, x: str, y: str, group: Optional[str] = None, **kwargs) -> None:
        super().__init__(kwargs.pop("title", f"{y} vs. {x}"))
        self.results, self.x, self.y, self.group = results, x, y, group

    def _draw(self, ax):
        groups = self.results.groupby(self.group) if self.group else [("", self.results)]
        for key, df in groups:
            df = df.sort_values(self.x)
            ax.plot(df[self.x], df[self.y], "o-", label=str(key) if key != "" else None)
        ax.set_xlabel(self.x); ax.set_ylabel(self.y)
        if self.group:
            ax.legend(title=self.group, fontsize=8)


class SpectrumPlotter(Plotter):
    def __init__(self, result: AnalysisResult, use_order: bool = False, f_max: Optional[float] = None,
                 **kwargs) -> None:
        super().__init__(kwargs.pop("title", f"Spectrum – OP {result.op_id}"))
        self.result, self.use_order, self.f_max = result, use_order, f_max

    def _draw(self, ax):
        key = "order" if self.use_order else "frequency"
        ax.plot(self.result.arrays[key], self.result.arrays["amplitude"], lw=0.8)
        ax.set_xlabel("engine order [-]" if self.use_order else "frequency [Hz]")
        ax.set_ylabel(f"amplitude [{self.result.arrays.get('unit', '')}]")
        if self.f_max:
            ax.set_xlim(0, self.f_max)
