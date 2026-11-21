"""
Plate & Flat Stock generator: plates with hole patterns, slots, cutouts.
Produces 3,500 parts for PhysAff-Sim.
"""

import math
import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import PLATE_DIM_RANGE, PLATE_THICKNESS_RANGE


class PlateGenerator(BaseGenerator):
    category = "plates"

    PLATE_TYPES = ["hole_pattern", "slotted", "cutout", "multi_feature"]
    PLATE_WEIGHTS = [0.30, 0.25, 0.20, 0.25]

    def sample_parameters(self) -> dict:
        plate_type = self.rng.choice(self.PLATE_TYPES, p=self.PLATE_WEIGHTS)
        material = self.sample_material()

        length = float(self.rng.uniform(*PLATE_DIM_RANGE))
        width = float(self.rng.uniform(PLATE_DIM_RANGE[0], length))
        thickness = float(self.rng.uniform(*PLATE_THICKNESS_RANGE))

        # Corner style
        corner_style = self.rng.choice(["sharp", "rounded", "chamfered"], p=[0.4, 0.4, 0.2])
        corner_radius = float(self.rng.uniform(2.0, min(10.0, min(length, width) * 0.15))) if corner_style == "rounded" else 0.0
        corner_chamfer = float(self.rng.uniform(2.0, min(8.0, min(length, width) * 0.1))) if corner_style == "chamfered" else 0.0

        # Holes
        n_holes = int(self.rng.integers(0, 13))  # 0-12 holes
        hole_diameter = float(self.rng.uniform(2.5, min(12.0, min(length, width) * 0.15)))
        hole_pattern = self.rng.choice(["grid", "perimeter", "random"])

        # Slots (for slotted and multi_feature)
        n_slots = int(self.rng.integers(1, 5)) if plate_type in ("slotted", "multi_feature") else 0
        slot_width = float(self.rng.uniform(3.0, min(15.0, width * 0.2)))
        slot_length = float(self.rng.uniform(10.0, min(60.0, length * 0.5)))

        # Cutouts (for cutout and multi_feature)
        n_cutouts = int(self.rng.integers(1, 4)) if plate_type in ("cutout", "multi_feature") else 0
        cutout_type = self.rng.choice(["rectangular", "circular"])
        cutout_size = float(self.rng.uniform(10.0, min(40.0, min(length, width) * 0.4)))

        # Countersink on holes
        has_countersink = bool(self.rng.random() < 0.3)
        countersink_d = float(hole_diameter * 1.8) if has_countersink else 0.0
        countersink_depth = float(thickness * 0.3) if has_countersink else 0.0

        return {
            "plate_type": plate_type,
            "material": material,
            "length": round(length, 2),
            "width": round(width, 2),
            "thickness": round(thickness, 2),
            "corner_style": corner_style,
            "corner_radius": round(corner_radius, 2),
            "corner_chamfer": round(corner_chamfer, 2),
            "n_holes": n_holes,
            "hole_diameter": round(hole_diameter, 2),
            "hole_pattern": hole_pattern,
            "n_slots": n_slots,
            "slot_width": round(slot_width, 2),
            "slot_length": round(slot_length, 2),
            "n_cutouts": n_cutouts,
            "cutout_type": cutout_type,
            "cutout_size": round(cutout_size, 2),
            "has_countersink": has_countersink,
            "countersink_diameter": round(countersink_d, 2),
            "countersink_depth": round(countersink_depth, 2),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        l = params["length"]
        w = params["width"]
        t = params["thickness"]

        # Base plate
        result = cq.Workplane("XY").box(l, w, t)

        # Corner treatment
        if params["corner_style"] == "rounded" and params["corner_radius"] > 0.1:
            try:
                result = result.edges("|Z").fillet(params["corner_radius"])
            except Exception:
                pass
        elif params["corner_style"] == "chamfered" and params["corner_chamfer"] > 0.1:
            try:
                result = result.edges("|Z").chamfer(params["corner_chamfer"])
            except Exception:
                pass

        # Add holes
        if params["n_holes"] > 0:
            result = self._add_holes(result, params)

        # Add slots
        if params["n_slots"] > 0:
            result = self._add_slots(result, params)

        # Add cutouts
        if params["n_cutouts"] > 0:
            result = self._add_cutouts(result, params)

        return result

    def get_symmetry_group(self, params: dict) -> str:
        l, w = params["length"], params["width"]
        if abs(l - w) / max(l, w) < 0.05 and params["n_holes"] == 0 and params["n_slots"] == 0:
            return "C4"
        elif params["n_holes"] == 0 and params["n_slots"] == 0:
            return "C2"
        return "C1"

    def _add_holes(self, result, params):
        l = params["length"]
        w = params["width"]
        t = params["thickness"]
        n = params["n_holes"]
        d = params["hole_diameter"]
        pattern = params["hole_pattern"]

        margin = max(d * 1.5, 5.0)
        positions = []

        if pattern == "grid":
            # Arrange in a grid
            n_cols = max(1, int(math.sqrt(n * l / w)))
            n_rows = max(1, int(math.ceil(n / n_cols)))
            x_spacing = (l - 2 * margin) / max(n_cols - 1, 1) if n_cols > 1 else 0
            y_spacing = (w - 2 * margin) / max(n_rows - 1, 1) if n_rows > 1 else 0
            count = 0
            for r in range(n_rows):
                for c in range(n_cols):
                    if count >= n:
                        break
                    x = -l / 2 + margin + c * x_spacing
                    y = -w / 2 + margin + r * y_spacing
                    positions.append((x, y))
                    count += 1

        elif pattern == "perimeter":
            # Holes along the edge
            spacing = 2 * (l + w - 4 * margin) / max(n, 1)
            perimeter_pts = []
            # Bottom edge
            for x in np.linspace(-l / 2 + margin, l / 2 - margin, max(n // 4, 1)):
                perimeter_pts.append((x, -w / 2 + margin))
            # Right edge
            for y in np.linspace(-w / 2 + margin, w / 2 - margin, max(n // 4, 1)):
                perimeter_pts.append((l / 2 - margin, y))
            # Top edge
            for x in np.linspace(l / 2 - margin, -l / 2 + margin, max(n // 4, 1)):
                perimeter_pts.append((x, w / 2 - margin))
            # Left edge
            for y in np.linspace(w / 2 - margin, -w / 2 + margin, max(n // 4, 1)):
                perimeter_pts.append((-l / 2 + margin, y))
            positions = perimeter_pts[:n]

        else:  # random
            for _ in range(n):
                x = float(self.rng.uniform(-l / 2 + margin, l / 2 - margin))
                y = float(self.rng.uniform(-w / 2 + margin, w / 2 - margin))
                positions.append((x, y))

        for x, y in positions:
            hole = (
                cq.Workplane("XY")
                .workplane(offset=t / 2 + 1)
                .center(x, y)
                .circle(d / 2)
                .extrude(-(t + 2))
            )
            result = result.cut(hole)

            # Countersink
            if params["has_countersink"]:
                cs = (
                    cq.Workplane("XY")
                    .workplane(offset=t / 2)
                    .center(x, y)
                    .circle(params["countersink_diameter"] / 2)
                    .extrude(-params["countersink_depth"])
                )
                result = result.cut(cs)

        return result

    def _add_slots(self, result, params):
        l = params["length"]
        w = params["width"]
        t = params["thickness"]
        n = params["n_slots"]
        sw = params["slot_width"]
        sl = params["slot_length"]

        margin = max(sw * 2, 10.0)

        for i in range(n):
            # Place slots with some spacing
            x = float(self.rng.uniform(-l / 2 + margin, l / 2 - margin - sl))
            y = float(self.rng.uniform(-w / 2 + margin, w / 2 - margin))

            # Slot = rectangle with semicircular ends
            slot = (
                cq.Workplane("XY")
                .workplane(offset=t / 2 + 1)
                .center(x + sl / 2, y)
                .slot2D(sl, sw)
                .extrude(-(t + 2))
            )
            result = result.cut(slot)

        return result

    def _add_cutouts(self, result, params):
        l = params["length"]
        w = params["width"]
        t = params["thickness"]
        n = params["n_cutouts"]
        ct = params["cutout_type"]
        cs = params["cutout_size"]

        margin = max(cs, 15.0)

        for i in range(n):
            x = float(self.rng.uniform(-l / 2 + margin, l / 2 - margin))
            y = float(self.rng.uniform(-w / 2 + margin, w / 2 - margin))

            if ct == "rectangular":
                h_size = float(cs * self.rng.uniform(0.5, 1.5))
                cutout = (
                    cq.Workplane("XY")
                    .workplane(offset=t / 2 + 1)
                    .center(x, y)
                    .rect(cs, h_size)
                    .extrude(-(t + 2))
                )
            else:  # circular
                cutout = (
                    cq.Workplane("XY")
                    .workplane(offset=t / 2 + 1)
                    .center(x, y)
                    .circle(cs / 2)
                    .extrude(-(t + 2))
                )
            result = result.cut(cutout)

        return result
