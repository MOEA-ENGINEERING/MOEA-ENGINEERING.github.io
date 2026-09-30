"""
writers.py
==========
Export of evaluation results.

Hierarchy
---------
ResultWriter (ABC)
 ├── CsvResultWriter
 └── ExcelResultWriter        – one sheet per result table, optional header block (VA/VB number)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

PathLike = Union[str, Path]


class ResultWriter(ABC):
    @abstractmethod
    def write(self, tables: Dict[str, pd.DataFrame], target: PathLike) -> Path: ...


class CsvResultWriter(ResultWriter):
    def __init__(self, sep: str = ";", decimal: str = ".") -> None:
        self.sep = sep
        self.decimal = decimal

    def write(self, tables: Dict[str, pd.DataFrame], target: PathLike) -> Path:
        target = Path(target)
        target.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            df.to_csv(target / f"{name}.csv", sep=self.sep, decimal=self.decimal)
        return target


class ExcelResultWriter(ResultWriter):
    def __init__(self, header: Optional[Dict[str, str]] = None) -> None:
        self.header = header or {}

    def write(self, tables: Dict[str, pd.DataFrame], target: PathLike) -> Path:
        target = Path(target)
        with pd.ExcelWriter(target, engine="openpyxl") as xw:
            if self.header:
                pd.Series(self.header, name="value").to_frame().to_excel(xw, sheet_name="Info")
            for name, df in tables.items():
                df.to_excel(xw, sheet_name=name[:31])
        return target
