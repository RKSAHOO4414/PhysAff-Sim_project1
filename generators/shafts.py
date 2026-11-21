"""
Shaft & Pin generator: plain shafts, stepped shafts, keyed shafts, chamfered shafts.
Produces 4,000 parts for PhysAff-Sim.
"""

import math
import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import SHAFT_DIAMETER_RANGE, SHAFT_LENGTH_RANGE


class ShaftGenerator(BaseGenerator):
    category = "shafts"

    SHAFT_TYPES = ["plain", "stepped", "keyed", "shouldered"]
    SHAFT_WEIGHTS = [0.25, 0.30, 0.20, 0.25]

    def sample_parameters(self) -> dict:
        shaft_type = self.rng.choice(self.SHAFT_TYPES, p=self.SHAFT_WEIGHTS)
        material = self.sample_material()

        diameter = float(self.rng.uniform(*SHAFT_DIAMETER_RANGE))
        length = float(self.rng.uniform(*SHAFT_LENGTH_RANGE))

        # Chamfers on ends
        has_chamfer = bool(self.rng.random() < 0.7)
        chamfer_size = float(diameter * 0.08) if has_chamfer else 0.0

        # Steps (for stepped shaft): 1-3 steps
        n_steps = int(self.rng.integers(1, 4)) if shaft_type == "stepped" else 0
        step_ratios = sorted(self.rng.uniform(0.5, 0.9, size=max(n_steps, 1)).tolist(), reverse=True)

        # Keyway (for keyed shaft)
        keyway_width = float(diameter * self.rng.uniform(0.2, 0.35)) if shaft_type == "keyed" else 0.0
        keyway_depth = float(keyway_width * 0.5) if shaft_type == "keyed" else 0.0
        keyway_length = float(length * self.rng.uniform(0.3, 0.7)) if shaft_type == "keyed" else 0.0

        # Shoulder (for shouldered shaft)
        shoulder_diameter = float(diameter * self.rng.uniform(1.3, 2.0)) if shaft_type == "shouldered" else 0.0
        shoulder_length = float(length * self.rng.uniform(0.1, 0.3)) if shaft_type == "shouldered" else 0.0
        shoulder_position = self.rng.choice(["end", "middle"]) if shaft_type == "shouldered" else "end"

        # Center hole (for lathe work)
        has_center_hole = bool(self.rng.random() < 0.3)
        center_hole_d = float(diameter * 0.15) if has_center_hole else 0.0
        center_hole_depth = float(min(5.0, length * 0.1)) if has_center_hole else 0.0

        return {
            "shaft_type": shaft_type,
            "material": material,
            "diameter": round(diameter, 2),
            "length": round(length, 2),
            "has_chamfer": has_chamfer,
            "chamfer_size": round(chamfer_size, 3),
            "n_steps": n_steps,
            "step_ratios": [round(r, 3) for r in step_ratios],
            "keyway_width": round(keyway_width, 2),
            "keyway_depth": round(keyway_depth, 2),
            "keyway_length": round(keyway_length, 2),
            "shoulder_diameter": round(shoulder_diameter, 2),
            "shoulder_length": round(shoulder_length, 2),
            "shoulder_position": shoulder_position,
            "has_center_hole": has_center_hole,
            "center_hole_diameter": round(center_hole_d, 2),
            "center_hole_depth": round(center_hole_depth, 2),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        st = params["shaft_type"]
        if st == "plain":
            return self._build_plain(params)
        elif st == "stepped":
            return self._build_stepped(params)
        elif st == "keyed":
            return self._build_keyed(params)
        elif st == "shouldered":
            return self._build_shouldered(params)
        raise ValueError(f"Unknown shaft type: {st}")

    def get_symmetry_group(self, params: dict) -> str:
        if params["shaft_type"] == "keyed":
            return "C1"  # keyway breaks rotational symmetry
        return "C_inf"  # cylindrical symmetry

    def _build_plain(self, params: dict) -> cq.Workplane:
        d = params["diameter"]
        l = params["length"]

        result = (
            cq.Workplane("XY")
            .circle(d / 2)
            .extrude(l)
        )

        # Chamfers
        if params["has_chamfer"] and params["chamfer_size"] > 0.05:
            cs = params["chamfer_size"]
            try:
                result = result.edges("%CIRCLE").chamfer(cs)
            except Exception:
                pass

        # Center holes
        if params["has_center_hole"]:
            result = self._add_center_holes(result, params)

        return result

    def _build_stepped(self, params: dict) -> cq.Workplane:
        d = params["diameter"]
        l = params["length"]
        n_steps = params["n_steps"]
        ratios = params["step_ratios"]

        # Divide length into n_steps + 1 segments
        n_segments = n_steps + 1
        seg_length = l / n_segments

        # First segment at full diameter
        result = (
            cq.Workplane("XY")
            .circle(d / 2)
            .extrude(seg_length)
        )

        # Subsequent segments at reduced diameters
        z_offset = seg_length
        for i in range(n_steps):
            step_d = d * ratios[min(i, len(ratios) - 1)]
            step = (
                cq.Workplane("XY")
                .workplane(offset=z_offset)
                .circle(step_d / 2)
                .extrude(seg_length)
            )
            result = result.union(step)
            z_offset += seg_length

        # Chamfers on ends
        if params["has_chamfer"] and params["chamfer_size"] > 0.05:
            try:
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, 0))
                ).chamfer(params["chamfer_size"])
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, l))
                ).chamfer(params["chamfer_size"] * ratios[-1])
            except Exception:
                pass

        return result

    def _build_keyed(self, params: dict) -> cq.Workplane:
        d = params["diameter"]
        l = params["length"]
        kw = params["keyway_width"]
        kd = params["keyway_depth"]
        kl = params["keyway_length"]

        # Base cylinder
        result = (
            cq.Workplane("XY")
            .circle(d / 2)
            .extrude(l)
        )

        # Keyway: rectangular slot along the top of the shaft
        keyway_start = (l - kl) / 2
        keyway = (
            cq.Workplane("XY")
            .workplane(offset=keyway_start)
            .center(0, d / 2 - kd)
            .box(kw, kd + 1, kl)  # +1 to ensure it cuts through the surface
        )
        result = result.cut(keyway)

        # Chamfers
        if params["has_chamfer"] and params["chamfer_size"] > 0.05:
            try:
                # Only chamfer end edges, not keyway edges
                cs = params["chamfer_size"]
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, 0))
                ).chamfer(cs)
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, l))
                ).chamfer(cs)
            except Exception:
                pass

        return result

    def _build_shouldered(self, params: dict) -> cq.Workplane:
        d = params["diameter"]
        l = params["length"]
        sd = params["shoulder_diameter"]
        sl = params["shoulder_length"]
        pos = params["shoulder_position"]

        # Main shaft
        result = (
            cq.Workplane("XY")
            .circle(d / 2)
            .extrude(l)
        )

        # Shoulder
        if pos == "end":
            shoulder = (
                cq.Workplane("XY")
                .circle(sd / 2)
                .extrude(sl)
                .translate((0, 0, -sl))
            )
        else:  # middle
            mid_z = (l - sl) / 2
            shoulder = (
                cq.Workplane("XY")
                .workplane(offset=mid_z)
                .circle(sd / 2)
                .extrude(sl)
            )

        result = result.union(shoulder)

        # Chamfers
        if params["has_chamfer"] and params["chamfer_size"] > 0.05:
            try:
                cs = params["chamfer_size"]
                if pos == "end":
                    result = result.edges(
                        cq.selectors.NearestToPointSelector((0, 0, -sl))
                    ).chamfer(cs)
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, l))
                ).chamfer(cs)
            except Exception:
                pass

        return result

    def _add_center_holes(self, result, params):
        d = params["center_hole_diameter"]
        depth = params["center_hole_depth"]
        l = params["length"]
        if d <= 0 or depth <= 0:
            return result

        # Hole at z=0 end
        hole1 = (
            cq.Workplane("XY")
            .workplane(offset=-1)
            .circle(d / 2)
            .extrude(depth + 1)
        )
        result = result.cut(hole1)

        # Hole at z=length end
        hole2 = (
            cq.Workplane("XY")
            .workplane(offset=l - depth)
            .circle(d / 2)
            .extrude(depth + 1)
        )
        result = result.cut(hole2)

        return result
