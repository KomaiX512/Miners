"""
Centralized Test Detection and Filtering Utility
Provides comprehensive test data filtering across all pipeline modules
with future-proof mechanisms to prevent test data execution in production.
"""

import re
from typing import List, Set, Dict, Any
from utils.logging import logger

class TestFilter:
    """
    Comprehensive test detection and filtering utility.
    Provides centralized test identification across all pipeline modules.
    """
    
    # 🚫 COMPREHENSIVE TEST INDICATORS - Exhaustive list for future-proofing
    TEST_INDICATORS: Set[str] = {
        # Basic test keywords
        "test", "testing", "tests",
        "demo", "demonstration", "demos",
        "sample", "samples", "sampling",
        "example", "examples", "ex",
        "mock", "mocking", "mocks",
        "fake", "fakes", "dummy", "dummies",
        
        # Development keywords
        "dev", "develop", "development", "developer",
        "debug", "debugging", "debugger",
        "trial", "trials", "experiment", "experimental", "experiments",
        "prototype", "prototyping", "prototypes",
        "poc", "proof-of-concept", "proofofconcept",
        
        # Environment keywords
        "staging", "stage", "stg",
        "qa", "quality", "qc", "quality-control",
        "uat", "user-acceptance-testing",
        "sandbox", "sandboxes", "sb",
        "temp", "temporary", "tmp",
        "local", "localhost", "127.0.0.1",
        
        # Status keywords
        "draft", "drafts", "wip", "work-in-progress",
        "pending", "review", "reviewing",
        "abandoned", "deprecated", "obsolete",
        "backup", "backups", "bak",
        
        # Validation keywords
        "validation", "validate", "validator",
        "verification", "verify", "verifier",
        "check", "checking", "checker",
        "eval", "evaluation", "evaluator",
        
        # Organization keywords
        "internal", "private", "confidential",
        "admin", "administrator", "root",
        "system", "sys", "service", "svc",
        "bot", "automated", "auto", "script",
        
        # Time-based keywords
        "old", "legacy", "archive", "archived",
        "new", "latest", "recent", "current",
        "2023", "2024", "2025", "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec",
        
        # Pattern keywords
        "placeholder", "lorem", "ipsum",
        "hello", "world", "helloworld",
        "foo", "bar", "baz", "qux",
        "user1", "user2", "user3", "account1", "account2"
    }
    
    # 🔍 ADVANCED PATTERN DETECTION
    TEST_PATTERNS: List[str] = [
        r"test.*\d+",           # test1, test123, testing1
        r"\d+.*test",           # 1test, 123testing
        r"demo.*\d+",           # demo1, demo123
        r"sample.*\d+",         # sample1, sample123
        r"user\d+",             # user1, user123
        r"account\d+",          # account1, account123
        r"temp.*\d+",           # temp1, temp123
        r"dev.*\d+",            # dev1, dev123
        r"qa.*\d+",             # qa1, qa123
        r".*test$",             # mytest, usertest
        r".*demo$",             # mydemo, userdemo
        r"^test.*",             # test_anything
        r"^demo.*",             # demo_anything
        r"^sample.*",           # sample_anything
        r".*validation.*",      # any_validation_text
        r".*experiment.*",      # any_experiment_text
    ]
    
    @classmethod
    def is_test_data(cls, identifier: str, context: str = "") -> bool:
        """
        🎯 COMPREHENSIVE TEST DETECTION
        Determines if an identifier (username, filename, path) represents test data.
        
        Args:
            identifier: The string to check (username, filename, path, etc.)
            context: Additional context for detection
            
        Returns:
            bool: True if identified as test data, False otherwise
        """
        if not identifier:
            return False
            
        # Normalize identifier for checking
        clean_identifier = identifier.lower().strip()
        
        # 🔍 STRATEGY 1: Direct keyword matching
        if cls._check_direct_keywords(clean_identifier):
            logger.debug(f"🚫 Test data detected via keywords: {identifier}")
            return True
            
        # 🔍 STRATEGY 2: Pattern matching
        if cls._check_patterns(clean_identifier):
            logger.debug(f"🚫 Test data detected via patterns: {identifier}")
            return True
            
        # 🔍 STRATEGY 3: Context-based detection
        if context and cls._check_context(clean_identifier, context.lower()):
            logger.debug(f"🚫 Test data detected via context: {identifier} (context: {context})")
            return True
            
        # 🔍 STRATEGY 4: Structural analysis
        if cls._check_structure(clean_identifier):
            logger.debug(f"🚫 Test data detected via structure: {identifier}")
            return True
            
        return False
    
    @classmethod
    def _check_direct_keywords(cls, identifier: str) -> bool:
        """Check for direct keyword matches"""
        # Split identifier by common separators
        parts = re.split(r'[_\-\.\s/\\]+', identifier)
        
        for part in parts:
            if part in cls.TEST_INDICATORS:
                return True
                
        # Check full identifier for exact matches (not substrings)
        # This prevents false positives like "foodblogger" containing "blog"
        for indicator in cls.TEST_INDICATORS:
            # Only match if indicator is a complete word or at word boundaries
            pattern = rf'\b{re.escape(indicator)}\b'
            if re.search(pattern, identifier, re.IGNORECASE):
                return True
                
        return False
    
    @classmethod
    def _check_patterns(cls, identifier: str) -> bool:
        """Check for pattern matches"""
        for pattern in cls.TEST_PATTERNS:
            if re.search(pattern, identifier, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _check_context(cls, identifier: str, context: str) -> bool:
        """Check context for test indicators"""
        combined = f"{identifier} {context}"
        
        # Be more specific about context checking to avoid false positives
        test_context_patterns = [
            r'\btest\b', r'\bdemo\b', r'\bsample\b', r'\bvalidation\b',
            r'\bexperiment\b', r'\bprototype\b', r'\btemp\b', r'\bdev\b'
        ]
        
        for pattern in test_context_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
                
        return False
    
    @classmethod
    def _check_structure(cls, identifier: str) -> bool:
        """Check structural patterns that indicate test data"""
        # Very short usernames (likely test) - but allow common short names
        if len(identifier) <= 2 and identifier not in ['ai', 'io', 'us', 'uk', 'tv', 'fm']:
            return True
            
        # All numbers
        if identifier.isdigit():
            return True
            
        # Repeated characters (like aaaa, bbbb) - but allow some legitimate cases
        if len(set(identifier)) <= 2 and len(identifier) > 4:
            return True
            
        # Contains 'validation' anywhere - clear test indicator
        if 'validation' in identifier.lower():
            return True
            
        # Sequential patterns like user1, user2, account1, etc.
        if re.match(r'^(user|account|test|demo)\d+$', identifier, re.IGNORECASE):
            return True
            
        return False
    
    @classmethod
    def filter_test_files(cls, file_list: List[str]) -> List[str]:
        """
        Filter out test files from a list of file paths.
        
        Args:
            file_list: List of file paths to filter
            
        Returns:
            List of production file paths (test files removed)
        """
        production_files = []
        test_files = []
        
        for file_path in file_list:
            if cls.is_test_data(file_path, "file_path"):
                test_files.append(file_path)
                logger.debug(f"🚫 Filtered out test file: {file_path}")
            else:
                production_files.append(file_path)
        
        if test_files:
            logger.info(f"🧹 Filtered out {len(test_files)} test files from pipeline")
            
        return production_files
    
    @classmethod
    def filter_test_objects(cls, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out test objects from R2 object list.
        
        Args:
            objects: List of R2 objects with 'Key' field
            
        Returns:
            List of production objects (test objects removed)
        """
        production_objects = []
        test_objects = []
        
        for obj in objects:
            key = obj.get("Key", "")
            if cls.is_test_data(key, "r2_object"):
                test_objects.append(obj)
                logger.debug(f"🚫 Filtered out test object: {key}")
            else:
                production_objects.append(obj)
        
        if test_objects:
            logger.info(f"🧹 Filtered out {len(test_objects)} test objects from pipeline")
            
        return production_objects
    
    @classmethod
    def should_skip_processing(cls, platform: str, username: str, additional_context: str = "") -> bool:
        """
        🛡️ MAIN PRODUCTION FILTER
        Determines if processing should be skipped for test data.
        
        Args:
            platform: Platform name (instagram, twitter, etc.)
            username: Username to check
            additional_context: Additional context (file path, etc.)
            
        Returns:
            bool: True if processing should be skipped (test data detected)
        """
        # Check username
        if cls.is_test_data(username, f"username {platform}"):
            logger.info(f"🚫 PRODUCTION FILTER: Skipping test user '{username}' on {platform}")
            return True
            
        # Check platform for test indicators
        if cls.is_test_data(platform, "platform"):
            logger.info(f"🚫 PRODUCTION FILTER: Skipping test platform '{platform}'")
            return True
            
        # Check additional context
        if additional_context and cls.is_test_data(additional_context, "context"):
            logger.info(f"🚫 PRODUCTION FILTER: Skipping due to test context '{additional_context}'")
            return True
            
        return False
    
    @classmethod
    def log_production_user(cls, platform: str, username: str, action: str = "processing"):
        """Log production user processing for monitoring"""
        logger.info(f"✅ PRODUCTION USER: {action} '{username}' on {platform}")
    
    @classmethod
    def add_custom_test_indicator(cls, indicator: str):
        """Add custom test indicator for future-proofing"""
        cls.TEST_INDICATORS.add(indicator.lower())
        logger.info(f"📝 Added custom test indicator: {indicator}")
    
    @classmethod
    def get_test_statistics(cls, objects: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about test vs production data"""
        test_count = 0
        production_count = 0
        
        for obj in objects:
            key = obj.get("Key", "")
            if cls.is_test_data(key):
                test_count += 1
            else:
                production_count += 1
                
        return {
            "test_files": test_count,
            "production_files": production_count,
            "total_files": len(objects),
            "test_percentage": (test_count / len(objects) * 100) if objects else 0
        } 