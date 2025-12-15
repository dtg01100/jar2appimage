#!/bin/bash
"""
Fixed working bundler for creating portable AppImages with Java
"""

import os
import sys
import subprocess
import shutil
import tarfile
from pathlib import Path


def download_openjdk(version="11", output_dir="."):
    """Download OpenJDK for bundling"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use working Adoptium OpenJDK download URL
    jdk_url = "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.12%2B7/OpenJDK11U-jdk_x64_linux_hotspot_11.0.12_7.tar.gz"
    jdk_path = output_dir / f"openjdk-{version}-x64_linux.tar.gz"

    print(f"🔍 Downloading OpenJDK {version}...")

    try:
        # Use curl to download
        result = subprocess.run(
            ["curl", "-L", "-o", str(jdk_path), jdk_url],
            check=True,
            capture_output=True,
            text=True,
        )

        if jdk_path.exists():
            size_mb = jdk_path.stat().st_size // (1024 * 1024)
            print(f"✅ OpenJDK {version} downloaded: {size_mb} MB")
            return jdk_path
        else:
            print("❌ Download failed - file not created")
            return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def extract_openjdk(jdk_path, extract_dir):
    """Extract OpenJDK to directory"""
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Extracting OpenJDK...")

    try:
        with tarfile.open(jdk_path, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Find the JDK directory (usually jdk-*)
        for item in extract_dir.iterdir():
            if item.is_dir() and item.name.startswith("jdk-"):
                print(f"✅ OpenJDK extracted: {item}")
                return item

        print("❌ Could not find JDK directory after extraction")
        return None

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None


def create_bundled_appimage(jar_file, app_name="SQLWorkbench", output_dir="."):
    """Create AppImage with bundled Java"""

    jar_file = Path(jar_file)
    if not jar_file.exists():
        print(f"❌ JAR file not found: {jar_file}")
        return None

    output_dir = Path(output_dir)
    app_dir = output_dir / f"{app_name}-Bundled.AppImage"

    print(f"🚀 Creating bundled AppImage for {app_name}...")

    # Clean up any existing AppImage
    if app_dir.exists():
        shutil.rmtree(app_dir)

    # Create AppImage structure
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

    # Step 1: Copy JAR file
    dest_jar = usr_bin_dir / f"{app_name.lower()}.jar"
    shutil.copy2(jar_file, dest_jar)
    print(f"📦 Copied JAR: {dest_jar}")

    # Step 2: Download and extract OpenJDK
    jdk_archive = download_openjdk("11", output_dir)
    if not jdk_archive:
        print("❌ Failed to download OpenJDK")
        return None

    jdk_dir = extract_openjdk(jdk_archive, output_dir)
    if not jdk_dir:
        print("❌ Failed to extract OpenJDK")
        return None

    # Step 3: Copy Java to AppImage
    try:
        # Copy entire JDK contents to usr/java
        for item in jdk_dir.iterdir():
            src = jdk_dir / item.name
            dst = usr_java_dir / item.name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        print(f"☕ Bundled Java: {usr_java_dir}")

        # Clean up downloaded JDK
        jdk_archive.unlink()
        shutil.rmtree(jdk_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ Failed to copy Java: {e}")
        return None

    # Step 4: Copy any existing dependencies
    if jar_file.parent.name == "test_jars":
        # Copy common JAR dependencies
        for dep_name in ["commons-cli-1.5.0.jar", "commons-lang3-3.12.0.jar"]:
            src = jar_file.parent / dep_name
            if src.exists():
                dst = usr_lib_dir / dep_name
                shutil.copy2(src, dst)
                print(f"📦 Copied dependency: {dep_name}")

    # Step 5: Create proper AppRun script for bundled Java
    apprun_content = f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
export PATH="${{HERE}}/usr/java/bin:${{PATH}}"
export JAVA_HOME="${{HERE}}/usr/java"

# Get JAR file path
JAR_FILE="${{HERE}}/usr/bin/{app_name.lower()}.jar"

# Check if JAR exists
if [ ! -f "$JAR_FILE" ]; then
    echo "Error: JAR file not found: $JAR_FILE"
    exit 1
fi

# Build classpath with dependencies
CLASSPATH="$JAR_FILE"
LIB_DIR="${{HERE}}/usr/lib"
if [ -d "$LIB_DIR" ]; then
    for jar in "$LIB_DIR"/*.jar; do
        if [ -f "$jar" ]; then
            CLASSPATH="$CLASSPATH:$jar"
        fi
    done
fi

# GUI-specific Java options for SQLWorkbench
JAVA_OPTS="--add-opens java.desktop/com.sun.java.swing.plaf.motif=ALL-UNNAMED"
JAVA_OPTS="$JAVA_OPTS --add-opens java.desktop/com.sun.java.swing.plaf.gtk=ALL-UNNAMED"
JAVA_OPTS="$JAVA_OPTS -Dawt.useSystemAAFontSettings=on"
JAVA_OPTS="$JAVA_OPTS -Dswing.defaultlaf=com.sun.java.swing.plaf.gtk.GTKLookAndFeel"

# Use bundled Java
JAVA_CMD="${{HERE}}/usr/java/bin/java"

# Validate bundled Java
if [ ! -f "$JAVA_CMD" ]; then
    echo "❌ Bundled Java not found: $JAVA_CMD"
    exit 1
fi

echo "✅ Using bundled Java: $("$JAVA_CMD" -version 2>&1 | head -1)"

# Try to run as -jar first (if Main-Class is defined)
if "$JAVA_CMD" -jar "$JAR_FILE" "$@"; then
    exit 0
fi

# Fallback: try main class directly
exec "$JAVA_CMD" $JAVA_OPTS -cp "$CLASSPATH" workbench.sql.Workbench "$@"
"""

    apprun_path = app_dir / "AppRun"
    with open(apprun_path, "w") as f:
        f.write(apprun_content)
    apprun_path.chmod(0o755)
    print(f"📝 Created AppRun: {apprun_path}")

    # Step 6: Create desktop file
    desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=SQL Workbench - Database tool
Exec={app_name}
Icon={app_name.lower()}
Categories=Development;Database;
Terminal=false
StartupNotify=true
"""

    desktop_path = usr_share_app_dir / f"{app_name.lower()}.desktop"
    with open(desktop_path, "w") as f:
        f.write(desktop_content)
    print(f"📝 Created desktop file: {desktop_path}")

    # Step 7: Copy icon if available
    icon_paths = [
        jar_file.parent / f"{app_name.lower()}.png",
        jar_file.parent / "sqlworkbench.png",
    ]

    icon_copied = False
    for icon_path in icon_paths:
        if icon_path.exists():
            icons_dir = usr_dir / "share" / "icons"
            icons_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(icon_path, icons_dir / f"{app_name.lower()}.png")
            print(f"🖼️  Copied icon: {icon_path}")
            icon_copied = True
            break

    if not icon_copied:
        print("⚠️  No icon found")

    # Step 8: Create final AppImage
    if Path("./appimagetool").exists():
        print(f"🔧 Creating final AppImage...")
        try:
            result = subprocess.run(
                ["./appimagetool", "--no-appstream", str(app_dir)],
                capture_output=True,
                text=True,
                cwd=output_dir,
            )

            if result.returncode == 0:
                final_appimage = output_dir / f"{app_name}-Bundled.AppImage"
                if final_appimage.exists():
                    size_mb = final_appimage.stat().st_size // (1024 * 1024)
                    print(f"✅ Bundled AppImage created: {final_appimage}")
                    print(f"📦 Size: {size_mb} MB")
                    print(f"☕ Contains: OpenJDK 11 (portable)")
                    print(f"🚀 Run with: ./{Path(final_appimage).name}")
                    return str(final_appimage)
            else:
                print(f"❌ AppImage creation failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error running appimagetool: {e}")
    else:
        print(f"⚠️  appimagetool not found")
        print(f"📦 AppImage directory created: {app_dir}")
        print(f"🔧 To create final AppImage: ./appimagetool {app_dir}")
        return str(app_dir)

    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 working_bundler.py <jar_file> [app_name] [output_dir]")
        sys.exit(1)

    jar_file = sys.argv[1]
    app_name = sys.argv[2] if len(sys.argv) > 2 else "SQLWorkbench"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "."

    result = create_bundled_appimage(jar_file, app_name, output_dir)
    if result:
        print(f"\n🎉 Success! Created: {result}")
        print(f"📱 This AppImage includes bundled Java - completely portable!")
        sys.exit(0)
    else:
        print("❌ Failed to create bundled AppImage")
        sys.exit(1)
