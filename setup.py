from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tileclipper',
    version='0.8',
    description='The `TileClipper` package enables users to download map tiles within a specified bounding box from a tile server',
    author='Sijan Dhungana',
    author_email='sijandhungana35@gmail.com',
    packages=find_packages(),
    package_data={'tileclipper': ['tileclipper/docs/user_guide.md']},
    license='GPLv3',
    install_requires=[
        'requests',
        'pyproj',
        'tqdm'
        # Add other dependencies here if needed
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)