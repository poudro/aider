"""
Setup for the Aider Agent package.
"""
from setuptools import find_packages, setup

setup(
    name="aider_agent",
    version="0.1.0",
    packages=find_packages(),
    description="Agent mode for Aider.",
    long_description=open("README.md").read(),
)
