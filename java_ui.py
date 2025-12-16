#!/usr/bin/env python3
"""
Java User Interface Module

This module provides user interaction and prompt handling for the Java management system.
Handles complex decision trees, user consent flows, and interactive prompts.

Key Responsibilities:
- User consent and decision making
- Interactive prompts and messaging
- Detailed information display
- Progress and status feedback
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class JavaUserInterface:
    """
    Handles all user interaction and prompt handling for Java operations
    """
    
    def __init__(self, interactive_mode: bool = True):
        """
        Initialize the Java UI handler
        
        Args:
            interactive_mode: Whether to use interactive prompts
        """
        self.interactive_mode = interactive_mode
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging for UI operations"""
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    def offer_portable_java(
        self, 
        download_needed: bool, 
        reason: str, 
        java_version: str,
        download_info: Dict[str, Any],
        current_platform: Dict[str, str]
    ) -> bool:
        """
        Offer to download portable Java with user consent
        
        Args:
            download_needed: Whether download is needed
            reason: Reason for download
            java_version: Java version to download
            download_info: Download information dictionary
            current_platform: Current platform information
            
        Returns:
            True if user consents to download
        """
        if not download_needed:
            logger.info("✅ System Java is sufficient, no download needed")
            return False

        logger.info(f"📥 Portable Java recommended: {reason}")

        if not self.interactive_mode:
            logger.info("🔧 Non-interactive mode: downloading Java automatically")
            return True

        # Display the download offer interface
        self._show_download_offer(java_version, reason, download_info, current_platform)
        
        # Handle user consent
        return self._get_user_consent(java_version, download_info)
    
    def _show_download_offer(
        self, 
        java_version: str, 
        reason: str, 
        download_info: Dict[str, Any],
        current_platform: Dict[str, str]
    ) -> None:
        """
        Display the download offer interface
        
        Args:
            java_version: Java version to download
            reason: Reason for download
            download_info: Download information
            current_platform: Platform information
        """
        print("\n" + "="*60)
        print("🚀 PORTABLE JAVA DETECTION AND DOWNLOAD OFFER")
        print("="*60)
        print("\n📋 Analysis Results:")
        print(f"   • System Java: {'Available' if download_info['has_system_java'] else 'Not found'}")
        print(f"   • Recommendation: Download portable Java {java_version}")
        print(f"   • Reason: {reason}")

        print("\n📦 Download Information:")
        print(f"   • Version: Java {java_version} (LTS)")
        print(f"   • Size: ~{download_info['estimated_size_mb']} MB")
        print("   • Type: JRE (Java Runtime Environment)")
        print(f"   • Architecture: {current_platform['arch']}")
        print(f"   • Download time: ~{download_info['estimated_time_minutes']} minutes")

        print("\n💡 Benefits of Portable Java:")
        print("   • Self-contained AppImage (no external dependencies)")
        print("   • Works on any Linux distribution")
        print("   • Latest security updates and features")
        print("   • Consistent Java version across deployments")

        print("\n⚠️  What will be downloaded:")
        print(f"   • Java {java_version} runtime files")
        print(f"   • Stored in: {download_info.get('cache_dir', 'cache directory')}")
        print("   • Used for creating portable AppImages")
    
    def _get_user_consent(self, java_version: str, download_info: Dict[str, Any]) -> bool:
        """
        Get user consent for download
        
        Args:
            java_version: Java version to download
            download_info: Download information
            
        Returns:
            True if user consents
        """
        while True:
            print(f"\n❓ Do you want to download Java {java_version}?")
            response = input("   [Y]es / [N]o / [I]nfo: ").strip().lower()

            if response in ['y', 'yes']:
                print(f"\n✅ Consent received. Downloading Java {java_version}...")
                return True
            elif response in ['n', 'no']:
                print("\n❌ Download cancelled. Will use system Java if available.")
                return False
            elif response in ['i', 'info']:
                self._show_detailed_download_info(java_version, download_info)
            else:
                print("   Please enter Y, N, or I")
    
    def _show_detailed_download_info(self, java_version: str, download_info: Dict[str, Any]) -> None:
        """
        Show detailed download information
        
        Args:
            java_version: Java version
            download_info: Download information dictionary
        """
        print(f"\n📋 Detailed Information for Java {java_version}:")
        print(f"   • Package Type: {download_info['package_type']} (Java Runtime Environment)")
        print(f"   • Architecture: {download_info['architecture']}")
        print(f"   • Estimated Size: {download_info['estimated_size_mb']} MB")
        print(f"   • Download Time: ~{download_info['estimated_time_minutes']} minutes")
        print(f"   • Cache Location: {download_info.get('cache_dir', 'cache directory')}")
        print("   • Source: Adoptium (Eclipse Temurin)")

        print("\n🔧 Technical Details:")
        print(f"   • Based on OpenJDK {java_version}")
        print("   • Linux x64 compatible")
        print("   • Includes JavaFX (if applicable)")
        print("   • Security updates included")

        print("\n💾 Storage:")
        print("   • Downloaded files cached locally")
        print("   • Reused for future AppImages")
        print("   • Can be cleared with --clear-cache")
    
    def show_java_detection_result(self, java_info: Optional[Dict[str, Any]]) -> None:
        """
        Display Java detection results
        
        Args:
            java_info: Java information dictionary or None if not found
        """
        if java_info:
            print(f"✅ Found Java {java_info['version']} ({java_info['type']})")
            print(f"   Command: {java_info['command']}")
            print(f"   Compatible: {java_info['is_compatible']}")
            if java_info.get('java_home'):
                print(f"   JAVA_HOME: {java_info['java_home']}")
        else:
            print("❌ No compatible Java found")
    
    def show_jar_analysis_results(self, jar_path: str, jar_requirements: Dict[str, Any]) -> None:
        """
        Display JAR analysis results
        
        Args:
            jar_path: Path to JAR file
            jar_requirements: JAR requirements analysis
        """
        print(f"📋 JAR Analysis for {jar_path}:")
        print(f"   Main Class: {jar_requirements.get('main_class', 'Not specified')}")
        print(f"   Requires Modules: {jar_requirements.get('requires_modules', False)}")
    
    def show_cache_info(self, cache_info: Dict[str, Any]) -> None:
        """
        Display cache information
        
        Args:
            cache_info: Cache information dictionary
        """
        print("📦 Java Download Cache:")
        print(f"   Location: {cache_info['cache_dir']}")
        print(f"   Total Files: {cache_info['total_files']}")
        print(f"   Total Size: {cache_info['total_size_mb']} MB")
        print(f"   Java Versions: {', '.join(cache_info['java_versions'])}")
    
    def show_detection_summary(self, summary: Dict[str, Any]) -> None:
        """
        Display Java detection summary
        
        Args:
            summary: Detection summary dictionary
        """
        print("🔍 Java Detection Summary:")
        print(f"   System Java: {'Found' if summary['system_java'] else 'Not found'}")
        print(f"   Latest LTS: {summary['latest_lts']}")
        print(f"   Platform: {summary['platform']['system']} {summary['platform']['arch']}")
        print(f"   Cache: {summary['cache_info']['total_files']} files, {summary['cache_info']['total_size_mb']} MB")
    
    def show_download_progress(self, java_version: str, downloaded_file: str) -> None:
        """
        Show download progress message
        
        Args:
            java_version: Java version being downloaded
            downloaded_file: Path to downloaded file
        """
        print(f"📥 Downloading Java {java_version}...")
        if downloaded_file:
            print(f"✅ Downloaded: {downloaded_file}")
        else:
            print("❌ Download failed")
    
    def show_operation_status(self, operation: str, success: bool, details: str = "") -> None:
        """
        Show operation status message
        
        Args:
            operation: Operation name
            success: Whether operation was successful
            details: Additional details
        """
        status = "✅" if success else "❌"
        message = f"{status} {operation}"
        if details:
            message += f": {details}"
        print(message)