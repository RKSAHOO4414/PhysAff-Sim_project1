"""
Mesh export utilities: STL, STEP, and point cloud sampling.
"""

import os
import numpy as np
import cadquery as cq


def export_stl(solid: cq.Workplane, filepath: str, tolerance: float = 0.01,
               angular_tolerance: float = 0.1):
    """Export CadQuery solid to STL file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cq.exporters.export(solid, filepath, exportType="STL",
                        tolerance=tolerance, angularTolerance=angular_tolerance)


def export_step(solid: cq.Workplane, filepath: str):
    """Export CadQuery solid to STEP file (preserves exact geometry)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cq.exporters.export(solid, filepath, exportType="STEP")


def sample_point_cloud(solid: cq.Workplane, n_points: int = 10000,
                       seed: int = 42) -> dict:
    """
    Sample a point cloud from a CadQuery solid surface.

    Returns dict with:
      - points: (N, 3) array of XYZ coordinates in mm
      - normals: (N, 3) array of estimated surface normals
    """
    try:
        import trimesh

        # Export to temporary STL and load with trimesh
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            tmp_path = f.name
        export_stl(solid, tmp_path, tolerance=0.005, angular_tolerance=0.05)

        mesh = trimesh.load(tmp_path, force="mesh")
        os.unlink(tmp_path)

        # Sample points on the surface
        points, face_indices = mesh.sample(n_points, return_index=True)

        # Get face normals for each sampled point
        normals = mesh.face_normals[face_indices]

        return {
            "points": points.astype(np.float32),
            "normals": normals.astype(np.float32),
            "n_points": len(points),
            "mesh_vertices": len(mesh.vertices),
            "mesh_faces": len(mesh.faces),
        }

    except ImportError:
        # Fallback: simple bounding-box-based sampling (not on surface)
        bb = solid.val().BoundingBox()
        rng = np.random.default_rng(seed)
        points = rng.uniform(
            [bb.xmin, bb.ymin, bb.zmin],
            [bb.xmax, bb.ymax, bb.zmax],
            size=(n_points * 3, 3),  # oversample then filter
        )
        # Very rough — only for testing without trimesh
        return {
            "points": points[:n_points].astype(np.float32),
            "normals": np.zeros((n_points, 3), dtype=np.float32),
            "n_points": n_points,
            "mesh_vertices": 0,
            "mesh_faces": 0,
        }


def save_point_cloud(pc_data: dict, filepath: str):
    """Save point cloud as compressed .npz file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.savez_compressed(
        filepath,
        points=pc_data["points"],
        normals=pc_data["normals"],
    )


def load_point_cloud(filepath: str) -> dict:
    """Load point cloud from .npz file."""
    data = np.load(filepath)
    return {
        "points": data["points"],
        "normals": data["normals"],
    }
