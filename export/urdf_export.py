"""
URDF export for physics simulation (Isaac Sim / MuJoCo / PyBullet).
"""

import os
import xml.etree.ElementTree as ET
import xml.dom.minidom

from export.mesh_export import export_stl


def export_urdf(part_data: dict, output_dir: str, mesh_subdir: str = "meshes"):
    """
    Generate a URDF file for a single part.

    Args:
        part_data: dict from BaseGenerator.generate_one()
        output_dir: directory to write the URDF and mesh files
        mesh_subdir: subdirectory name for mesh files relative to URDF
    """
    part_id = part_data["part_id"]
    phys = part_data["physical_properties"]
    solid = part_data["solid"]

    # Ensure directories exist
    urdf_dir = os.path.join(output_dir, "urdf")
    mesh_dir = os.path.join(output_dir, mesh_subdir)
    os.makedirs(urdf_dir, exist_ok=True)
    os.makedirs(mesh_dir, exist_ok=True)

    # Export mesh for URDF
    mesh_filename = f"{part_id}.stl"
    mesh_path = os.path.join(mesh_dir, mesh_filename)
    export_stl(solid, mesh_path)

    # Build URDF XML
    robot = ET.Element("robot", name=part_id)

    # Single link
    link = ET.SubElement(robot, "link", name="base_link")

    # Inertial properties
    inertial = ET.SubElement(link, "inertial")

    mass = ET.SubElement(inertial, "mass", value=str(phys["mass_kg"]))

    com = phys["com_mm"]
    # Convert CoM from mm to meters for URDF
    origin = ET.SubElement(inertial, "origin",
                           xyz=f"{com[0] / 1000:.6f} {com[1] / 1000:.6f} {com[2] / 1000:.6f}",
                           rpy="0 0 0")

    inertia_data = phys["inertia_kg_m2"]
    ET.SubElement(inertial, "inertia",
                  ixx=str(inertia_data["ixx"]),
                  iyy=str(inertia_data["iyy"]),
                  izz=str(inertia_data["izz"]),
                  ixy=str(inertia_data["ixy"]),
                  ixz=str(inertia_data["ixz"]),
                  iyz=str(inertia_data["iyz"]))

    # Visual geometry
    visual = ET.SubElement(link, "visual")
    vis_geom = ET.SubElement(visual, "geometry")
    # Mesh path relative to URDF; scale mm -> m
    ET.SubElement(vis_geom, "mesh",
                  filename=f"../{mesh_subdir}/{mesh_filename}",
                  scale="0.001 0.001 0.001")

    # Collision geometry (same mesh)
    collision = ET.SubElement(link, "collision")
    col_geom = ET.SubElement(collision, "geometry")
    ET.SubElement(col_geom, "mesh",
                  filename=f"../{mesh_subdir}/{mesh_filename}",
                  scale="0.001 0.001 0.001")

    # Contact properties (Gazebo-style, also used by PyBullet)
    contact = ET.SubElement(collision, "contact")
    ET.SubElement(contact, "lateral_friction", value=str(phys["friction_mu"]))
    ET.SubElement(contact, "rolling_friction", value="0.001")
    ET.SubElement(contact, "restitution", value="0.1")

    # Write URDF file
    urdf_path = os.path.join(urdf_dir, f"{part_id}.urdf")
    xml_str = ET.tostring(robot, encoding="unicode")
    # Pretty print
    dom = xml.dom.minidom.parseString(xml_str)
    with open(urdf_path, "w") as f:
        f.write(dom.toprettyxml(indent="  "))

    return urdf_path


def export_usd(part_data: dict, output_dir: str):
    """
    Export part as USD file for NVIDIA Isaac Sim.
    Requires the `pxr` (OpenUSD) package.

    This is a placeholder — full USD export requires Isaac Sim SDK.
    For now, Isaac Sim can import URDF directly.
    """
    # Isaac Sim's URDF importer handles conversion to USD
    # This function is for future direct USD export
    urdf_path = export_urdf(part_data, output_dir)
    print(f"[USD] URDF exported to {urdf_path}. Use Isaac Sim URDF importer for USD conversion.")
    return urdf_path
