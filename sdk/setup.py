"""Build script for the standalone wmrSim Plugin SDK.

Copyright (C) 2026 宇集創新科技. All Rights Reserved.

Usage::

    python3 -m pip install --break-system-packages build
    python3 -m build --wheel
    python3 -m pip install --break-system-packages dist/*.whl
"""

from setuptools import setup

setup(
    name="wmr-sim-sdk",
    version="1.0.0",
    description="Customer Plugin SDK for wmrSim Multi-AMR Fleet Platform (Release V1.0)",
    long_description=(
        "Customer Plugin SDK for developing custom Global Planners, Local "
        "Controllers, Traffic Managers and Task Managers on the wmrSim "
        "platform. Contains only the public plugin interface; the proprietary "
        "simulation core is distributed separately.\n\n"
        "Copyright (C) 2026 宇集創新科技. All Rights Reserved."
    ),
    author="宇集創新科技",
    packages=["wmr_sim", "wmr_sim.sdk"],
    python_requires=">=3.10",
    install_requires=["numpy"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Robotics",
        "License :: Other/Proprietary License",
    ],
)
