"""Setup configuration for cli-anything-aseprite."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-aseprite",
    version="0.1.0",
    description="Stateful CLI harness for Aseprite pixel art editor",
    author="cli-anything",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.aseprite": ["skills/SKILL.md"],
    },
    install_requires=[
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-aseprite=cli_anything.aseprite.aseprite_cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
