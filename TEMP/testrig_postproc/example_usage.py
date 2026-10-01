"""
example_usage.py
================
Builds a compressor test rig with synthetic data and runs the standard evaluation chain:
    set-up rig -> import data -> process -> analyse -> plot -> export
"""
from pathlib import Path

import numpy as np
import pandas as pd

from testrig_postproc import (AngularRange, CompressorTestRig, CompressorWheel, DisplacementPoint,
                              MeasurementSector, PlaneRole, Position, PressureTransducer, ProximityProbe,
                              Rotor, Shaft, SpeedPoint, StationaryMeasurementPlane, StaticPressurePoint,
                              TestCampaign, TestRun, TimeSeriesRecord, TotalPressurePoint,
                              TotalTemperaturePoint)
from testrig_postproc.analysis import CircumferentialAnalysis, CompressorPerformanceAnalysis, OrderAnalysis
from testrig_postproc.dataio import ExcelResultWriter, SteadyStateCsvReader
from testrig_postproc.processing import LowPassFilter, OutlierRemoval, ProcessingPipeline
from testrig_postproc.visualization import CircumferentialPlotter, PerformanceMapPlotter, SpectrumPlotter

OUT = Path("example_output"); OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(0)

# ---------------------------------------------------------------- 1. rig set-up
rig = CompressorTestRig("Rig_Demo", location="Baden")
rotor = rig.add_rotor(Rotor("R1", speed_point=SpeedPoint("N1", channel="N_RPM"), max_speed_rpm=40000))
rotor.add(Shaft("Shaft", length=0.6, diameter=0.05))
rotor.add(CompressorWheel("CW", outer_radius=0.15, blade_count=9, splitter_count=9))


def build_plane(pid, role, x, n_sectors=4, rakes_per_sector=2):
    plane = rig.add(StationaryMeasurementPlane(pid, axial_position=x, role=role, hub_radius=0.05, tip_radius=0.15))
    span = 360 / n_sectors
    for s in range(n_sectors):
        sec = plane.add(MeasurementSector(f"{pid}_S{s+1}", AngularRange(s * span, (s + 1) * span)))
        for k in range(rakes_per_sector):
            th = s * span + (k + 0.5) * span / rakes_per_sector
            pos = Position(x, 0.10, th)
            tag = f"{pid}_S{s+1}_{k+1}"
            sec.add(TotalPressurePoint(f"PT_{tag}", position=pos,
                                       sensor=PressureTransducer(f"PT_{tag}_sens", serial_number=f"SN{s}{k}")))
            sec.add(TotalTemperaturePoint(f"TT_{tag}", position=pos))
            sec.add(StaticPressurePoint(f"PS_{tag}", position=Position(x, 0.15, th)))
    return plane


p1 = build_plane("E1", PlaneRole.COMPRESSOR_INLET, 0.0)
p2 = build_plane("E2", PlaneRole.COMPRESSOR_OUTLET, 0.3)
brg = rig.add(StationaryMeasurementPlane("B1", axial_position=0.4, role=PlaneRole.BEARING))
brg_sec = brg.add(MeasurementSector("B1_S1"))
prox = brg_sec.add(DisplacementPoint("DX_B1", direction="x", position=Position(0.4, 0.025, 45),
                                     sensor=ProximityProbe("PX1")))

---------------------------------------------------------------- 2. campaign & data import
campaign = TestCampaign("Demo campaign", rig, va_number="VA-0000", test_object="Demo compressor")
run = campaign.add(TestRun("Run01", operator="Demo"))

rows = []
for n in (20000, 25000, 30000):
    for j, throttle in enumerate((0.8, 1.0, 1.2)):
        op = f"N{n//1000}_P{j+1}"
        pr = 1 + 2.2 * (n / 30000) ** 2 * (1.1 - 0.1 * throttle)
        tr = pr ** (0.2857 / (0.80 - 0.04 * (throttle - 1) ** 2 * 10))
        row = {"op_id": op, "N_RPM": n}
        for pt in rig.points():
            if pt.plane is None or pt.plane.id not in ("E1", "E2"):
                continue
            th = np.deg2rad(pt.position.theta)
            dist = 1 + 0.01 * np.cos(th)  # 1st harmonic distortion
            if isinstance(pt, TotalPressurePoint):
                row[pt.channel] = (1.0 if pt.plane.id == "E1" else pr) * 101325 * dist
            elif isinstance(pt, TotalTemperaturePoint):
                row[pt.channel] = (293.15 if pt.plane.id == "E1" else 293.15 * tr) + rng.normal(0, 0.2)
            else:
                row[pt.channel] = (0.95 if pt.plane.id == "E1" else 0.9 * pr) * 101325
        rows.append(row)
csv = OUT / "steady_data.csv"
pd.DataFrame(rows).to_csv(csv, index=False)
reader = SteadyStateCsvReader(rig)
reader.read(csv, run)

# # time-resolved shaft displacement for one OP (1x + 2x + noise)
# op_dyn = "N30_P2"
# fs, t = 20000.0, np.arange(0, 1.0, 1 / 20000.0)
# f1 = 30000 / 60
# x = 25 * np.sin(2 * np.pi * f1 * t) + 6 * np.sin(2 * np.pi * 2 * f1 * t) + rng.normal(0, 2, t.size)
# prox.add_record(op_dyn, TimeSeriesRecord(t, x, "um"))

# # ---------------------------------------------------------------- 3. processing
# pipeline = ProcessingPipeline([OutlierRemoval(4.0), LowPassFilter(cutoff_hz=3000)])
# pipeline.apply_to_points([prox], [op_dyn])

# # ---------------------------------------------------------------- 4. analysis
# perf = CompressorPerformanceAnalysis(rig, rig.compressor_inlet, rig.compressor_outlet)
# perf_df = perf.run_all(campaign.operating_point_ids())
# perf_df["speed_line"] = perf_df.speed_rpm.round(-3).astype(int)
# circ = CircumferentialAnalysis(rig, p2, TotalPressurePoint, unit="bar").run(op_dyn)
# order = OrderAnalysis(rig, prox).run(op_dyn)

# print(rig.instrumentation_list().head(8).to_string(), "\n")
# print(perf_df[["speed_rpm", "pressure_ratio_tt", "eta_is_tt"]].round(3).to_string(), "\n")
# print("Circumferential:", {k: round(v, 4) for k, v in circ.scalars.items()})
# print("Order analysis :", {k: round(v, 3) for k, v in order.scalars.items()})

# # ---------------------------------------------------------------- 5. plots & export
# CircumferentialPlotter(p2, TotalPressurePoint, ["N20_P2", "N25_P2", "N30_P2"], unit="bar").save(OUT / "circ.png")
# PerformanceMapPlotter(perf_df, "corrected_speed_rpm", "pressure_ratio_tt", group="speed_line").save(OUT / "map.png")
# SpectrumPlotter(order, use_order=True).save(OUT / "spectrum.png")
# ExcelResultWriter({"VA": campaign.va_number, "Rig": rig.name}).write(
#     {"performance": perf_df, "instrumentation": rig.instrumentation_list()}, OUT / "results.xlsx")
# print("\nOutputs written to", OUT.resolve())
