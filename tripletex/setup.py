import setuptools

setuptools.setup(
    name="cyb-tripletex",
    version="0.0.1",
    packages=setuptools.find_packages(include=["tripletex"]),
    install_requires=[
        # Do not allow black to put these on one line. It seems Renovate has
        # trouble updating this if it goes in one line.
        # fmt: off
        "requests>=2.26.0",
        # fmt: on
    ],
    extras_require={
        "dev": [
            # Do not allow black to put these on one line. It seems Renovate has
            # trouble updating this if it goes in one line.
            # fmt: off
            "pytest>=6.2.5",
            "wheel",
            # fmt: on
        ]
    }
)
