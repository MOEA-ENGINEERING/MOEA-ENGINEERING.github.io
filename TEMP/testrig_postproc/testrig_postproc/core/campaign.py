"""
campaign.py
===========
Organisational hierarchy of the test: TestCampaign (VA) -> TestRun -> OperatingPoint.

Hierarchy
---------
Entity
 └── OperatingPoint

CompositeEntity[OperatingPoint]
 └── TestRun

CompositeEntity[TestRun]
 └── TestCampaign
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import CompositeEntity, Entity
from .test_rig import TestRig


class OperatingPoint(Entity):
    """One stabilised (or transient) operating condition, identified by ``id``."""

    def __init__(self, name: str, speed_setpoint_rpm: Optional[float] = None,
                 timestamp: Optional[datetime] = None, is_steady: bool = True,
                 boundary_conditions: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.speed_setpoint_rpm = speed_setpoint_rpm
        self.timestamp = timestamp
        self.is_steady = is_steady
        self.boundary_conditions = dict(boundary_conditions or {})  # e.g. ambient p, T, humidity


class TestRun(CompositeEntity[OperatingPoint]):
    """A continuous run (e.g. one speed line or one test day)."""

    __test__ = False
    child_type = OperatingPoint

    def __init__(self, name: str, start_time: Optional[datetime] = None, operator: str = "",
                 rig_configuration: str = "", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.start_time = start_time
        self.operator = operator
        self.rig_configuration = rig_configuration

    @property
    def operating_points(self) -> List[OperatingPoint]:
        return self.children

    @property
    def campaign(self) -> Optional["TestCampaign"]:
        return self.parent


class TestCampaign(CompositeEntity[TestRun]):
    """Test campaign, traceable via test order (VA) and test report (VB) number."""

    __test__ = False
    child_type = TestRun

    def __init__(self, name: str, rig: TestRig, va_number: str = "", vb_number: str = "",
                 test_object: str = "", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.rig = rig
        self.va_number = va_number
        self.vb_number = vb_number
        self.test_object = test_object

    @property
    def runs(self) -> List[TestRun]:
        return self.children

    def operating_points(self) -> List[OperatingPoint]:
        return [op for run in self for op in run]

    def operating_point_ids(self) -> List[str]:
        return [op.id for op in self.operating_points()]
