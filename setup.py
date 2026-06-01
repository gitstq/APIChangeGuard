"""
APIChangeGuard - 轻量级API变更智能检测与影响分析引擎
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="apichangeguard",
    version="1.0.0",
    author="APIChangeGuard Team",
    author_email="contact@apichangeguard.dev",
    description="轻量级API变更智能检测与影响分析引擎",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/APIChangeGuard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "apichangeguard=apichangeguard.cli:main",
            "acg=apichangeguard.cli:main",
        ],
    },
    keywords=[
        "api",
        "openapi",
        "swagger",
        "graphql",
        "diff",
        "comparison",
        "changelog",
        "versioning",
        "compatibility",
        "breaking-changes",
        "ci-cd",
        "testing",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/APIChangeGuard/issues",
        "Source": "https://github.com/yourusername/APIChangeGuard",
        "Documentation": "https://github.com/yourusername/APIChangeGuard/blob/main/README.md",
    },
)
