from pathlib import Path
import subprocess


ROOT = Path('/home/moonlight/Project/Github/MyProject/EgoCore')


def test_doc_system_inventory_builder_generates_key_outputs():
    subprocess.run(['python', str(ROOT / 'tools' / 'build_doc_system_inventory.py')], check=True)
    generated = ROOT / 'docs' / 'generated'
    assert (generated / 'repo_inventory.md').exists()
    assert (generated / 'file_inventory.csv').exists()
    assert (generated / 'module_map.md').exists()
    assert (generated / 'import_or_reference_map.csv').exists()
    assert (generated / 'orphan_candidates.md').exists()
    assert (generated / 'recent_hotspots.md').exists()
