#!/usr/bin/env python3
"""
Configuration File Support for jar2appimage
Supports YAML, JSON, and TOML configuration files for build settings and metadata
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

# Configure module-level logger
logger = logging.getLogger(__name__)

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import toml

    HAS_TOML = True
except ImportError:
    HAS_TOML = False


@dataclass
class AppImageConfig:
    """Configuration data class for AppImage creation"""

    # Basic settings
    name: Optional[str] = None
    version: str = "1.0.0"
    description: Optional[str] = None

    # JAR configuration
    jar_path: Optional[str] = None
    main_class: Optional[str] = None
    classpath: Optional[List[str]] = None

    # AppImage settings
    icon: Optional[str] = None
    category: str = "Utility"
    bundled_java: bool = False
    java_version: Optional[str] = None

    # Build settings
    output_dir: str = "."
    validate: bool = False
    verbose: bool = False
    cleanup: bool = True

    # Desktop integration
    terminal: Optional[bool] = None  # Auto-detect if None
    startup_notify: bool = True
    mime_types: Optional[List[str]] = None

    # Advanced settings
    dependencies: Optional[List[str]] = None
    libraries: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    java_options: Optional[List[str]] = None

    # Metadata
    author: Optional[str] = None
    license: Optional[str] = None
    website: Optional[str] = None
    keywords: Optional[List[str]] = None

    def __post_init__(self) -> None:
        # Initialize lists that should not be None
        if self.classpath is None:
            self.classpath = []
        if self.mime_types is None:
            self.mime_types = []
        if self.dependencies is None:
            self.dependencies = []
        if self.libraries is None:
            self.libraries = []
        if self.environment is None:
            self.environment = {}
        if self.java_options is None:
            self.java_options = []
        if self.keywords is None:
            self.keywords = []


class ConfigManager:
    """Manages configuration files and settings"""

    SUPPORTED_FORMATS = ["json", "yaml", "yml", "toml"]
    DEFAULT_CONFIG_NAMES = [
        "jar2appimage.json",
        "jar2appimage.yaml",
        "jar2appimage.yml",
        "jar2appimage.toml",
        ".jar2appimage.json",
        ".jar2appimage.yaml",
        ".jar2appimage.yml",
        ".jar2appimage.toml",
    ]

    def __init__(self) -> None:
        self.current_config: AppImageConfig = AppImageConfig()
        self.config_file_path: Optional[Path] = None

    def load_config(self, config_path: Union[str, Path]) -> AppImageConfig:
        """Load configuration from file"""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        self.config_file_path = config_path
        logger.info(f"Loading configuration from: {config_path}")

        # Determine file format
        if config_path.suffix.lower() == ".json":
            config_data: Dict[str, Any] = self._load_json(config_path)
        elif config_path.suffix.lower() in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise ImportError(
                    "PyYAML is required for YAML configuration files. Install with: pip install PyYAML"
                )
            config_data = self._load_yaml(config_path)
        elif config_path.suffix.lower() == ".toml":
            if not HAS_TOML:
                raise ImportError(
                    "toml is required for TOML configuration files. Install with: pip install toml"
                )
            config_data = self._load_toml(config_path)
        else:
            raise ValueError(f"Unsupported configuration format: {config_path.suffix}")

        # Create config object
        self.current_config = self._dict_to_config(config_data)
        logger.info(f"Configuration loaded successfully: {self.current_config.name or 'unnamed'}")
        return self.current_config

    def auto_discover_config(
        self, working_dir: Union[str, Path] = "."
    ) -> Optional[AppImageConfig]:
        """Auto-discover and load configuration file"""
        working_dir = Path(working_dir)
        logger.debug(f"Auto-discovering config in: {working_dir}")

        # Search for config files in order of preference
        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = working_dir / config_name
            if config_path.exists():
                try:
                    logger.info(f"Found configuration file: {config_path}")
                    return self.load_config(config_path)
                except Exception as e:
                    print(f"⚠️  Found config file {config_path} but failed to load: {e}")
                    logger.warning(f"Failed to load config file {config_path}: {e}")
                    continue

        logger.debug("No configuration file found during auto-discovery")
        return None

    def save_config(
        self, config_path: Union[str, Path], config: Optional[AppImageConfig] = None
    ) -> None:
        """Save configuration to file"""
        config_path = Path(config_path)
        config = config or self.current_config

        config_data = asdict(config)

        # Determine file format
        if config_path.suffix.lower() == ".json":
            self._save_json(config_path, config_data)
        elif config_path.suffix.lower() in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise ImportError("PyYAML is required for YAML configuration files")
            self._save_yaml(config_path, config_data)
        elif config_path.suffix.lower() == ".toml":
            if not HAS_TOML:
                raise ImportError("toml is required for TOML configuration files")
            self._save_toml(config_path, config_data)
        else:
            raise ValueError(f"Unsupported configuration format: {config_path.suffix}")

        print(f"✅ Configuration saved to: {config_path}")
        logger.info(f"Configuration saved to: {config_path}")

    def merge_cli_args(self, cli_args: argparse.Namespace) -> AppImageConfig:
        """Merge CLI arguments with configuration"""
        # Override config with CLI args (non-None values)
        for key, value in vars(cli_args).items():
            if value is not None and hasattr(self.current_config, key):
                setattr(self.current_config, key, value)
                logger.debug(f"CLI arg override: {key} = {value}")

        return self.current_config

    def _load_json(self, config_path: Path) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(config_path, encoding="utf-8") as f:
            return cast(Dict[str, Any], json.load(f))

    def _load_yaml(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML configuration"""
        with open(config_path, encoding="utf-8") as f:
            return cast(Dict[str, Any], yaml.safe_load(f) or {})

    def _load_toml(self, config_path: Path) -> Dict[str, Any]:
        """Load TOML configuration"""
        with open(config_path, encoding="utf-8") as f:
            return cast(Dict[str, Any], toml.load(f))

    def _save_json(self, config_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON configuration"""
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_yaml(self, config_path: Path, data: Dict[str, Any]) -> None:
        """Save YAML configuration"""
        if not HAS_YAML:
            raise ImportError("PyYAML is required")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)

    def _save_toml(self, config_path: Path, data: Dict[str, Any]) -> None:
        """Save TOML configuration"""
        if not HAS_TOML:
            raise ImportError("toml is required")
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(data, f)

    def _dict_to_config(self, data: Dict[str, Any]) -> AppImageConfig:
        """Convert dictionary to AppImageConfig object"""
        # Filter out keys that don't exist in AppImageConfig
        valid_keys = {
            field.name for field in AppImageConfig.__dataclass_fields__.values()
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}

        return AppImageConfig(**filtered_data)

    def create_sample_config(self, format: str = "yaml") -> str:
        """Create a sample configuration file content"""
        sample_config = AppImageConfig(
            name="My Application",
            version="1.0.0",
            description="A sample Java application packaged as AppImage",
            jar_path="myapp.jar",
            main_class="com.example.MyApp",
            icon="myapp.png",
            category="Development",
            bundled_java=True,
            java_version="11",
            output_dir="./dist",
            validate=True,
            verbose=False,
            author="Your Name",
            license="MIT",
            website="https://github.com/yourname/myapp",
            keywords=["java", "application"],
            dependencies=["lib1.jar", "lib2.jar"],
            java_options=["-Xmx512m", "-Dapp.name=myapp"],
            environment={"JAVA_OPTS": "-Xmx512m"},
        )

        config_data = asdict(sample_config)

        if format.lower() == "json":
            return json.dumps(config_data, indent=2)
        elif format.lower() in ["yaml", "yml"]:
            if not HAS_YAML:
                return "# PyYAML is required for YAML format\n" + json.dumps(
                    config_data, indent=2
                )
            return yaml.dump(
                config_data, default_flow_style=False, allow_unicode=True, indent=2
            )
        elif format.lower() == "toml":
            if not HAS_TOML:
                return "# toml is required for TOML format\n" + json.dumps(
                    config_data, indent=2
                )
            return toml.dumps(config_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def validate_config(self, config: Optional[AppImageConfig] = None) -> List[str]:
        """Validate configuration and return list of issues"""
        config = config or self.current_config
        issues = []
        logger.debug("Validating configuration")

        # Check required fields
        if not config.jar_path:
            issues.append("jar_path is required")
        elif not Path(config.jar_path).exists():
            issues.append(f"JAR file not found: {config.jar_path}")

        # Validate icon if specified
        if config.icon and not Path(config.icon).exists():
            issues.append(f"Icon file not found: {config.icon}")

        # Validate category
        valid_categories = [
            "AudioVideo",
            "Development",
            "Education",
            "Game",
            "Graphics",
            "Network",
            "Office",
            "Science",
            "Settings",
            "System",
            "Utility",
        ]
        if config.category and config.category not in valid_categories:
            issues.append(
                f"Invalid category: {config.category}. Valid: {', '.join(valid_categories)}"
            )

        # Validate output directory
        output_path = Path(config.output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(
                    f"Cannot create output directory {config.output_dir}: {e}"
                )

        # Validate dependencies and libraries
        for dep in config.dependencies or []:
            if not Path(dep).exists():
                issues.append(f"Dependency not found: {dep}")

        for lib in config.libraries or []:
            if not Path(lib).exists():
                issues.append(f"Library not found: {lib}")

        if issues:
            logger.warning(f"Configuration validation failed with {len(issues)} issues")
        else:
            logger.debug("Configuration validation passed")

        return issues


class ConfigTemplate:
    """Templates for different types of applications"""

    @staticmethod
    def cli_app(name: str, jar_path: str, main_class: str) -> AppImageConfig:
        """Template for CLI applications"""
        return AppImageConfig(
            name=name,
            jar_path=jar_path,
            main_class=main_class,
            category="Utility",
            terminal=True,
            bundled_java=True,
            java_options=["-Xmx256m"],
        )

    @staticmethod
    def gui_app(
        name: str, jar_path: str, main_class: str, icon: Optional[str] = None
    ) -> AppImageConfig:
        """Template for GUI applications"""
        return AppImageConfig(
            name=name,
            jar_path=jar_path,
            main_class=main_class,
            icon=icon,
            category="Development",
            terminal=False,
            bundled_java=True,
            startup_notify=True,
            java_options=["-Xmx512m", "-Dswing.aatext=true"],
        )

    @staticmethod
    def enterprise_app(name: str, jar_path: str, main_class: str) -> AppImageConfig:
        """Template for enterprise applications"""
        return AppImageConfig(
            name=name,
            jar_path=jar_path,
            main_class=main_class,
            category="Office",
            bundled_java=True,
            java_version="11",
            validate=True,
            verbose=True,
            java_options=["-Xmx1g", "-server", "-XX:+UseG1GC"],
            environment={"JAVA_OPTS": "-Xmx1g -server"},
        )

    @staticmethod
    def game(name: str, jar_path: str, main_class: str) -> AppImageConfig:
        """Template for Java games"""
        return AppImageConfig(
            name=name,
            jar_path=jar_path,
            main_class=main_class,
            icon=f"{name.lower()}.png",
            category="Game",
            terminal=False,
            bundled_java=True,
            java_options=["-Xmx2g", "-XX:+UseG1GC", "-Dsun.java2d.opengl=true"],
        )


# Utility functions
def load_config_from_file(config_path: str) -> AppImageConfig:
    """Convenient function to load config from file"""
    manager = ConfigManager()
    return manager.load_config(config_path)


def auto_discover_config(working_dir: str = ".") -> Optional[AppImageConfig]:
    """Convenient function to auto-discover config"""
    manager = ConfigManager()
    return manager.auto_discover_config(working_dir)


def create_sample_config_file(output_path: str, format: str = "yaml") -> str:
    """Create a sample configuration file"""
    manager = ConfigManager()
    sample_content = manager.create_sample_config(format)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    return sample_content


if __name__ == "__main__":
    import argparse

    # Setup logging for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(
        description="jar2appimage configuration management"
    )
    parser.add_argument(
        "action",
        choices=["create-sample", "validate", "show"],
        help="Action to perform",
    )
    parser.add_argument("--file", "-f", help="Configuration file path")
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "toml"],
        default="yaml",
        help="Config format",
    )
    parser.add_argument("--output", "-o", help="Output file for sample config")

    args = parser.parse_args()

    if args.action == "create-sample":
        if not args.output:
            print("Error: --output is required for create-sample action")
            sys.exit(1)

        create_sample_config_file(args.output, args.format)
        print(f"✅ Sample configuration created: {args.output}")

    elif args.action == "validate":
        if not args.file:
            print("Error: --file is required for validate action")
            sys.exit(1)

        try:
            manager = ConfigManager()
            config = manager.load_config(args.file)
            issues = manager.validate_config(config)

            if issues:
                print("❌ Configuration validation failed:")
                for issue in issues:
                    print(f"  • {issue}")
                sys.exit(1)
            else:
                print("✅ Configuration is valid")
        except Exception as e:
            print(f"❌ Error validating configuration: {e}")
            sys.exit(1)

    elif args.action == "show":
        if not args.file:
            print("Error: --file is required for show action")
            sys.exit(1)

        try:
            manager = ConfigManager()
            config = manager.load_config(args.file)
            print(json.dumps(asdict(config), indent=2))
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            sys.exit(1)
