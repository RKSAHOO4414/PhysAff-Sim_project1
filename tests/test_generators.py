"""
Quick test script to verify all generators work.
Run: python -m tests.test_generators
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import GENERATOR_REGISTRY


def test_all_generators():
    """Test that each generator can produce at least one valid part."""
    print("=" * 60)
    print("PhysAff-Sim Generator Test Suite")
    print("=" * 60)

    all_passed = True

    for category, gen_class in GENERATOR_REGISTRY.items():
        print(f"\n[TEST] {category}...")

        try:
            generator = gen_class(seed=12345)

            # Generate 3 parts to test variation
            for i in range(3):
                part = generator.generate_one(index=i)

                assert part["part_id"], f"Missing part_id for {category} #{i}"
                assert part["category"] == category
                assert part["solid"] is not None
                assert part["physical_properties"]["mass_kg"] > 0
                assert part["symmetry_group"] in [
                    "C1", "C2", "C4", "C6", "C_inf",
                    "C8",  # for 8-hole flanges
                ]

                # Check bounding box dimensions are reasonable
                bbox = part["bounding_box"]["size"]
                for dim in bbox:
                    assert dim > 0.1, f"Dimension too small: {dim}mm"
                    assert dim < 500, f"Dimension too large: {dim}mm"

            print(f"  PASSED - Generated 3 parts successfully")
            print(f"    Example: {part['part_id']}")
            print(f"    Mass: {part['physical_properties']['mass_kg']:.4f} kg")
            print(f"    BBox: {part['bounding_box']['size']} mm")
            print(f"    Symmetry: {part['symmetry_group']}")

        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)


if __name__ == "__main__":
    test_all_generators()
