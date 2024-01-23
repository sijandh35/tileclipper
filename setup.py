from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tileclipper',
    version='1.0.1',
    description='The `TileClipper` package enables users to download map tiles within a specified bounding box from a tile server',
    author='Sijan Dhungana',
    author_email='sijandhungana35@gmail.com',
    packages=find_packages(),
    package_data={'tileclipper': ['tileclipper/docs/user_guide.md']},
    license='GPLv3',
    url='https://github.com/sijandh35/tileclipper',
    install_requires=['requests==2.31.0','pyproj==3.6.1','tqdm==4.66.1', "boto3==1.24.54"],
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
