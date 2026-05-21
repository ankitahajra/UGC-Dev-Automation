"""
Setup script for Azure Function Auto-Diagnose and Auto-Fix Pipeline
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="azure-function-autofix-pipeline",
    version="1.0.0",
    author="BOB ICA Team",
    author_email="team@example.com",
    description="Automated failure detection, analysis, and remediation for Azure Functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/cron-job-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "autofix-pipeline=main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="azure functions monitoring automation devops ci-cd",
    project_urls={
        "Bug Reports": "https://github.com/your-org/cron-job-automation/issues",
        "Source": "https://github.com/your-org/cron-job-automation",
        "Documentation": "https://github.com/your-org/cron-job-automation/blob/main/README.md",
    },
)

# Made with Bob
