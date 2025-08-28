#!/usr/bin/env python3
"""
Clean up old database files after migration to CSV
"""

import os
import shutil
from pathlib import Path


def cleanup_databases():
    """Remove old database files after CSV migration"""

    print("🧹 Cleaning up old database files...")
    print("=" * 50)

    # Find all database files
    db_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db") or file.endswith(".sqlite"):
                db_files.append(os.path.join(root, file))

    print(f"Found {len(db_files)} database files")

    # Create backup directory
    backup_dir = "old_databases_backup"
    os.makedirs(backup_dir, exist_ok=True)

    # Move databases to backup (don't delete, just move)
    moved_count = 0
    for db_file in db_files:
        try:
            # Get relative path
            rel_path = os.path.relpath(db_file, ".")
            backup_path = os.path.join(backup_dir, rel_path)

            # Create backup directory structure
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Move file
            shutil.move(db_file, backup_path)
            print(f"   📦 Moved: {rel_path}")
            moved_count += 1

        except Exception as e:
            print(f"   ❌ Error moving {db_file}: {e}")

    print(f"\n✅ Moved {moved_count} database files to: {backup_dir}")
    print(f"📁 Your CSV data is now in: csv_data/")
    print(f"🔄 You can restore databases from {backup_dir} if needed")


if __name__ == "__main__":
    cleanup_databases()
