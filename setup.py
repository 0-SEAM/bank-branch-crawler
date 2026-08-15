from setuptools import find_packages, setup


setup(
    name="daedeok-bank-branch-crawler",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    install_requires=[
        "beautifulsoup4>=4.12,<5",
        "requests>=2.32,<3",
        "urllib3<2; python_version < '3.10'",
    ],
    extras_require={"test": ["pytest>=8.0,<9"]},
)
