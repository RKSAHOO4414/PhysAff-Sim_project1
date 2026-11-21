"""
Connector & Fitting generator: straight pipes, elbows, T-fittings, flange adapters.
Produces 3,500 parts for PhysAff-Sim.
"""

import math
import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import CONNECTOR_PORT_RANGE, CONNECTOR_WALL_RANGE


class ConnectorGenerator(BaseGenerator):
    category = "connectors"

    CONNECTOR_TYPES = ["straight_pipe", "elbow", "t_fitting", "flange_adapter"]
    CONNECTOR_WEIGHTS = [0.20, 0.30, 0.25, 0.25]

    def sample_parameters(self) -> dict:
        conn_type = self.rng.choice(self.CONNECTOR_TYPES, p=self.CONNECTOR_WEIGHTS)
        material = self.sample_material()

        inner_d = float(self.rng.uniform(*CONNECTOR_PORT_RANGE))
        wall_t = float(self.rng.uniform(*CONNECTOR_WALL_RANGE))
        outer_d = inner_d + 2 * wall_t
        length = float(self.rng.uniform(20.0, 100.0))

        # Bend angle for elbow (45° or 90° are standard, with variation)
        if conn_type == "elbow":
            base_angle = self.rng.choice([45.0, 90.0], p=[0.3, 0.7])
            bend_angle = float(base_angle + self.rng.uniform(-5.0, 5.0))
            bend_radius = float(outer_d * self.rng.uniform(1.5, 3.0))
        else:
            bend_angle = 0.0
            bend_radius = 0.0

        # Flange properties
        if conn_type == "flange_adapter":
            flange_d = float(outer_d * self.rng.uniform(1.8, 3.0))
            flange_t = float(self.rng.uniform(3.0, 10.0))
            n_flange_holes = int(self.rng.choice([4, 6, 8]))
            flange_hole_d = float(self.rng.uniform(3.0, 8.0))
        else:
            flange_d = 0.0
            flange_t = 0.0
            n_flange_holes = 0
            flange_hole_d = 0.0

        # T-fitting branch diameter
        if conn_type == "t_fitting":
            branch_inner_d = float(inner_d * self.rng.uniform(0.5, 1.0))
            branch_wall_t = wall_t
            branch_length = float(length * self.rng.uniform(0.4, 0.8))
        else:
            branch_inner_d = 0.0
            branch_wall_t = 0.0
            branch_length = 0.0

        # Bevel on pipe ends
        has_bevel = bool(self.rng.random() < 0.5)
        bevel_angle = float(self.rng.uniform(15.0, 45.0)) if has_bevel else 0.0

        return {
            "connector_type": conn_type,
            "material": material,
            "inner_diameter": round(inner_d, 2),
            "wall_thickness": round(wall_t, 2),
            "outer_diameter": round(outer_d, 2),
            "length": round(length, 2),
            "bend_angle": round(bend_angle, 2),
            "bend_radius": round(bend_radius, 2),
            "flange_diameter": round(flange_d, 2),
            "flange_thickness": round(flange_t, 2),
            "n_flange_holes": n_flange_holes,
            "flange_hole_diameter": round(flange_hole_d, 2),
            "branch_inner_diameter": round(branch_inner_d, 2),
            "branch_wall_thickness": round(branch_wall_t, 2),
            "branch_length": round(branch_length, 2),
            "has_bevel": has_bevel,
            "bevel_angle": round(bevel_angle, 2),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        ct = params["connector_type"]
        if ct == "straight_pipe":
            return self._build_straight(params)
        elif ct == "elbow":
            return self._build_elbow(params)
        elif ct == "t_fitting":
            return self._build_t_fitting(params)
        elif ct == "flange_adapter":
            return self._build_flange(params)
        raise ValueError(f"Unknown connector type: {ct}")

    def get_symmetry_group(self, params: dict) -> str:
        ct = params["connector_type"]
        if ct == "straight_pipe":
            return "C_inf"
        elif ct == "elbow":
            return "C1"  # elbow has a bend plane
        elif ct == "t_fitting":
            return "C2"  # mirror across the branch plane
        elif ct == "flange_adapter":
            n = params["n_flange_holes"]
            return f"C{n}"  # rotational symmetry from bolt holes
        return "C1"

    def _build_straight(self, params: dict) -> cq.Workplane:
        od = params["outer_diameter"]
        id_ = params["inner_diameter"]
        l = params["length"]

        # Outer cylinder
        result = (
            cq.Workplane("XY")
            .circle(od / 2)
            .circle(id_ / 2)  # inner hole
            .extrude(l)
        )

        return result

    def _build_elbow(self, params: dict) -> cq.Workplane:
        od = params["outer_diameter"]
        id_ = params["inner_diameter"]
        angle = params["bend_angle"]
        br = params["bend_radius"]

        # Create elbow by sweeping a ring profile along a circular arc
        # Profile: annular ring (outer - inner)
        path = (
            cq.Workplane("XZ")
            .center(br, 0)
            .radiusArc((br * (1 - math.cos(math.radians(angle))),
                        br * math.sin(math.radians(angle))),
                       -br)
        )

        # For simplicity, build as two straight pipe segments at an angle
        seg_length = br * math.tan(math.radians(angle / 2))
        seg_length = max(seg_length, od)

        # Segment 1: along Z
        seg1 = (
            cq.Workplane("XY")
            .circle(od / 2)
            .circle(id_ / 2)
            .extrude(seg_length)
        )

        # Segment 2: rotated by bend_angle
        seg2 = (
            cq.Workplane("XY")
            .circle(od / 2)
            .circle(id_ / 2)
            .extrude(seg_length)
            .rotate((0, 0, 0), (0, 1, 0), angle)
            .translate((0, 0, seg_length))
        )

        # Junction block to fill the bend area
        junction = (
            cq.Workplane("XY")
            .workplane(offset=seg_length * 0.7)
            .sphere(od / 2 * 1.3)
        )

        result = seg1.union(seg2).union(junction)

        # Cut through-hole
        hole1 = (
            cq.Workplane("XY")
            .circle(id_ / 2)
            .extrude(seg_length * 1.1)
        )
        hole2 = (
            cq.Workplane("XY")
            .circle(id_ / 2)
            .extrude(seg_length * 1.1)
            .rotate((0, 0, 0), (0, 1, 0), angle)
            .translate((0, 0, seg_length))
        )
        result = result.cut(hole1).cut(hole2)

        return result

    def _build_t_fitting(self, params: dict) -> cq.Workplane:
        od = params["outer_diameter"]
        id_ = params["inner_diameter"]
        l = params["length"]
        bid = params["branch_inner_diameter"]
        bwt = params["branch_wall_thickness"]
        bl = params["branch_length"]
        bod = bid + 2 * bwt

        # Main pipe along Z
        main = (
            cq.Workplane("XY")
            .circle(od / 2)
            .circle(id_ / 2)
            .extrude(l)
        )

        # Branch pipe along +X, centered at Z = l/2
        branch_outer = (
            cq.Workplane("YZ")
            .workplane(offset=od / 2)
            .circle(bod / 2)
            .extrude(bl - od / 2)
        )
        branch_outer = branch_outer.translate((0, 0, l / 2))

        result = main.union(branch_outer)

        # Branch inner bore
        branch_hole = (
            cq.Workplane("YZ")
            .workplane(offset=-1)
            .center(0, l / 2)
            .circle(bid / 2)
            .extrude(od / 2 + bl + 2)
        )
        result = result.cut(branch_hole)

        return result

    def _build_flange(self, params: dict) -> cq.Workplane:
        od = params["outer_diameter"]
        id_ = params["inner_diameter"]
        l = params["length"]
        fd = params["flange_diameter"]
        ft = params["flange_thickness"]
        n_holes = params["n_flange_holes"]
        hd = params["flange_hole_diameter"]

        # Pipe section
        pipe = (
            cq.Workplane("XY")
            .circle(od / 2)
            .circle(id_ / 2)
            .extrude(l)
        )

        # Flange disk at z=0
        flange = (
            cq.Workplane("XY")
            .workplane(offset=-ft)
            .circle(fd / 2)
            .circle(id_ / 2)
            .extrude(ft)
        )

        result = pipe.union(flange)

        # Bolt holes in flange (arranged in a circle)
        bolt_circle_d = (fd + od) / 2
        for i in range(n_holes):
            angle = 2 * math.pi * i / n_holes
            hx = bolt_circle_d / 2 * math.cos(angle)
            hy = bolt_circle_d / 2 * math.sin(angle)
            hole = (
                cq.Workplane("XY")
                .workplane(offset=-ft - 1)
                .center(hx, hy)
                .circle(hd / 2)
                .extrude(ft + 2)
            )
            result = result.cut(hole)

        return result
