### TileClipper Package Usage Guide

#### Introduction

The `TileClipper` package enables users to download map tiles within a specified bounding box from a tile server. This guide illustrates the installation process, instantiation of the `TileClipper` class, and downloading map tiles using the package.

#### Installation

Ensure Python is installed on your system, then install the `TileClipper` package using `pip`:

```sh
pip install tileclipper
```


```python
from tileclipper import TileClipper
```

#### Instantiate TileClipper

Define the required parameters for the TileClipper class:

    base_url (str): Base URL of the tile server.
    bbox (list): Bounding box coordinates [minx, miny, maxx, maxy].
    output_folder (str): Directory to save downloaded tiles.
    max_workers (int, optional): Maximum number of concurrent workers for tile downloads (default is 10).

Create an instance of the TileClipper class:

```python

base_url = "https://example.com/tiles/"  # Replace with your tile server URL
bbox = [xmin, ymin, xmax, ymax]  # Replace with bounding box coordinates
output_folder = "/path/to/output/folder/"  # Replace with output folder path
max_workers = 10  # Optional: Set maximum workers for concurrent downloads

tileclipper = TileClipper(base_url, bbox, output_folder, max_workers)

```

Download Tiles

Utilize the download_tiles(zoom_start, zoom_end) method to download tiles within a specified zoom level range:

```python

    # Download tiles within zoom level range 18 to 20
    tileclipper.download_tiles(18, 20)

```

Example

Here's an example demonstrating the usage of the TileClipper class:

```python

from tileclipper import TileClipper

base_url = "https://example.com/tiles/"
bbox = [xmin, ymin, xmax, ymax]
output_folder = "/path/to/output/folder/"
max_workers = 10

tileclipper = TileClipper(base_url, bbox, output_folder, max_workers)
tileclipper.download_tiles(18, 20)
    
```

Replace the placeholder values (base_url, bbox, output_folder, etc.) with your specific values according to your use case.