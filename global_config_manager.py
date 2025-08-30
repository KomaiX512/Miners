"""
GLOBAL CONFIGURATION MANAGER - CRITICAL ACCOUNT INFO HANDLER
This module ensures info.json (inf.json) is ALWAYS globally accessible to every module.
Prevents the critical error: "CRITICAL: Twitter Account info (info.json) missing"

NEVER MODIFY THIS FILE WITHOUT UNDERSTANDING THE GLOBAL IMPACT.
"""

import json
import logging
import os
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class GlobalConfigManager:
    """
    CRITICAL: Global manager ensuring account info is ALWAYS accessible.
    This prevents the fatal 'info.json missing' error across all modules.
    """
    
    _instance = None
    _account_config = None
    _config_loaded = False
    
    def __new__(cls):
        """Singleton pattern - ensure only one instance globally."""
        if cls._instance is None:
            cls._instance = super(GlobalConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize global config manager."""
        if not self._config_loaded:
            self.load_account_config()
    
    def load_account_config(self, force_reload: bool = False) -> bool:
        """
        CRITICAL: Load account configuration from inf.json (info.json).
        This MUST be called at startup to prevent global failures.
        """
        if self._config_loaded and not force_reload:
            return True
        
        # Define possible config file paths
        config_paths = [
            'inf.json',          # Current file name
            'info.json',         # Expected file name
            './inf.json',        # Relative path
            './info.json',       # Relative path
            os.path.join(os.getcwd(), 'inf.json'),    # Absolute path
            os.path.join(os.getcwd(), 'info.json'),   # Absolute path
        ]
        
        config_loaded = False
        
        for config_path in config_paths:
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._account_config = json.load(f)
                    
                    # Validate CRITICAL fields
                    if self._validate_account_config():
                        logger.info(f"✅ GLOBAL CONFIG: Successfully loaded account info from {config_path}")
                        logger.info(f"📊 Primary Username: {self._account_config.get('username', 'N/A')}")
                        logger.info(f"📊 Account Type: {self._account_config.get('accountType', 'N/A')}")
                        logger.info(f"📊 Posting Style: {self._account_config.get('postingStyle', 'N/A')}")
                        logger.info(f"📊 Platform: {self._account_config.get('platform', 'N/A')}")
                        
                        self._config_loaded = True
                        config_loaded = True
                        break
                    else:
                        logger.warning(f"⚠️ GLOBAL CONFIG: Invalid config structure in {config_path}")
                        
            except Exception as e:
                logger.warning(f"⚠️ GLOBAL CONFIG: Failed to load {config_path}: {str(e)}")
                continue
        
        if not config_loaded:
            logger.warning("⚠️ No root-level info.json found – proceeding with dynamic, per-account configuration only.")
            self._account_config = {}
            self._config_loaded = True
            return True
        
        return config_loaded
    
    def _validate_account_config(self) -> bool:
        """Validate that account config has all CRITICAL fields."""
        if not self._account_config:
            return False
        
        # CRITICAL fields that MUST be present
        critical_fields = ['username', 'platform']
        
        # Check for account type (multiple possible names)
        account_type_fields = ['accountType', 'account_type']
        has_account_type = any(field in self._account_config for field in account_type_fields)
        
        # Check for posting style (multiple possible names) 
        posting_style_fields = ['postingStyle', 'posting_style']
        has_posting_style = any(field in self._account_config for field in posting_style_fields)
        
        # Validate all critical fields
        for field in critical_fields:
            if field not in self._account_config or not self._account_config[field]:
                logger.error(f"🚨 CRITICAL FIELD MISSING: {field}")
                return False
        
        if not has_account_type:
            logger.warning("⚠️ Optional field 'accountType' missing – defaulting to 'personal'.")
        if not has_posting_style:
            logger.warning("⚠️ Optional field 'postingStyle' missing – defaulting to 'casual'.")
        
        return True
    
    def _create_emergency_fallback(self) -> Dict:
        """Create emergency fallback config to prevent complete system failure."""
        fallback_config = {
            'username': 'emergency_fallback',
            'accountType': 'personal',
            'postingStyle': 'casual',
            'platform': 'twitter',
            'competitors': [],
            'timestamp': '2025-08-02T00:00:00.000Z',
            'status': 'emergency_fallback'
        }
        logger.warning("🚨 USING EMERGENCY FALLBACK CONFIG - System may not function correctly!")
        return fallback_config
    
    def get_account_config(self) -> Dict:
        """Get the complete account configuration."""
        if not self._config_loaded:
            self.load_account_config()
        return self._account_config or {}
    
    def reset(self):
        """Completely reset global configuration (use between accounts)."""
        self._account_config = {}
        self._config_loaded = False

    def get_primary_username(self) -> str:
        """Get the primary username from config. Returns empty string if not yet set or empty."""
        config = self.get_account_config()
        username = config.get('username', '') if config else ''
        # Treat empty/whitespace username as not configured
        # CRITICAL FIX: Return empty string when no config file exists to allow scraped data to be used
        return username.strip()
    
    def get_account_type(self) -> str:
        """Get account type (branding/personal) from config."""
        config = self.get_account_config()
        # Check multiple possible field names
        # CRITICAL FIX: Return empty string when no config file exists to allow scraped data to be used
        account_type = (config.get('accountType') or 
                config.get('account_type') or 
                '')
        return account_type
    
    def get_posting_style(self) -> str:
        """Get posting style from config."""
        config = self.get_account_config()
        # Check multiple possible field names
        # CRITICAL FIX: Return empty string when no config file exists to allow scraped data to be used
        posting_style = (config.get('postingStyle') or 
                config.get('posting_style') or 
                '')
        return posting_style
    
    def get_platform(self) -> str:
        """Get platform from config."""
        config = self.get_account_config()
        return config.get('platform', 'twitter')
    
    def get_competitors(self) -> list:
        """Get competitors list from config."""
        config = self.get_account_config()
        return config.get('competitors', [])
    
    def update_config(self, updates: Dict) -> bool:
        """Update configuration with new values."""
        try:
            if not self._account_config:
                self.load_account_config()
            
            self._account_config.update(updates)
            
            # Save back to file
            config_file = 'inf.json' if os.path.exists('inf.json') else 'info.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._account_config, f, indent=2)
            
            logger.info(f"✅ GLOBAL CONFIG: Updated configuration in {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"🚨 GLOBAL CONFIG: Failed to update config: {str(e)}")
            return False
    
    def ensure_config_available(self) -> bool:
        """
        CRITICAL: Ensure config is loaded and available.
        Call this before any operation that needs account info.
        """
        if not self._config_loaded:
            return self.load_account_config()
        return True
    
    def get_config_status(self) -> Dict:
        """Get status of global configuration."""
        return {
            'loaded': self._config_loaded,
            'config_available': self._account_config is not None,
            'primary_username': self.get_primary_username(),
            'account_type': self.get_account_type(),
            'posting_style': self.get_posting_style(),
            'platform': self.get_platform(),
            'competitors_count': len(self.get_competitors())
        }

# GLOBAL INSTANCE - Import this in any module that needs account config
global_config = GlobalConfigManager()

def get_global_config() -> GlobalConfigManager:
    """
    CRITICAL: Get the global configuration manager instance.
    Use this in any module that needs account information.
    """
    return global_config

def ensure_global_config() -> bool:
    """
    CRITICAL: Ensure global configuration is loaded.
    Call this at the start of any module that needs account info.
    """
    return global_config.ensure_config_available()

def get_account_info() -> Dict:
    """
    CRITICAL: Get complete account information.
    This replaces all individual info.json loading attempts.
    """
    global_config.ensure_config_available()
    return global_config.get_account_config()

# Convenience functions for direct access
def get_primary_username() -> str:
    """Get primary username globally."""
    global_config.ensure_config_available()
    return global_config.get_primary_username()

def get_account_type() -> str:
    """Get account type globally."""
    global_config.ensure_config_available()
    return global_config.get_account_type()

def get_posting_style() -> str:
    """Get posting style globally."""
    global_config.ensure_config_available()
    return global_config.get_posting_style()

def get_platform() -> str:
    """Get platform globally."""
    global_config.ensure_config_available()
    return global_config.get_platform()

def get_competitors() -> list:
    """Get competitors list globally."""
    global_config.ensure_config_available()
    return global_config.get_competitors()
