"""
Fastener generator: hex bolts, socket head cap screws, pan head, flat/countersunk, studs.
Produces 6,000 parts for PhysAff-Sim.
"""

import math
import numpy as np
import cadquery as cq

from .base import BaseGenerator
from config.iso_standards import ISO_BOLT_DIMS, M_SIZES, HEAD_TYPES


class FastenerGenerator(BaseGenerator):
    category = "fasteners"

    # Head type distribution (weighted toward hex and socket — most common industrially)
    HEAD_WEIGHTS = [0.30, 0.30, 0.15, 0.15, 0.10]  # hex, socket, pan, flat, stud

    def sample_parameters(self) -> dict:
        # M-size (weighted toward common industrial sizes M5-M12)
        size_weights = np.array([0.05, 0.08, 0.12, 0.15, 0.18, 0.15, 0.10, 0.07, 0.05, 0.03, 0.02])
        size_weights = size_weights / size_weights.sum()
        m_size = self.rng.choice(M_SIZES, p=size_weights)

        dims = ISO_BOLT_DIMS[m_size]
        shaft_d = dims["shaft_d"]

        # Head type
        head_type = self.rng.choice(HEAD_TYPES, p=self.HEAD_WEIGHTS)

        # Length: 10-100mm, biased toward 20-50mm range
        length = float(self.rng.uniform(max(10.0, shaft_d * 2), 100.0))

        # Thread length (portion of shaft that is threaded)
        # ISO 4014: thread_length = 2*d + 6 for L <= 125mm
        thread_length_std = min(2 * shaft_d + 6, length)
        thread_length = float(self.rng.uniform(thread_length_std * 0.8, min(thread_length_std * 1.2, length)))

        # Material
        material = self.sample_material()

        # Optional: chamfer on shaft end
        has_chamfer = bool(self.rng.random() < 0.7)
        chamfer_size = float(shaft_d * 0.1) if has_chamfer else 0.0

        # Optional: washer face under head (for hex bolts)
        has_washer_face = bool(self.rng.random() < 0.3) if head_type == "hex" else False
        washer_face_thickness = float(shaft_d * 0.05) if has_washer_face else 0.0

        return {
            "m_size": m_size,
            "head_type": head_type,
            "shaft_diameter": shaft_d,
            "length": round(length, 2),
            "thread_length": round(thread_length, 2),
            "material": material,
            "has_chamfer": has_chamfer,
            "chamfer_size": round(chamfer_size, 3),
            "has_washer_face": has_washer_face,
            "washer_face_thickness": round(washer_face_thickness, 3),
        }

    def build_shape(self, params: dict) -> cq.Workplane:
        head_type = params["head_type"]

        if head_type == "hex":
            return self._build_hex_bolt(params)
        elif head_type == "socket":
            return self._build_socket_head(params)
        elif head_type == "pan":
            return self._build_pan_head(params)
        elif head_type == "flat":
            return self._build_flat_head(params)
        elif head_type == "stud":
            return self._build_stud(params)
        else:
            raise ValueError(f"Unknown head type: {head_type}")

    def get_symmetry_group(self, params: dict) -> str:
        head_type = params["head_type"]
        if head_type == "stud":
            return "C_inf"  # cylindrical symmetry
        elif head_type in ("hex", "socket"):
            return "C6"  # 6-fold rotational symmetry
        elif head_type in ("pan", "flat"):
            return "C_inf"  # circular head = continuous rotational symmetry
        return "C1"

    # ------------------------------------------------------------------
    # Build methods for each head type
    # ------------------------------------------------------------------
    def _build_hex_bolt(self, params: dict) -> cq.Workplane:
        dims = ISO_BOLT_DIMS[params["m_size"]]
        shaft_d = params["shaft_diameter"]
        length = params["length"]
        hex_af = dims["hex_af"]  # across flats
        hex_h = dims["hex_h"]

        # Hex head: regular hexagonal prism
        # Across flats -> circumradius = af / sqrt(3)
        hex_cr = hex_af / math.sqrt(3)

        result = (
            cq.Workplane("XY")
            .polygon(6, hex_cr * 2)  # regular hexagon by circumradius diameter
            .extrude(hex_h)
        )

        # Washer face
        if params["has_washer_face"]:
            wf_t = params["washer_face_thickness"]
            washer = (
                cq.Workplane("XY")
                .circle(hex_af / 2 * 1.1)
                .extrude(wf_t)
                .translate((0, 0, -wf_t))
            )
            result = result.union(washer)
            shaft_start_z = -wf_t
        else:
            shaft_start_z = 0.0

        # Shaft (cylinder extending downward)
        shaft = (
            cq.Workplane("XY")
            .circle(shaft_d / 2)
            .extrude(-length)
            .translate((0, 0, shaft_start_z))
        )
        result = result.union(shaft)

        # Chamfer on shaft tip
        if params["has_chamfer"] and params["chamfer_size"] > 0:
            try:
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, shaft_start_z - length))
                ).chamfer(params["chamfer_size"])
            except Exception:
                pass  # Skip chamfer if geometry fails

        return result

    def _build_socket_head(self, params: dict) -> cq.Workplane:
        dims = ISO_BOLT_DIMS[params["m_size"]]
        shaft_d = params["shaft_diameter"]
        length = params["length"]
        socket_d = dims["socket_d"]
        socket_h = dims["socket_h"]
        socket_hex = dims["socket_hex"]

        # Cylindrical head
        result = (
            cq.Workplane("XY")
            .circle(socket_d / 2)
            .extrude(socket_h)
        )

        # Hex socket recess in top of head
        hex_cr = socket_hex / math.sqrt(3)
        socket_depth = socket_h * 0.6
        recess = (
            cq.Workplane("XY")
            .workplane(offset=socket_h)
            .polygon(6, hex_cr * 2)
            .extrude(-socket_depth)
        )
        result = result.cut(recess)

        # Shaft
        shaft = (
            cq.Workplane("XY")
            .circle(shaft_d / 2)
            .extrude(-length)
        )
        result = result.union(shaft)

        # Chamfer
        if params["has_chamfer"] and params["chamfer_size"] > 0:
            try:
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, -length))
                ).chamfer(params["chamfer_size"])
            except Exception:
                pass

        return result

    def _build_pan_head(self, params: dict) -> cq.Workplane:
        dims = ISO_BOLT_DIMS[params["m_size"]]
        shaft_d = params["shaft_diameter"]
        length = params["length"]
        pan_d = dims["pan_d"]
        pan_h = dims["pan_h"]

        # Pan head: low cylinder with rounded top edge
        result = (
            cq.Workplane("XY")
            .circle(pan_d / 2)
            .extrude(pan_h)
        )

        # Fillet on top edge for the dome shape
        fillet_r = min(pan_h * 0.3, pan_d * 0.05)
        if fillet_r > 0.1:
            try:
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, pan_h))
                ).fillet(fillet_r)
            except Exception:
                pass

        # Cross slot on top (simplified as two perpendicular cuts)
        slot_w = shaft_d * 0.15
        slot_depth = pan_h * 0.4
        slot1 = (
            cq.Workplane("XY")
            .workplane(offset=pan_h - slot_depth)
            .box(pan_d * 0.8, slot_w, slot_depth + 0.1)
        )
        slot2 = (
            cq.Workplane("XY")
            .workplane(offset=pan_h - slot_depth)
            .box(slot_w, pan_d * 0.8, slot_depth + 0.1)
        )
        result = result.cut(slot1).cut(slot2)

        # Shaft
        shaft = (
            cq.Workplane("XY")
            .circle(shaft_d / 2)
            .extrude(-length)
        )
        result = result.union(shaft)

        return result

    def _build_flat_head(self, params: dict) -> cq.Workplane:
        dims = ISO_BOLT_DIMS[params["m_size"]]
        shaft_d = params["shaft_diameter"]
        length = params["length"]
        flat_d = dims["flat_d"]
        flat_h = dims["flat_h"]

        # Countersunk head: truncated cone (wider at top, narrows to shaft diameter)
        # Build as a revolved profile
        half_top = flat_d / 2
        half_bot = shaft_d / 2

        result = (
            cq.Workplane("XZ")
            .moveTo(0, 0)
            .lineTo(half_bot, 0)
            .lineTo(half_top, flat_h)
            .lineTo(0, flat_h)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        # Shaft
        shaft = (
            cq.Workplane("XY")
            .circle(shaft_d / 2)
            .extrude(-length)
        )
        result = result.union(shaft)

        # Chamfer
        if params["has_chamfer"] and params["chamfer_size"] > 0:
            try:
                result = result.edges(
                    cq.selectors.NearestToPointSelector((0, 0, -length))
                ).chamfer(params["chamfer_size"])
            except Exception:
                pass

        return result

    def _build_stud(self, params: dict) -> cq.Workplane:
        shaft_d = params["shaft_diameter"]
        length = params["length"]

        # Stud: simple cylinder (threaded rod, no head)
        # Total length includes both threaded ends
        result = (
            cq.Workplane("XY")
            .circle(shaft_d / 2)
            .extrude(length)
        )

        # Chamfer both ends
        if params["has_chamfer"] and params["chamfer_size"] > 0:
            try:
                result = result.edges("%CIRCLE").chamfer(params["chamfer_size"])
            except Exception:
                pass

        return result
