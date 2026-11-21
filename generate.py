#!/usr/bin/env python3
"""
PhysAff-Sim: Main dataset generation script.

Generates 25,000 procedurally generated industrial parts across 6 categories,
exports meshes (STL/STEP), point clouds, URDF files, and metadata.

Usage:
    # Generate all 25K parts
    python generate.py --output ./output

    # Generate a small test batch (100 parts)
    python generate.py --output ./output --test-run

    # Generate a single category
    python generate.py --output ./output --category fasteners --count 100

    # Generate with specific seed for reproducibility
    python generate.py --output ./output --seed 42
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from tqdm import tqdm

from generators import GENERATOR_REGISTRY, CATEGORY_COUNTS
from export.mesh_export import export_stl, export_step, sample_point_cloud, save_point_cloud
from export.urdf_export import export_urdf
from validation.mesh_validator import validate_mesh


def parse_args():
    parser = argparse.ArgumentParser(
        description="PhysAff-Sim: Procedural Industrial Part Generator"
    )
    parser.add_argument("--output", "-o", type=str, default="./output",
                        help="Output directory (default: ./output)")
    parser.add_argument("--category", "-c", type=str, default=None,
                        choices=list(GENERATOR_REGISTRY.keys()),
                        help="Generate only this category (default: all)")
    parser.add_argument("--count", "-n", type=int, default=None,
                        help="Override part count for the category")
    parser.add_argument("--seed", "-s", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--test-run", action="store_true",
                        help="Quick test: 10 parts per category")
    parser.add_argument("--export-step", action="store_true",
                        help="Also export STEP files (slower, larger)")
    parser.add_argument("--skip-pointcloud", action="store_true",
                        help="Skip point cloud sampling (faster)")
    parser.add_argument("--skip-urdf", action="store_true",
                        help="Skip URDF generation")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip mesh validation")
    parser.add_argument("--points-per-cloud", type=int, default=10000,
                        help="Number of points per point cloud (default: 10000)")
    parser.add_argument("--workers", "-w", type=int, default=1,
                        help="Number of parallel workers (default: 1)")
    return parser.parse_args()


def generate_category(category: str, count: int, output_dir: str, seed: int,
                      args: argparse.Namespace) -> dict:
    """Generate all parts for a single category."""
    gen_class = GENERATOR_REGISTRY[category]
    generator = gen_class(seed=seed)

    # Create output subdirectories
    cat_dir = os.path.join(output_dir, category)
    mesh_dir = os.path.join(cat_dir, "meshes")
    pc_dir = os.path.join(cat_dir, "point_clouds")
    urdf_dir = os.path.join(cat_dir, "urdf")
    meta_dir = os.path.join(cat_dir, "metadata")

    for d in [mesh_dir, pc_dir, urdf_dir, meta_dir]:
        os.makedirs(d, exist_ok=True)

    stats = {
        "category": category,
        "total": count,
        "generated": 0,
        "valid": 0,
        "failed": 0,
        "failed_ids": [],
        "time_seconds": 0.0,
    }

    t_start = time.time()

    for i in tqdm(range(count), desc=f"  {category}", leave=True):
        try:
            # Generate part
            part = generator.generate_one(index=i)
            part_id = part["part_id"]

            # Export STL mesh
            stl_path = os.path.join(mesh_dir, f"{part_id}.stl")
            export_stl(part["solid"], stl_path)

            # Export STEP (optional)
            if args.export_step:
                step_path = os.path.join(mesh_dir, f"{part_id}.step")
                export_step(part["solid"], step_path)

            # Sample point cloud
            if not args.skip_pointcloud:
                pc_data = sample_point_cloud(part["solid"],
                                             n_points=args.points_per_cloud,
                                             seed=seed + i)
                pc_path = os.path.join(pc_dir, f"{part_id}.npz")
                save_point_cloud(pc_data, pc_path)

            # Export URDF
            if not args.skip_urdf:
                export_urdf(part, cat_dir)

            # Validate
            if not args.skip_validation:
                val_result = validate_mesh(part["solid"], part)
                if val_result["valid"]:
                    stats["valid"] += 1
                else:
                    stats["failed_ids"].append({
                        "part_id": part_id,
                        "warnings": val_result["warnings"],
                    })

            # Save metadata (without the CadQuery solid object)
            meta = {
                "part_id": part_id,
                "category": part["category"],
                "params": {k: v for k, v in part["params"].items()
                           if not k.startswith("_")},
                "physical_properties": part["physical_properties"],
                "bounding_box": part["bounding_box"],
                "symmetry_group": part["symmetry_group"],
            }
            meta_path = os.path.join(meta_dir, f"{part_id}.json")
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2, default=str)

            stats["generated"] += 1

        except Exception as e:
            stats["failed"] += 1
            stats["failed_ids"].append({
                "part_id": f"{category}_{i}",
                "error": str(e),
            })
            print(f"\n  [ERROR] {category} part {i}: {e}")

    stats["time_seconds"] = round(time.time() - t_start, 2)
    return stats


def main():
    args = parse_args()

    print("=" * 70)
    print("PhysAff-Sim: Procedural Industrial Part Generator")
    print("=" * 70)

    # Determine categories and counts
    if args.category:
        categories = {args.category: args.count or CATEGORY_COUNTS.get(args.category, 100)}
    elif args.test_run:
        categories = {cat: 10 for cat in GENERATOR_REGISTRY}
    else:
        categories = CATEGORY_COUNTS.copy()
        if args.count:
            # Override all counts proportionally
            total_orig = sum(CATEGORY_COUNTS.values())
            scale = args.count / total_orig
            categories = {cat: max(1, int(c * scale)) for cat, c in categories.items()}

    total_parts = sum(categories.values())
    print(f"\nConfiguration:")
    print(f"  Output directory: {args.output}")
    print(f"  Seed: {args.seed}")
    print(f"  Total parts: {total_parts:,}")
    print(f"  Points per cloud: {args.points_per_cloud:,}")
    print(f"  Categories:")
    for cat, count in categories.items():
        print(f"    {cat}: {count:,}")
    print()

    # Generate each category
    all_stats = []
    overall_start = time.time()

    for cat, count in categories.items():
        print(f"\n[{cat.upper()}] Generating {count:,} parts...")
        # Unique seed per category for reproducibility
        cat_seed = args.seed + hash(cat) % (2**31)
        stats = generate_category(cat, count, args.output, cat_seed, args)
        all_stats.append(stats)

        print(f"  Done: {stats['generated']}/{count} generated, "
              f"{stats['valid']} valid, {stats['failed']} failed, "
              f"{stats['time_seconds']:.1f}s")

    overall_time = time.time() - overall_start

    # Summary
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)

    total_gen = sum(s["generated"] for s in all_stats)
    total_valid = sum(s["valid"] for s in all_stats)
    total_failed = sum(s["failed"] for s in all_stats)

    print(f"  Total generated: {total_gen:,} / {total_parts:,}")
    print(f"  Valid: {total_valid:,} ({total_valid / max(total_gen, 1) * 100:.1f}%)")
    print(f"  Failed: {total_failed:,}")
    print(f"  Total time: {overall_time:.1f}s ({overall_time / 60:.1f} min)")
    print(f"  Rate: {total_gen / max(overall_time, 1):.1f} parts/sec")

    # Save generation report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": args.seed,
        "total_requested": total_parts,
        "total_generated": total_gen,
        "total_valid": total_valid,
        "total_failed": total_failed,
        "time_seconds": round(overall_time, 2),
        "categories": all_stats,
    }
    report_path = os.path.join(args.output, "generation_report.json")
    os.makedirs(args.output, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved to: {report_path}")

    if total_failed > 0:
        print(f"\n  [WARNING] {total_failed} parts failed. Check report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
