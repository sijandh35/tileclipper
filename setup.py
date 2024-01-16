from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as rh:
    install_requires = rh.read()

setup(
    name='tileclipper',
    version='0.8',
    description='The `TileClipper` package enables users to download map tiles within a specified bounding box from a tile server',
    author='Sijan Dhungana',
    author_email='sijandhungana35@gmail.com',
    packages=find_packages(),
    package_data={'tileclipper': ['tileclipper/docs/user_guide.md']},
    license='GPLv3',
    url='https://github.com/sijandh35/tileclipper',
    install_requires=install_requires,
    keywords=['map', 'tile', 'clip', 'download', 'tileclipper'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3.8',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)