from setuptools import setup

with open('requirements.txt') as f:
    install_packages = f.readlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="PlantBot",
    version="1.0",
    author="jfri3d",
    python_requires='>=3.5',
    description="Smart tracking for when to water plants with a pesky SlackBot!",
    long_description=long_description,
    install_requires=install_packages,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
