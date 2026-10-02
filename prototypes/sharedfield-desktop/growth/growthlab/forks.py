"""Consistent, independent SQLite copies. Never share test writable storage."""
import hashlib
import sqlite3
from pathlib import Path


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fork_storage(source,destination):
    source,destination=Path(source).resolve(),Path(destination).resolve()
    if source==destination or destination.exists():raise ValueError('fork_destination_exists')
    destination.parent.mkdir(parents=True,exist_ok=True)
    original=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    target=sqlite3.connect(destination)
    try:original.backup(target)
    finally:target.close();original.close()
    return {'source_sha256':file_hash(source),'copy_sha256':file_hash(destination),'copy':str(destination)}
