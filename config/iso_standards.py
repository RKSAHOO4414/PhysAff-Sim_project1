"""
ISO metric standards and material properties for PhysAff-Sim.
All dimensions in millimeters, masses in kilograms.
"""

# ============================================================================
# ISO 4014/4017 Hex Bolt Dimensions (mm)
# Key: M-size -> {pitch, head_across_flats, head_height, washer_dia}
# ============================================================================
ISO_BOLT_DIMS = {
    "M3":  {"pitch": 0.5,  "shaft_d": 3.0,  "hex_af": 5.5,   "hex_h": 2.0,  "socket_d": 5.5,  "socket_h": 3.0,  "socket_hex": 2.5,  "pan_d": 6.0,   "pan_h": 2.1,  "flat_d": 6.0,   "flat_h": 1.7,  "flat_angle": 90},
    "M4":  {"pitch": 0.7,  "shaft_d": 4.0,  "hex_af": 7.0,   "hex_h": 2.8,  "socket_d": 7.0,  "socket_h": 4.0,  "socket_hex": 3.0,  "pan_d": 8.0,   "pan_h": 2.6,  "flat_d": 8.0,   "flat_h": 2.3,  "flat_angle": 90},
    "M5":  {"pitch": 0.8,  "shaft_d": 5.0,  "hex_af": 8.0,   "hex_h": 3.5,  "socket_d": 8.5,  "socket_h": 5.0,  "socket_hex": 4.0,  "pan_d": 10.0,  "pan_h": 3.3,  "flat_d": 10.0,  "flat_h": 2.8,  "flat_angle": 90},
    "M6":  {"pitch": 1.0,  "shaft_d": 6.0,  "hex_af": 10.0,  "hex_h": 4.0,  "socket_d": 10.0, "socket_h": 6.0,  "socket_hex": 5.0,  "pan_d": 12.0,  "pan_h": 3.9,  "flat_d": 12.0,  "flat_h": 3.3,  "flat_angle": 90},
    "M8":  {"pitch": 1.25, "shaft_d": 8.0,  "hex_af": 13.0,  "hex_h": 5.3,  "socket_d": 13.0, "socket_h": 8.0,  "socket_hex": 6.0,  "pan_d": 16.0,  "pan_h": 5.0,  "flat_d": 16.0,  "flat_h": 4.4,  "flat_angle": 90},
    "M10": {"pitch": 1.5,  "shaft_d": 10.0, "hex_af": 17.0,  "hex_h": 6.4,  "socket_d": 16.0, "socket_h": 10.0, "socket_hex": 8.0,  "pan_d": 20.0,  "pan_h": 6.5,  "flat_d": 20.0,  "flat_h": 5.5,  "flat_angle": 90},
    "M12": {"pitch": 1.75, "shaft_d": 12.0, "hex_af": 19.0,  "hex_h": 7.5,  "socket_d": 18.0, "socket_h": 12.0, "socket_hex": 10.0, "pan_d": 24.0,  "pan_h": 7.5,  "flat_d": 24.0,  "flat_h": 6.5,  "flat_angle": 90},
    "M14": {"pitch": 2.0,  "shaft_d": 14.0, "hex_af": 22.0,  "hex_h": 8.8,  "socket_d": 21.0, "socket_h": 14.0, "socket_hex": 12.0, "pan_d": 28.0,  "pan_h": 8.5,  "flat_d": 28.0,  "flat_h": 7.5,  "flat_angle": 90},
    "M16": {"pitch": 2.0,  "shaft_d": 16.0, "hex_af": 24.0,  "hex_h": 10.0, "socket_d": 24.0, "socket_h": 16.0, "socket_hex": 14.0, "pan_d": 32.0,  "pan_h": 10.0, "flat_d": 32.0,  "flat_h": 8.8,  "flat_angle": 90},
    "M18": {"pitch": 2.5,  "shaft_d": 18.0, "hex_af": 27.0,  "hex_h": 11.5, "socket_d": 27.0, "socket_h": 18.0, "socket_hex": 14.0, "pan_d": 36.0,  "pan_h": 11.0, "flat_d": 36.0,  "flat_h": 10.0, "flat_angle": 90},
    "M20": {"pitch": 2.5,  "shaft_d": 20.0, "hex_af": 30.0,  "hex_h": 12.5, "socket_d": 30.0, "socket_h": 20.0, "socket_hex": 17.0, "pan_d": 40.0,  "pan_h": 12.5, "flat_d": 40.0,  "flat_h": 11.0, "flat_angle": 90},
}

# Available M-sizes for sampling
M_SIZES = list(ISO_BOLT_DIMS.keys())

# Head types for fasteners
HEAD_TYPES = ["hex", "socket", "pan", "flat", "stud"]

# ============================================================================
# Material Properties
# ============================================================================
MATERIALS = ["steel", "aluminum", "brass", "plastic"]

# Density in kg/m^3
MATERIAL_DENSITIES = {
    "steel":    7850.0,
    "aluminum": 2700.0,
    "brass":    8500.0,
    "plastic":  1200.0,
}

# Friction coefficient ranges (mu)
FRICTION_COEFFICIENTS = {
    "steel":    (0.4, 0.8),
    "aluminum": (0.3, 0.6),
    "brass":    (0.3, 0.5),
    "plastic":  (0.3, 0.5),
}

# Young's modulus (Pa) - for URDF if needed
YOUNGS_MODULUS = {
    "steel":    200e9,
    "aluminum": 69e9,
    "brass":    100e9,
    "plastic":  3e9,
}

# ============================================================================
# Standard bracket profiles
# ============================================================================
BRACKET_TYPES = ["L", "U", "T"]

# Bracket thickness range (mm)
BRACKET_THICKNESS_RANGE = (1.0, 10.0)

# Bracket arm length range (mm)
BRACKET_ARM_RANGE = (15.0, 120.0)

# ============================================================================
# Housing dimensions
# ============================================================================
HOUSING_WALL_THICKNESS_RANGE = (1.5, 5.0)  # mm
HOUSING_DIM_RANGE = (20.0, 150.0)  # mm per side

# ============================================================================
# Shaft dimensions
# ============================================================================
SHAFT_DIAMETER_RANGE = (3.0, 30.0)  # mm
SHAFT_LENGTH_RANGE = (15.0, 150.0)  # mm

# ============================================================================
# Connector dimensions
# ============================================================================
CONNECTOR_PORT_RANGE = (5.0, 40.0)  # mm inner diameter
CONNECTOR_WALL_RANGE = (1.0, 4.0)   # mm wall thickness

# ============================================================================
# Plate dimensions
# ============================================================================
PLATE_DIM_RANGE = (20.0, 150.0)   # mm
PLATE_THICKNESS_RANGE = (1.0, 12.0)  # mm
