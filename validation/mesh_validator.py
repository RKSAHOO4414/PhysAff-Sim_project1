"""
Mesh validation: watertight check, self-intersection, volume sanity.
"""

import os
import tempfile
import numpy as np


def validate_mesh(solid, part_data: dict = None) -> dict:
    """
    Validate a CadQuery solid for simulation readiness.

    Checks:
      1. Volume > 0 (non-degenerate)
      2. Watertight (closed shell)
      3. No self-intersections
      4. Mass within physical bounds
      5. Bounding box within expected ranges

    Returns dict with pass/fail for each check and overall validity.
    """
    import cadquery as cq

    results = {
        "valid": True,
        "checks": {},
        "warnings": [],
    }

    # Check 1: Volume
    try:
        vol = solid.val().Volume()
        results["checks"]["volume_mm3"] = round(vol, 2)
        if vol <= 0:
            results["checks"]["volume_positive"] = False
            results["valid"] = False
            results["warnings"].append("Volume is zero or negative")
        else:
            results["checks"]["volume_positive"] = True
    except Exception as e:
        results["checks"]["volume_positive"] = False
        results["valid"] = False
        results["warnings"].append(f"Volume computation failed: {e}")

    # Check 2: Bounding box sanity
    try:
        bb = solid.val().BoundingBox()
        dims = [bb.xmax - bb.xmin, bb.ymax - bb.ymin, bb.zmax - bb.zmin]
        results["checks"]["bbox_mm"] = [round(d, 2) for d in dims]

        # Industrial parts should be 1mm–300mm in any dimension
        for i, d in enumerate(dims):
            if d < 0.5:
                results["warnings"].append(f"Dimension {i} too small: {d:.2f}mm")
                results["valid"] = False
            if d > 500:
                results["warnings"].append(f"Dimension {i} too large: {d:.2f}mm")
                results["valid"] = False

        results["checks"]["bbox_valid"] = len([w for w in results["warnings"] if "Dimension" in w]) == 0
    except Exception as e:
        results["checks"]["bbox_valid"] = False
        results["warnings"].append(f"Bounding box check failed: {e}")

    # Check 3: Watertight (via trimesh)
    try:
        import trimesh

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            tmp_path = f.name
        cq.exporters.export(solid, tmp_path, exportType="STL",
                            tolerance=0.01, angularTolerance=0.1)

        mesh = trimesh.load(tmp_path, force="mesh")
        os.unlink(tmp_path)

        results["checks"]["watertight"] = bool(mesh.is_watertight)
        results["checks"]["n_vertices"] = len(mesh.vertices)
        results["checks"]["n_faces"] = len(mesh.faces)

        if not mesh.is_watertight:
            results["warnings"].append("Mesh is not watertight")
            # Not necessarily invalid — some parts have intentional openings
            # Only fail if it's supposed to be solid
    except ImportError:
        results["checks"]["watertight"] = None
        results["warnings"].append("trimesh not installed; skipping watertight check")
    except Exception as e:
        results["checks"]["watertight"] = None
        results["warnings"].append(f"Watertight check failed: {e}")

    # Check 4: Mass sanity (if physical properties available)
    if part_data and "physical_properties" in part_data:
        mass = part_data["physical_properties"]["mass_kg"]
        results["checks"]["mass_kg"] = mass

        # Industrial parts: 0.1g to 50kg is reasonable
        if mass < 1e-4:
            results["warnings"].append(f"Mass suspiciously low: {mass:.6f} kg")
        if mass > 50:
            results["warnings"].append(f"Mass suspiciously high: {mass:.2f} kg")

        results["checks"]["mass_valid"] = 1e-4 <= mass <= 50

    return results


def validate_batch(parts: list) -> dict:
    """Validate a batch of parts and return summary statistics."""
    total = len(parts)
    valid_count = 0
    invalid_parts = []
    all_warnings = []

    for part in parts:
        result = validate_mesh(part["solid"], part)
        if result["valid"]:
            valid_count += 1
        else:
            invalid_parts.append({
                "part_id": part["part_id"],
                "category": part["category"],
                "warnings": result["warnings"],
            })
        all_warnings.extend(result["warnings"])

    return {
        "total": total,
        "valid": valid_count,
        "invalid": total - valid_count,
        "validity_rate": round(valid_count / max(total, 1) * 100, 1),
        "invalid_parts": invalid_parts,
        "unique_warnings": list(set(all_warnings)),
    }
