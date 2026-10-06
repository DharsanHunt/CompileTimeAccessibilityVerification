"""Setup configuration for A11yCC compiler package."""

from setuptools import setup, find_packages

setup(
    name="a11ycc",
    version="1.0.0",
    description="A11yCC: Compile-Time Accessibility Verification for Declarative UI DSL",
    author="DharsanHunt",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "a11ycc=a11ycc.cli:cli_main",
            "kanaforge=a11ycc.cli:cli_main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Compilers",
        "Topic :: Accessibility",
    ],
)
