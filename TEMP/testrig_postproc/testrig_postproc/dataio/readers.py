"""
readers.py
==========
Import of raw / pre-processed DAQ data into the object model.

Hierarchy
---------
ChannelMap (dataclass)                – DAQ channel name -> MeasurementPoint id

DataReader (ABC)
 ├── SteadyStateCsvReader              – one row per operating point, one column per channel
 ├── TimeSeriesCsvReader               – one file per operating point, 'time' + channel columns
 └── Hdf5Reader                        – template for HDF5 / TDMS based acquisition systems
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from ..core.campaign import OperatingPoint, TestRun
from ..core.data import SteadyStateRecord, TimeSeriesRecord
from ..core.measurement_point import MeasurementPoint
from ..core.test_rig import TestRig

PathLike = Union[str, Path]


@dataclass
class ChannelMap:
    """Mapping DAQ channel name -> (point id, unit of the raw file)."""

    point_ids: Dict[str, str] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_rig(cls, rig: TestRig) -> "ChannelMap":
        pts = rig.points()
        return cls({p.channel: p.id for p in pts}, {p.channel: p.unit for p in pts})

    @classmethod
    def from_csv(cls, path: PathLike) -> "ChannelMap":
        """CSV with columns: channel, point_id, unit"""
        df = pd.read_csv(path)
        return cls(dict(zip(df.channel, df.point_id)), dict(zip(df.channel, df.unit)))


class DataReader(ABC):
    def __init__(self, rig: TestRig, channel_map: Optional[ChannelMap] = None) -> None:
        self.rig = rig
        self.channel_map = channel_map or ChannelMap.from_rig(rig)
        self.unmapped_channels: List[str] = []

    @abstractmethod
    def read(self, source: PathLike, run: TestRun) -> List[OperatingPoint]:
        """Read ``source`` and attach DataRecords to the rig's measurement points."""

    # ---- helpers -----------------------------------------------------
    def _point(self, channel: str) -> Optional[MeasurementPoint]:
        pid = self.channel_map.point_ids.get(channel)
        if pid is None:
            if channel not in self.unmapped_channels:
                self.unmapped_channels.append(channel)
            return None
        return self.rig.find_point(pid)

    def _unit(self, channel: str, point: MeasurementPoint) -> str:
        return self.channel_map.units.get(channel, point.unit)

    @staticmethod
    def _get_or_create_op(run: TestRun, op_id: str) -> OperatingPoint:
        return run.get(op_id) if op_id in run else run.add(OperatingPoint(op_id))


class SteadyStateCsvReader(DataReader):
    def __init__(self, rig: TestRig, channel_map: Optional[ChannelMap] = None,
                 op_column: str = "op_id", sep: str = ",") -> None:
        super().__init__(rig, channel_map)
        self.op_column = op_column
        self.sep = sep

    def read(self, source: PathLike, run: TestRun) -> List[OperatingPoint]:
        df = pd.read_csv(source, sep=self.sep)
        ops = []
        for _, row in df.iterrows():
            op = self._get_or_create_op(run, str(row[self.op_column]))
            for channel in df.columns.drop(self.op_column):
                point = self._point(channel)
                if point is not None and pd.notna(row[channel]):
                    point.add_record(op.id, SteadyStateRecord(row[channel], self._unit(channel, point)))
            ops.append(op)
        return ops


class TimeSeriesCsvReader(DataReader):
    def __init__(self, rig: TestRig, channel_map: Optional[ChannelMap] = None,
                 time_column: str = "time", sep: str = ",") -> None:
        super().__init__(rig, channel_map)
        self.time_column = time_column
        self.sep = sep

    def read(self, source: PathLike, run: TestRun, op_id: Optional[str] = None) -> List[OperatingPoint]:
        source = Path(source)
        df = pd.read_csv(source, sep=self.sep)
        op = self._get_or_create_op(run, op_id or source.stem)
        t = df[self.time_column].to_numpy()
        for channel in df.columns.drop(self.time_column):
            point = self._point(channel)
            if point is not None:
                point.add_record(op.id, TimeSeriesRecord(t, df[channel].to_numpy(), self._unit(channel, point)))
        return [op]


class Hdf5Reader(DataReader):
    """Template for HDF5-based acquisition data (structure is DAQ specific)."""

    def __init__(self, rig: TestRig, channel_map: Optional[ChannelMap] = None, group: str = "/") -> None:
        super().__init__(rig, channel_map)
        self.group = group

    def read(self, source: PathLike, run: TestRun) -> List[OperatingPoint]:
        raise NotImplementedError("Implement according to the HDF5 layout of the DAQ system")
