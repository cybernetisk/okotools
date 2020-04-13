import setuptools

setuptools.setup(
    name="cyb-ajour",
    version="0.0.1",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    entry_points={"console_scripts": ["ajour = cybajour.cli:main"]},
    python_requires='>=3.6',
    install_requires=[
        "colorama==0.4.3",
        "numpy==1.18.1",
        "pandas==1.0.1",
    ]
)
