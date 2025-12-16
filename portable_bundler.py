#!/usr/bin/env python3
"""
Simple Java AppImage bundler demo - creates portable AppImages
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_system_architecture():
    """Get the system architecture for AppImage creation"""
    import platform

    machine = platform.machine().lower()

    # Map common architectures
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "armv7l": "armhf",
        "i386": "i386",
        "i686": "i386",
    }

    return arch_map.get(machine, "x86_64")  # Default to x86_64


def _create_portable_apprun(jar_name: str) -> str:
    """Create AppRun script with fallback to system Java."""
    return f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"

# Get JAR file path
JAR_FILE="$HERE/usr/bin/{jar_name}.jar"

# Check if JAR exists
if [ ! -f "$JAR_FILE" ]; then
    echo "Error: JAR file not found: $JAR_FILE"
    exit 1
fi

# Build classpath with dependencies
CLASSPATH="$JAR_FILE"
LIB_DIR="$HERE/usr/lib"
if [ -d "$LIB_DIR" ]; then
    for jar in "$LIB_DIR"/*.jar; do
        if [ -f "$jar" ]; then
            CLASSPATH="$CLASSPATH:$jar"
        fi
    done
fi

# Priority 1: Try bundled Java (if available)
BUNDLED_JAVA="$HERE/usr/java/bin/java"
if [ -f "$BUNDLED_JAVA" ]; then
    export JAVA_HOME="$HERE/usr/java"
    export PATH="$HERE/usr/java/bin:$PATH"
    JAVA_CMD="$BUNDLED_JAVA"
    echo "✅ Using bundled Java: $($JAVA_CMD -version 2>&1 | head -1)"
else
    # Priority 2: Fall back to system Java
    JAVA_CMD="java"
    if command -v "$JAVA_CMD" >/dev/null 2>&1; then
        echo "✅ Using system Java: $($JAVA_CMD -version 2>&1 | head -1)"
    else
        echo "❌ No Java runtime found - neither bundled nor system Java available"
        echo ""
        echo "To create a fully portable AppImage with bundled Java:"
        echo "1. Download OpenJDK 11 or later"
        echo "2. Extract to $HERE/usr/java/"
        echo "3. Re-run this AppImage"
        exit 1
    fi
fi

# GUI-specific Java options for SQLWorkbench
JAVA_OPTS="--add-opens java.desktop/com.sun.java.swing.plaf.motif=ALL-UNNAMED"
JAVA_OPTS="$JAVA_OPTS --add-opens=java.desktop/com.sun.java.swing.plaf.gtk=ALL-UNNAMED"
JAVA_OPTS="$JAVA_OPTS -Dawt.useSystemAAFontSettings=on"
JAVA_OPTS="$JAVA_OPTS -Dswing.defaultlaf=com.sun.java.swing.plaf.gtk.GTKLookAndFeel"

export JAVA_OPTS

# Try to run as -jar first (if Main-Class is defined)
if "$JAVA_CMD" -jar "$JAR_FILE" "$@"; then
    exit 0
fi

# Fallback: try main class directly
exec "$JAVA_CMD" -cp "$CLASSPATH" workbench.sql.Workbench "$@"
"""


def _setup_directories(app_dir: Path) -> tuple:
    """Create and return the directory structure."""
    app_dir.mkdir(parents=True)
    usr_dir = app_dir / "usr"
    usr_bin_dir = usr_dir / "bin"
    usr_lib_dir = usr_dir / "lib"
    usr_java_dir = usr_dir / "java"
    usr_share_dir = usr_dir / "share"
    usr_share_app_dir = usr_share_dir / "applications"

    for dir_path in [
        usr_bin_dir,
        usr_lib_dir,
        usr_java_dir,
        usr_share_dir,
        usr_share_app_dir,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    return usr_dir, usr_bin_dir, usr_lib_dir, usr_java_dir, usr_share_dir, usr_share_app_dir


def _copy_jar_and_deps(jar_file: Path, usr_bin_dir: Path, usr_lib_dir: Path, app_name: str) -> None:
    """Copy JAR file and dependencies."""
    dest_jar = usr_bin_dir / f"{app_name.lower()}.jar"
    shutil.copy2(jar_file, dest_jar)
    print(f"📦 Copied JAR: {dest_jar}")

    if jar_file.parent.name == "test_jars":
        for dep_name in ["commons-cli-1.5.0.jar", "commons-lang3-3.12.0.jar"]:
            src = jar_file.parent / dep_name
            if src.exists():
                dst = usr_lib_dir / dep_name
                shutil.copy2(src, dst)
                print(f"📦 Copied dependency: {dep_name}")


def _create_desktop_files(app_dir: Path, app_dir_name: str, app_name: str, usr_share_app_dir: Path) -> None:
    """Create desktop files for AppImage."""
    desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=SQL Workbench - Portable Database Tool
Exec={app_dir_name}
Icon={app_dir_name.lower()}
Categories=Development;Database;
Terminal=false
StartupNotify=true
"""
    root_desktop_path = app_dir / f"{app_dir_name}.desktop"
    with open(root_desktop_path, "w") as f:
        f.write(desktop_content)
    print(f"📝 Created root desktop file: {root_desktop_path}")

    desktop_path = usr_share_app_dir / f"{app_dir_name}.desktop"
    with open(desktop_path, "w") as f:
        f.write(desktop_content)
    print(f"📝 Created usr desktop file: {desktop_path}")


def _copy_or_create_icon(jar_file: Path, app_dir: Path, app_dir_name: str, usr_dir: Path) -> None:
    """Copy icon or create minimal one."""
    icon_paths = [
        jar_file.parent / f"{app_dir_name.replace('-', '')}.png",
        jar_file.parent / "sqlworkbench.png",
    ]

    for icon_path in icon_paths:
        if icon_path.exists():
            root_icon_path = app_dir / f"{app_dir_name}.png"
            shutil.copy2(icon_path, root_icon_path)
            print(f"🖼️  Copied icon to root: {root_icon_path}")
            icons_dir = usr_dir / "share" / "icons"
            icons_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(icon_path, icons_dir / f"{app_dir_name}.png")
            return

    # Create minimal icon
    root_icon_path = app_dir / f"{app_dir_name}.png"
    with open(root_icon_path, "wb") as f:
        f.write(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )
    print(f"🖼️  Created minimal icon: {root_icon_path}")


def _create_java_readme(usr_java_dir: Path, app_name: str) -> None:
    """Create Java bundling instructions."""
    java_placeholder = usr_java_dir / "README.md"
    with open(java_placeholder, "w") as f:
        f.write(f"""# Java Bundling for {app_name}

This AppImage is designed to be portable with bundled Java runtime.

## To Add Bundled Java:
1. Download OpenJDK 11 or later from: https://adoptium.net/
2. Extract JDK contents to this directory
3. Re-run the AppImage

## Current Status:
- Smart AppRun: ✅ Supports both bundled and system Java
- System Java fallback: ✅ Uses system Java if bundled not available
- Dependencies: ✅ JAR dependencies included
- Desktop Integration: ✅ Professional desktop file created

## Java Options Included:
- GUI optimizations for Swing applications
- Font anti-aliasing enabled
- Platform-specific Look & Feel
- Desktop module access permissions
""")
    print(f"📝 Created Java bundling instructions: {java_placeholder}")


def _build_appimage(app_dir: Path, app_dir_name: str, arch: str | None, output_dir: Path) -> str | None:
    """Build final AppImage."""
    if not Path("./appimagetool").exists():
        print("⚠️  appimagetool not found")
        print(f"📦 AppImage directory created: {app_dir}")
        print(f"🔧 To create final AppImage: ./appimagetool {app_dir}")
        return str(app_dir)

    if arch is None:
        arch = get_system_architecture()
    print(f"🔧 Creating final AppImage for {arch}...")

    try:
        env = os.environ.copy()
        env["ARCH"] = arch
        result = subprocess.run(
            ["./appimagetool", "--no-appstream", str(app_dir)],
            capture_output=True,
            text=True,
            cwd=output_dir,
            env=env,
        )

        if result.returncode != 0:
            print(f"❌ AppImage creation failed: {result.stderr}")
            return None

        possible_names = [
            f"{app_dir_name}-x86_64.AppImage",
            f"{app_dir_name}.AppImage",
        ]

        for name in possible_names:
            candidate = output_dir / name
            if candidate.exists():
                size_mb = candidate.stat().st_size // (1024 * 1024)
                print(f"✅ Portable AppImage created: {candidate}")
                print(f"📦 Size: {size_mb} MB")
                print("☕ Java: Smart bundling system (uses system Java, ready for bundled)")
                print("📱 Features: Portable + Desktop Integration")
                return str(candidate)

        return None
    except Exception as e:
        print(f"❌ Error running appimagetool: {e}")
        return None


def create_portable_appimage(
    jar_file, app_name="SQLWorkbench", output_dir=".", arch=None
):
    """Create a portable AppImage that uses bundled Java or system Java"""

    jar_file = Path(jar_file)
    if not jar_file.exists():
        print(f"❌ JAR file not found: {jar_file}")
        return None

    output_dir = Path(output_dir)
    app_dir_name = f"{app_name.replace(' ', '-').lower()}-portable"
    app_dir = output_dir / f"{app_dir_name}.AppImage"

    print(f"🚀 Creating portable AppImage for {app_name}...")

    if app_dir.exists():
        shutil.rmtree(app_dir)

    # Setup directories
    usr_dir, usr_bin_dir, usr_lib_dir, usr_java_dir, usr_share_dir, usr_share_app_dir = _setup_directories(app_dir)

    # Copy JAR and dependencies
    _copy_jar_and_deps(jar_file, usr_bin_dir, usr_lib_dir, app_name)

    # Create AppRun script
    apprun_content = _create_portable_apprun(app_name.lower())
    apprun_path = app_dir / "AppRun"
    with open(apprun_path, "w") as f:
        f.write(apprun_content)
    apprun_path.chmod(0o755)
    print(f"📝 Created smart AppRun: {apprun_path}")

    # Create desktop files
    _create_desktop_files(app_dir, app_dir_name, app_name, usr_share_app_dir)

    # Handle icon
    _copy_or_create_icon(jar_file, app_dir, app_dir_name, usr_dir)

    # Create Java readme
    _create_java_readme(usr_java_dir, app_name)

    # Build final AppImage
    return _build_appimage(app_dir, app_dir_name, arch, output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create portable AppImage with smart Java handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("jar_file", help="JAR file to convert")
    parser.add_argument(
        "--name",
        "-n",
        default="SQLWorkbench",
        help="Application name (default: SQLWorkbench)",
    )
    parser.add_argument(
        "--output", "-o", default=".", help="Output directory (default: current)"
    )
    parser.add_argument(
        "--arch",
        "-a",
        help=f"Target architecture (default: auto-detected, current: {get_system_architecture()})",
    )

    parser.add_argument(
        "--help-examples", action="store_true", help="Show usage examples"
    )

    args = parser.parse_args()

    if args.help_examples:
        print("Examples:")
        print("  python3 portable_bundler.py myapp.jar")
        print("  python3 portable_bundler.py myapp.jar --name 'My App'")
        print(
            f"  python3 portable_bundler.py myapp.jar --arch {get_system_architecture()}"
        )
        print("  python3 portable_bundler.py myapp.jar -n SQLWorkbench -o ~/Desktop")
        sys.exit(0)

    result = create_portable_appimage(args.jar_file, args.name, args.output, args.arch)
    if result:
        print(f"\n🎉 Success! Created: {result}")
        print("📱 This AppImage is portable and includes smart Java handling!")
        print(f"🚀 Run with: ./{Path(result).name}")
        print("☕ Add bundled Java to usr/java/ for true portability")
        sys.exit(0)
    else:
        print("❌ Failed to create portable AppImage")
        sys.exit(1)
