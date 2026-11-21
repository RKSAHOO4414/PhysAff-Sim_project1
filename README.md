# PhysAff-Sim: Procedural Industrial Part Generator

**A Physics-Grounded Affordance Benchmark for Industrial Robotic Manipulation**

This pipeline procedurally generates 25,000 industrial parts across 6 parametric
categories using CadQuery, exports meshes (STL/STEP), point clouds, URDF files,
and metadata for physics simulation in Isaac Sim / MuJoCo / PyBullet.

## Project Structure

```
physaff-sim/
├── generate.py                 # Main generation script
├── requirements.txt            # Python dependencies
├── config/
│   ├── __init__.py
│   └── iso_standards.py        # ISO metric bolt dims, materials, friction
├── generators/
│   ├── __init__.py
│   ├── base.py                 # Abstract base generator class
│   ├── fasteners.py            # Bolts, screws, studs (6,000 parts)
│   ├── brackets.py             # L, U, T-brackets (4,000 parts)
│   ├── housings.py             # Boxes, enclosures (4,000 parts)
│   ├── shafts.py               # Plain, stepped, keyed shafts (4,000 parts)
│   ├── connectors.py           # Pipes, elbows, T-fittings, flanges (3,500 parts)
│   └── plates.py               # Plates with holes, slots, cutouts (3,500 parts)
├── export/
│   ├── __init__.py
│   ├── mesh_export.py          # STL/STEP export + point cloud sampling
│   └── urdf_export.py          # URDF/USD export for simulation
├── validation/
│   ├── __init__.py
│   └── mesh_validator.py       # Watertight, volume, mass sanity checks
├── tests/
│   └── test_generators.py      # Quick generator validation
└── output/                     # Generated data (created at runtime)
    ├── <category>/
    │   ├── meshes/             # STL files
    │   ├── point_clouds/       # .npz files (10K points + normals)
    │   ├── urdf/               # URDF files for simulation
    │   └── metadata/           # JSON files with params + physics
    └── generation_report.json
```

## Setup

### 1. Install CadQuery (requires conda)

```bash
conda create -n physaff python=3.10 -y
conda activate physaff
conda install -c conda-forge cadquery -y
pip install trimesh numpy scipy tqdm pyyaml
```

### 2. Verify installation

```bash
python -c "import cadquery; print('CadQuery version:', cadquery.__version__)"
```

## Usage

### Quick test (10 parts per category = 60 total)

```bash
python generate.py --test-run --output ./output
```

### Generate a single category

```bash
python generate.py --category fasteners --count 100 --output ./output
```

### Generate full dataset (25,000 parts)

```bash
python generate.py --output ./output --seed 42
```

### Run generator tests

```bash
python -m tests.test_generators
```

## Command-Line Options

| Flag | Default | Description |
|---|---|---|
| `--output, -o` | `./output` | Output directory |
| `--category, -c` | all | Generate only one category |
| `--count, -n` | per-category | Override part count |
| `--seed, -s` | 42 | Random seed for reproducibility |
| `--test-run` | off | Quick test: 10 parts per category |
| `--export-step` | off | Also export STEP files |
| `--skip-pointcloud` | off | Skip point cloud sampling |
| `--skip-urdf` | off | Skip URDF generation |
| `--skip-validation` | off | Skip mesh validation |
| `--points-per-cloud` | 10000 | Points per point cloud |

## Part Categories

### 1. Fasteners (6,000 parts)
- **Subtypes:** Hex bolt, socket head cap screw, pan head, flat/countersunk, stud
- **Parameters:** M-size (M3–M20), length (10–100mm), thread pitch, head type, chamfer
- **Symmetry:** C6 (hex/socket), C∞ (pan/flat/stud)

### 2. Brackets (4,000 parts)
- **Subtypes:** L-bracket, U-bracket, T-bracket
- **Parameters:** Arm lengths, thickness (1–10mm), width, bend angle, hole count/diameter
- **Symmetry:** C2 (U-bracket), C1 (L/T)

### 3. Housings (4,000 parts)
- **Subtypes:** Open box, closed box, ported enclosure
- **Parameters:** Dimensions, wall thickness, mounting holes, ports, flanges
- **Symmetry:** C4 (square), C2 (rectangular)

### 4. Shafts & Pins (4,000 parts)
- **Subtypes:** Plain, stepped, keyed, shouldered
- **Parameters:** Diameter (3–30mm), length (15–150mm), step ratios, keyway dims
- **Symmetry:** C∞ (plain/stepped/shouldered), C1 (keyed)

### 5. Connectors & Fittings (3,500 parts)
- **Subtypes:** Straight pipe, elbow, T-fitting, flange adapter
- **Parameters:** Inner diameter, wall thickness, bend angle/radius, flange holes
- **Symmetry:** C∞ (straight), C1 (elbow), C2 (T-fitting), Cn (flange)

### 6. Plates & Flat Stock (3,500 parts)
- **Subtypes:** Hole pattern, slotted, cutout, multi-feature
- **Parameters:** Dimensions, thickness (1–12mm), hole patterns, slot/cutout geometry
- **Symmetry:** C4/C2/C1 depending on features

## Output Format

Each generated part produces:

| File | Format | Description |
|---|---|---|
| `meshes/<id>.stl` | Binary STL | Triangle mesh (~1–2 MB) |
| `point_clouds/<id>.npz` | Compressed NumPy | 10K points (XYZ) + normals (~240 KB) |
| `urdf/<id>.urdf` | XML | Physics properties for simulation |
| `metadata/<id>.json` | JSON | Parameters, mass, CoM, inertia, friction, symmetry |

## Next Steps (Isaac Sim Integration)

1. **Import URDFs into Isaac Sim** using the URDF importer
2. **Set up 4,000 parallel environments** for affordance labeling
3. **Run pick_functional simulation:** grasp → lift → reorient → insert
4. **Run insert/mate_surface/support_surface simulations**
5. **Export per-point affordance labels** as 4-class multi-hot vectors

## Citation

```bibtex
@inproceedings{sahoo2027physaffsim,
  title={PhysAff-Sim: A Task-Conditioned, Physics-Grounded Affordance Benchmark
         for Industrial Robotic Manipulation},
  author={Sahoo, Ranjan Kumar},
  booktitle={Proceedings of the IEEE/CVF International Conference on
             Computer Vision (ICCV)},
  year={2027}
}
```
