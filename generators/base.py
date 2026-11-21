"""
Base generator class for all PhysAff-Sim part categories.
Every category generator inherits from this and implements:
  - sample_parameters() -> dict
  - build_shape(params) -> cadquery.Workplane
  - get_symmetry_group(params) -> str
"""

import abc
import hashlib
import json
import math
import numpy as np
import cadquery as cq

from config.iso_standards import MATERIALS, MATERIAL_DENSITIES, FRICTION_COEFFICIENTS


class BaseGenerator(abc.ABC):
    """Abstract base for procedural part generators."""

    category: str = ""  # Override in subclass

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def reseed(self, seed: int):
        """Reset RNG with a new seed for reproducibility."""
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Abstract methods — every category MUST implement these
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def sample_parameters(self) -> dict:
        """Sample a random parameter dict for one part."""
        ...

    @abc.abstractmethod
    def build_shape(self, params: dict) -> cq.Workplane:
        """Build and return a CadQuery Workplane solid from params."""
        ...

    @abc.abstractmethod
    def get_symmetry_group(self, params: dict) -> str:
        """Return symmetry group string, e.g. 'C_inf', 'C6', 'C1'."""
        ...

    # ------------------------------------------------------------------
    # Common methods
    # ------------------------------------------------------------------
    def sample_material(self) -> str:
        """Sample a material with weighted probabilities (steel most common)."""
        weights = [0.50, 0.25, 0.15, 0.10]  # steel, aluminum, brass, plastic
        return self.rng.choice(MATERIALS, p=weights)

    def compute_physical_properties(self, solid: cq.Workplane, material: str) -> dict:
        """Compute mass, CoM, inertia tensor, friction from a CadQuery solid."""
        # Volume in mm^3 from CadQuery
        vol_mm3 = solid.val().Volume()
        vol_m3 = vol_mm3 * 1e-9  # convert to m^3

        density = MATERIAL_DENSITIES[material]
        mass = density * vol_m3  # kg

        # Center of mass from CadQuery (in mm)
        com = solid.val().Center()
        com_mm = [com.x, com.y, com.z]

        # Bounding box for approximate inertia
        bb = solid.val().BoundingBox()
        lx = (bb.xmax - bb.xmin) * 1e-3  # m
        ly = (bb.ymax - bb.ymin) * 1e-3
        lz = (bb.zmax - bb.zmin) * 1e-3

        # Approximate inertia as a solid rectangular box (conservative)
        ixx = (mass / 12.0) * (ly**2 + lz**2)
        iyy = (mass / 12.0) * (lx**2 + lz**2)
        izz = (mass / 12.0) * (lx**2 + ly**2)

        # Friction
        mu_range = FRICTION_COEFFICIENTS[material]
        mu = float(self.rng.uniform(mu_range[0], mu_range[1]))

        return {
            "mass_kg": round(mass, 6),
            "volume_mm3": round(vol_mm3, 2),
            "com_mm": [round(c, 3) for c in com_mm],
            "inertia_kg_m2": {
                "ixx": round(ixx, 9),
                "iyy": round(iyy, 9),
                "izz": round(izz, 9),
                "ixy": 0.0, "ixz": 0.0, "iyz": 0.0,
            },
            "friction_mu": round(mu, 3),
            "material": material,
            "density_kg_m3": density,
        }

    def compute_bounding_box(self, solid: cq.Workplane) -> dict:
        """Return bounding box dimensions in mm."""
        bb = solid.val().BoundingBox()
        return {
            "min": [round(bb.xmin, 3), round(bb.ymin, 3), round(bb.zmin, 3)],
            "max": [round(bb.xmax, 3), round(bb.ymax, 3), round(bb.zmax, 3)],
            "size": [
                round(bb.xmax - bb.xmin, 3),
                round(bb.ymax - bb.ymin, 3),
                round(bb.zmax - bb.zmin, 3),
            ],
        }

    def generate_part_id(self, params: dict) -> str:
        """Deterministic part ID from parameters."""
        param_str = json.dumps(params, sort_keys=True, default=str)
        h = hashlib.sha256(param_str.encode()).hexdigest()[:12]
        return f"{self.category}_{h}"

    def generate_one(self, index: int = 0) -> dict:
        """
        Generate a single part: sample params, build geometry, compute physics.

        Returns a dict with:
          - part_id: unique identifier
          - category: part category string
          - params: sampled parameters
          - solid: CadQuery Workplane (for export)
          - physical_properties: mass, CoM, inertia, friction
          - bounding_box: min/max/size in mm
          - symmetry_group: symmetry annotation
        """
        params = self.sample_parameters()
        params["_index"] = index

        solid = self.build_shape(params)
        material = params.get("material", "steel")
        phys = self.compute_physical_properties(solid, material)
        bbox = self.compute_bounding_box(solid)
        sym = self.get_symmetry_group(params)
        part_id = self.generate_part_id(params)

        return {
            "part_id": part_id,
            "category": self.category,
            "params": params,
            "solid": solid,
            "physical_properties": phys,
            "bounding_box": bbox,
            "symmetry_group": sym,
        }

    def generate_batch(self, count: int, start_index: int = 0) -> list:
        """Generate a batch of parts."""
        parts = []
        for i in range(count):
            part = self.generate_one(index=start_index + i)
            parts.append(part)
        return parts
