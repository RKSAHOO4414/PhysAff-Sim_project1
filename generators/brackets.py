"""
Bracket generator: L-brackets, U-brackets, T-brackets.
Produces 4,000 parts for PhysAff-Sim.
"""

import math
import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import BRACKET_TYPES, BRACKET_THICKNESS_RANGE, BRACKET_ARM_RANGE


class BracketGenerator(BaseGenerator):
    category = "brackets"

    BRACKET_WEIGHTS = [0.45, 0.30, 0.25]  # L, U, T

    def sample_parameters(self) -> dict:
        bracket_type = self.rng.choice(BRACKET_TYPES, p=self.BRACKET_WEIGHTS)
        material = self.sample_material()

        thickness = float(self.rng.uniform(*BRACKET_THICKNESS_RANGE))

        # Arm lengths
        arm1_length = float(self.rng.uniform(*BRACKET_ARM_RANGE))
        arm2_length = float(self.rng.uniform(*BRACKET_ARM_RANGE))
        width = float(self.rng.uniform(15.0, 80.0))  # depth (Z extent)

        # Bend angle (90° is standard, allow 80-100° for variation)
        bend_angle = float(self.rng.uniform(80.0, 100.0))

        # Holes: 0–4 per arm
        n_holes_arm1 = int(self.rng.integers(0, 5))
        n_holes_arm2 = int(self.rng.integers(0, 5))
        hole_diameter = float(self.rng.uniform(3.0, min(12.0, width * 0.4, thickness * 3)))

        # Fillet at the bend
        bend_fillet = float(self.rng.uniform(0, thickness * 2))

        # For U-bracket: gap width
        gap_width = float(self.rng.uniform(15.0, 80.0)) if bracket_type == "U" else 0.0

        # For T-bracket: stem length
        stem_length = float(self.rng.uniform(*BRACKET_ARM_RANGE)) if bracket_type == "T" else 0.0

        return {
            "bracket_type": bracket_type,
            "material": material,
            "thickness": round(thickness, 2),
            "arm1_length": round(arm1_length, 2),
            "arm2_length": round(arm2_length, 2),
            "width": round(width, 2),
            "bend_angle": round(bend_angle, 2),
            "n_holes_arm1": n_holes_arm1,
            "n_holes_arm2": n_holes_arm2,
            "hole_diameter": round(hole_diameter, 2),
            "bend_fillet": round(bend_fillet, 2),
            "gap_width": round(gap_width, 2),
            "stem_length": round(stem_length, 2),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        bt = params["bracket_type"]
        if bt == "L":
            return self._build_L(params)
        elif bt == "U":
            return self._build_U(params)
        elif bt == "T":
            return self._build_T(params)
        raise ValueError(f"Unknown bracket type: {bt}")

    def get_symmetry_group(self, params: dict) -> str:
        bt = params["bracket_type"]
        if bt == "U":
            return "C2"  # mirror symmetry
        return "C1"

    # ------------------------------------------------------------------
    def _build_L(self, params: dict) -> cq.Workplane:
        t = params["thickness"]
        a1 = params["arm1_length"]
        a2 = params["arm2_length"]
        w = params["width"]

        # Horizontal arm (along +X)
        arm_h = (
            cq.Workplane("XY")
            .box(a1, w, t, centered=False)
        )
        # Vertical arm (along +Z)
        arm_v = (
            cq.Workplane("XY")
            .box(t, w, a2, centered=False)
        )

        result = arm_h.union(arm_v)

        # Fillet at the inner corner
        if params["bend_fillet"] > 0.1:
            try:
                result = result.edges("|Y").edges(
                    cq.selectors.NearestToPointSelector((t / 2, w / 2, t / 2))
                ).fillet(min(params["bend_fillet"], t * 0.9))
            except Exception:
                pass

        # Holes in horizontal arm
        result = self._add_holes(result, params, arm="horizontal",
                                 count=params["n_holes_arm1"],
                                 arm_length=a1, width=w, thickness=t,
                                 hole_d=params["hole_diameter"],
                                 start_offset=t + 5)

        # Holes in vertical arm
        result = self._add_holes_vertical(result, params, count=params["n_holes_arm2"],
                                          arm_length=a2, width=w, thickness=t,
                                          hole_d=params["hole_diameter"],
                                          start_offset=t + 5)

        return result

    def _build_U(self, params: dict) -> cq.Workplane:
        t = params["thickness"]
        a1 = params["arm1_length"]  # height of the two arms
        gap = params["gap_width"]
        w = params["width"]

        # Base plate
        total_width = gap + 2 * t
        base = (
            cq.Workplane("XY")
            .box(total_width, w, t, centered=False)
        )

        # Left arm (vertical)
        left = (
            cq.Workplane("XY")
            .box(t, w, a1, centered=False)
        )

        # Right arm (vertical)
        right = (
            cq.Workplane("XY")
            .box(t, w, a1, centered=False)
            .translate((gap + t, 0, 0))
        )

        result = base.union(left).union(right)

        # Holes in base
        result = self._add_holes(result, params, arm="horizontal",
                                 count=min(params["n_holes_arm1"], 3),
                                 arm_length=total_width, width=w, thickness=t,
                                 hole_d=params["hole_diameter"],
                                 start_offset=t + 2)

        return result

    def _build_T(self, params: dict) -> cq.Workplane:
        t = params["thickness"]
        a1 = params["arm1_length"]  # top bar length
        stem = params["stem_length"]
        w = params["width"]

        # Top horizontal bar (centered on X)
        top_bar = (
            cq.Workplane("XY")
            .box(a1, w, t)  # centered
        )

        # Stem going downward from center
        stem_part = (
            cq.Workplane("XY")
            .box(t, w, stem, centered=False)
            .translate((-t / 2, -w / 2, -stem))
        )

        result = top_bar.union(stem_part)

        # Holes in top bar
        if params["n_holes_arm1"] > 0:
            spacing = a1 / (params["n_holes_arm1"] + 1)
            for i in range(params["n_holes_arm1"]):
                x = -a1 / 2 + spacing * (i + 1)
                hole = (
                    cq.Workplane("XY")
                    .workplane(offset=t / 2)
                    .center(x, 0)
                    .circle(params["hole_diameter"] / 2)
                    .extrude(-t - 1)
                )
                result = result.cut(hole)

        return result

    # ------------------------------------------------------------------
    # Helpers for adding holes
    # ------------------------------------------------------------------
    def _add_holes(self, result, params, arm, count, arm_length, width, thickness,
                   hole_d, start_offset):
        if count <= 0 or hole_d >= thickness * 3:
            return result
        usable = arm_length - start_offset - 5
        if usable <= 0 or count == 0:
            return result
        spacing = usable / max(count, 1)
        for i in range(count):
            x = start_offset + spacing * (i + 0.5)
            if x + hole_d / 2 > arm_length - 2:
                continue
            hole = (
                cq.Workplane("XY")
                .workplane(offset=thickness + 1)
                .center(x, width / 2)
                .circle(hole_d / 2)
                .extrude(-(thickness + 2))
            )
            result = result.cut(hole)
        return result

    def _add_holes_vertical(self, result, params, count, arm_length, width, thickness,
                            hole_d, start_offset):
        if count <= 0 or hole_d >= thickness * 3:
            return result
        usable = arm_length - start_offset - 5
        if usable <= 0:
            return result
        spacing = usable / max(count, 1)
        for i in range(count):
            z = start_offset + spacing * (i + 0.5)
            if z + hole_d / 2 > arm_length - 2:
                continue
            hole = (
                cq.Workplane("XZ")
                .workplane(offset=width / 2)
                .center(thickness / 2, z)
                .circle(hole_d / 2)
                .extrude(-(width + 2))
            )
            result = result.cut(hole)
        return result
