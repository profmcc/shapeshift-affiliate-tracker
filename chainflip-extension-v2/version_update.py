#!/usr/bin/env python3
"""
Chainflip Extension Version Update Script
Automatically updates version numbers across all extension files
"""

import os
import re
import sys
from datetime import datetime


class VersionUpdater:
    def __init__(self, extension_dir):
        self.extension_dir = extension_dir
        self.current_version = None
        self.new_version = None

    def get_current_version(self):
        """Extract current version from manifest.json"""
        manifest_path = os.path.join(self.extension_dir, "manifest.json")

        if not os.path.exists(manifest_path):
            print("❌ manifest.json not found!")
            return None

        with open(manifest_path, "r") as f:
            content = f.read()

        # Extract version from manifest
        version_match = re.search(r'"version":\s*"([^"]+)"', content)
        if version_match:
            self.current_version = version_match.group(1)
            print(f"📋 Current version: {self.current_version}")
            return self.current_version
        else:
            print("❌ Could not extract version from manifest.json")
            return None

    def prompt_new_version(self):
        """Prompt user for new version number"""
        if not self.current_version:
            print("❌ No current version found")
            return None

        print(f"\n🔄 Current version: {self.current_version}")
        print("Enter new version (e.g., 2.1.0, 3.0.0):")

        while True:
            new_version = input("New version: ").strip()

            # Validate version format (x.y.z)
            if re.match(r"^\d+\.\d+\.\d+$", new_version):
                self.new_version = new_version
                return new_version
            else:
                print("❌ Invalid version format. Use x.y.z format (e.g., 2.1.0)")

    def update_file_version(self, file_path, old_version, new_version):
        """Update version in a specific file"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Replace version references
            updated_content = content.replace(old_version, new_version)

            # Also update version comments
            updated_content = re.sub(
                r"v\d+\.\d+\.\d+", f"v{new_version}", updated_content
            )

            # Update date references if present
            today = datetime.now().strftime("%Y-%m-%d")
            updated_content = re.sub(r"\d{4}-\d{2}-\d{2}", today, updated_content)

            if content != updated_content:
                with open(file_path, "w") as f:
                    f.write(updated_content)
                print(f"✅ Updated: {os.path.basename(file_path)}")
                return True
            else:
                print(f"⏭️  No changes needed: {os.path.basename(file_path)}")
                return False

        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
            return False

    def update_all_files(self):
        """Update version numbers in all relevant files"""
        if not self.current_version or not self.new_version:
            print("❌ Cannot proceed without version information")
            return False

        print(f"\n🚀 Updating from v{self.current_version} to v{self.new_version}")

        # Files to update
        files_to_update = [
            "manifest.json",
            "content.js",
            "background.js",
            "popup.html",
            "popup.js",
            "README.md",
        ]

        updated_count = 0
        for filename in files_to_update:
            file_path = os.path.join(self.extension_dir, filename)
            if os.path.exists(file_path):
                if self.update_file_version(
                    file_path, self.current_version, self.new_version
                ):
                    updated_count += 1
            else:
                print(f"⚠️  File not found: {filename}")

        print(f"\n✅ Updated {updated_count} files")
        return True

    def create_backup(self):
        """Create a backup of the current version"""
        if not self.current_version:
            return False

        backup_dir = f"{self.extension_dir}_v{self.current_version}_backup"

        try:
            import shutil

            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(self.extension_dir, backup_dir)
            print(f"💾 Backup created: {backup_dir}")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def run(self):
        """Main execution flow"""
        print("🔄 Chainflip Extension Version Updater")
        print("=" * 40)

        # Get current version
        if not self.get_current_version():
            return False

        # Create backup
        self.create_backup()

        # Prompt for new version
        if not self.prompt_new_version():
            return False

        # Confirm update
        print(
            f"\n⚠️  About to update from v{self.current_version} to v{self.new_version}"
        )
        confirm = input("Continue? (y/N): ").strip().lower()

        if confirm != "y":
            print("❌ Update cancelled")
            return False

        # Perform update
        if self.update_all_files():
            print(f"\n🎉 Successfully updated to v{self.new_version}!")
            print(f"📁 Extension directory: {self.extension_dir}")
            print("\nNext steps:")
            print("1. Test the updated extension")
            print("2. Update any external documentation")
            print("3. Commit changes to version control")
            return True
        else:
            print("❌ Update failed!")
            return False


def main():
    # Get extension directory
    if len(sys.argv) > 1:
        extension_dir = sys.argv[1]
    else:
        # Default to current directory
        extension_dir = os.getcwd()

    # Validate directory
    if not os.path.exists(extension_dir):
        print(f"❌ Directory not found: {extension_dir}")
        sys.exit(1)

    if not os.path.exists(os.path.join(extension_dir, "manifest.json")):
        print(f"❌ Not a valid extension directory: {extension_dir}")
        print("Please run from the extension directory or provide the correct path")
        sys.exit(1)

    # Run updater
    updater = VersionUpdater(extension_dir)
    success = updater.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
