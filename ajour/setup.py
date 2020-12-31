import setuptools

setuptools.setup(
    name="cyb-ajour",
    version="0.0.1",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    entry_points={"console_scripts": ["ajour = cybajour.cli:main"]},
    python_requires='>=3.6',
    install_requires=[
        "colorama==0.4.4",
        "numpy==1.19.4",
        "pandas==1.2.0",
        "reportlab==3.5.57",
    ]
)
