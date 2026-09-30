"""
testrig_postproc
================
Object-oriented framework for post-processing and analysis of test rig data.

Physical hierarchy      : TestRig -> MeasurementPlane -> MeasurementSector -> MeasurementPoint
                          TestRig -> Rotor -> RotorComponent
Organisational hierarchy: TestCampaign (VA) -> TestRun -> OperatingPoint
Data                    : MeasurementPoint[op_id] -> DataRecord
"""
from .core import *  # noqa: F401,F403
from . import analysis, dataio, processing, visualization  # noqa: F401

__version__ = "0.1.0"
