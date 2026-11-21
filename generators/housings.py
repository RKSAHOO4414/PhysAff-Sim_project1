"""
Housing generator: open boxes, closed enclosures, enclosures with ports.
Produces 4,000 parts for PhysAff-Sim.
"""

import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import HOUSING_WALL_THICKNESS_RANGE, HOUSING_DIM_RANGE


class HousingGenerator(BaseGenerator):
    category = "housings"

    HOUSING_TYPES = ["open_box", "closed_box", "ported_enclosure"]
    HOUSING_WEIGHTS = [0.35, 0.30, 0.35]

    def sample_parameters(self) -> dict:
        housing_type = self.rng.choice(self.HOUSING_TYPES, p=self.HOUSING_WEIGHTS)
        material = self.sample_material()

        length = float(self.rng.uniform(*HOUSING_DIM_RANGE))
        width = float(self.rng.uniform(HOUSING_DIM_RANGE[0], length))  # width <= length
        height = float(self.rng.uniform(15.0, 100.0))
        wall_t = float(self.rng.uniform(*HOUSING_WALL_THICKNESS_RANGE))

        # Mounting holes: 0-4 on bottom
        n_mounting_holes = int(self.rng.integers(0, 5))
        mounting_hole_d = float(self.rng.uniform(2.5, 6.0))

        # Ports (for ported_enclosure): 0-3 on sides
        n_ports = int(self.rng.integers(1, 4)) if housing_type == "ported_enclosure" else 0
        port_diameter = float(self.rng.uniform(5.0, min(25.0, height * 0.6)))

        # Lid thickness (for closed_box)
        lid_thickness = float(self.rng.uniform(wall_t * 0.5, wall_t * 1.5)) if housing_type == "closed_box" else 0.0

        # Corner fillets
        corner_fillet = float(self.rng.uniform(0.0, min(wall_t * 2, 5.0)))

        # Flanges (mounting ears)
        has_flanges = bool(self.rng.random() < 0.4)
        flange_width = float(self.rng.uniform(8.0, 20.0)) if has_flanges else 0.0

        return {
            "housing_type": housing_type,
            "material": material,
            "length": round(length, 2),
            "width": round(width, 2),
            "height": round(height, 2),
            "wall_thickness": round(wall_t, 2),
            "n_mounting_holes": n_mounting_holes,
            "mounting_hole_diameter": round(mounting_hole_d, 2),
            "n_ports": n_ports,
            "port_diameter": round(port_diameter, 2),
            "lid_thickness": round(lid_thickness, 2),
            "corner_fillet": round(corner_fillet, 2),
            "has_flanges": has_flanges,
            "flange_width": round(flange_width, 2),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        ht = params["housing_type"]
        if ht == "open_box":
            return self._build_open_box(params)
        elif ht == "closed_box":
            return self._build_closed_box(params)
        elif ht == "ported_enclosure":
            return self._build_ported(params)
        raise ValueError(f"Unknown housing type: {ht}")

    def get_symmetry_group(self, params: dict) -> str:
        l, w = params["length"], params["width"]
        # If roughly square, C4 symmetry; if rectangular, C2
        if abs(l - w) / max(l, w) < 0.05:
            return "C4"
        return "C2"

    def _build_open_box(self, params: dict) -> cq.Workplane:
        l = params["length"]
        w = params["width"]
        h = params["height"]
        t = params["wall_thickness"]

        # Outer shell
        outer = cq.Workplane("XY").box(l, w, h)

        # Inner cavity (open top)
        inner = (
            cq.Workplane("XY")
            .workplane(offset=-h / 2 + t)  # start above bottom wall
            .box(l - 2 * t, w - 2 * t, h)  # taller than outer to cut through top
        )
        result = outer.cut(inner)

        # Corner fillets
        if params["corner_fillet"] > 0.1:
            try:
                result = result.edges("|Z").fillet(params["corner_fillet"])
            except Exception:
                pass

        # Mounting holes on bottom
        result = self._add_mounting_holes(result, params)

        # Flanges
        if params["has_flanges"]:
            result = self._add_flanges(result, params)

        return result

    def _build_closed_box(self, params: dict) -> cq.Workplane:
        l = params["length"]
        w = params["width"]
        h = params["height"]
        t = params["wall_thickness"]
        lid_t = params["lid_thickness"]

        # Outer shell
        total_h = h + lid_t
        outer = cq.Workplane("XY").box(l, w, total_h)

        # Inner cavity
        inner = (
            cq.Workplane("XY")
            .workplane(offset=-total_h / 2 + t)
            .box(l - 2 * t, w - 2 * t, h - t)
        )
        result = outer.cut(inner)

        # Mounting holes
        result = self._add_mounting_holes(result, params)

        if params["has_flanges"]:
            result = self._add_flanges(result, params)

        return result

    def _build_ported(self, params: dict) -> cq.Workplane:
        # Start with open box, then add port cutouts on sides
        result = self._build_open_box(params)

        l = params["length"]
        w = params["width"]
        h = params["height"]
        t = params["wall_thickness"]
        port_d = params["port_diameter"]

        # Add ports on the front face (+X side)
        for i in range(params["n_ports"]):
            port_z = float(self.rng.uniform(-h / 4, h / 4))
            port_y = float(self.rng.uniform(-w / 4, w / 4))

            port = (
                cq.Workplane("YZ")
                .workplane(offset=l / 2)
                .center(port_y, port_z)
                .circle(port_d / 2)
                .extrude(-(t + 2))
            )
            result = result.cut(port)

        return result

    def _add_mounting_holes(self, result, params):
        n = params["n_mounting_holes"]
        if n <= 0:
            return result

        l = params["length"]
        w = params["width"]
        h = params["height"]
        d = params["mounting_hole_diameter"]
        t = params["wall_thickness"]

        # Place holes near corners
        inset = max(d * 2, 8.0)
        positions = []
        if n >= 1:
            positions.append((-l / 2 + inset, -w / 2 + inset))
        if n >= 2:
            positions.append((l / 2 - inset, -w / 2 + inset))
        if n >= 3:
            positions.append((l / 2 - inset, w / 2 - inset))
        if n >= 4:
            positions.append((-l / 2 + inset, w / 2 - inset))

        for x, y in positions:
            hole = (
                cq.Workplane("XY")
                .workplane(offset=-h / 2 - 1)
                .center(x, y)
                .circle(d / 2)
                .extrude(t + 2)
            )
            result = result.cut(hole)

        return result

    def _add_flanges(self, result, params):
        l = params["length"]
        w = params["width"]
        h = params["height"]
        t = params["wall_thickness"]
        fw = params["flange_width"]

        # Two flanges on opposite sides (along length)
        for sign in [-1, 1]:
            flange = (
                cq.Workplane("XY")
                .workplane(offset=-h / 2)
                .center(0, sign * (w / 2 + fw / 2))
                .box(l * 0.6, fw, t)
            )
            result = result.union(flange)

            # Mounting hole in flange
            hole = (
                cq.Workplane("XY")
                .workplane(offset=-h / 2 - 1)
                .center(0, sign * (w / 2 + fw / 2))
                .circle(params["mounting_hole_diameter"] / 2)
                .extrude(t + 2)
            )
            result = result.cut(hole)

        return result
