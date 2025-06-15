#!/usr/bin/env python3
"""
Setup script for Social Media Content Recommendation System
Includes both Module 1 (Main System) and Module 2 (Enhanced Goal Handler)
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure Python 3.8+
if sys.version_info < (3, 8):
    sys.exit('Python 3.8 or higher is required')

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Social Media Content Recommendation System with AI-powered analytics"

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments, empty lines, and built-in modules
                if (line and 
                    not line.startswith('#') and 
                    not line.startswith('io ') and
                    not line.startswith('json ') and
                    not line.startswith('logging ') and
                    not line.startswith('datetime ') and
                    not line.startswith('threading ') and
                    not line.startswith('asyncio ') and
                    not line.startswith('traceback ') and
                    not line.startswith('time ') and
                    not line.startswith('sys ') and
                    not line.startswith('os ') and
                    not line.startswith('re ') and
                    not line.startswith('pathlib ') and
                    not line.startswith('argparse ')):
                    requirements.append(line)
    
    return requirements

setup(
    name="social-media-recommendation-system",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered social media content recommendation system with advanced analytics",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/social-media-recommendation-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'gpu': [
            'torch[cuda]>=1.6.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'social-media-rec=main:main',
            'smr-api=api:main',
            'smr-module2=Module2.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=['social-media', 'ai', 'recommendation-system', 'content-generation', 'analytics'],
    project_urls={
        'Documentation': 'https://github.com/yourusername/social-media-recommendation-system#readme',
        'Source': 'https://github.com/yourusername/social-media-recommendation-system',
        'Tracker': 'https://github.com/yourusername/social-media-recommendation-system/issues',
    },
) 