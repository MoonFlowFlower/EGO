#!/usr/bin/env python3
"""Debug script to check consolidation drift values"""

from emotiond.core import RelationshipManager

# Set up multiple targets with different relationship values
targets_data = {
    "user_A": {"bond": 0.9, "grudge": 0.1},
    "user_B": {"bond": 0.3, "grudge": 0.8},
    "user_C": {"bond": 0.5, "grudge": 0.5}
}

manager = RelationshipManager()
for target, data in targets_data.items():
    manager.relationships[target] = data

print("Initial values:")
for target, data in targets_data.items():
    print(f"  {target}: bond={data['bond']}, grudge={data['grudge']}")

# Apply consolidation drift multiple times
for i in range(10):
    manager.apply_consolidation_drift()
    print(f"\nAfter {i+1} consolidation drifts:")
    for target in targets_data:
        print(f"  {target}: bond={manager.relationships[target]['bond']:.6f}, grudge={manager.relationships[target]['grudge']:.6f}")

# Check decay
print("\nDecay analysis:")
for target, initial_data in targets_data.items():
    bond_decayed = manager.relationships[target]["bond"] < initial_data["bond"]
    grudge_decayed = manager.relationships[target]["grudge"] < initial_data["grudge"]
    print(f"  {target}: bond decayed={bond_decayed}, grudge decayed={grudge_decayed}")
    print(f"    bond: {initial_data['bond']} -> {manager.relationships[target]['bond']:.6f}")
    print(f"    grudge: {initial_data['grudge']} -> {manager.relationships[target]['grudge']:.6f}")