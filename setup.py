from setuptools import find_packages, setup

__version__ = None  # This will get replaced when reading version.py
exec(open("rlgym_compat/version.py").read())

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="rlgym_compat",
    packages=find_packages(),
    version=__version__,
    description="A library of RLBot compatibility objects for RLGym Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lucas Emery, Matthew Allen, Jonathan Keegan",
    url="https://rlgym.github.io",
    install_requires=[
        "numpy==1.*",
    ],
    python_requires=">=3.11",
    license="Apache 2.0",
    license_file="LICENSE",
    keywords=["rocket-league", "gym", "reinforcement-learning"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
)
