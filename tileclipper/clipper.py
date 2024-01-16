import requests
import os
from math import floor, pi, log, tan, cos
from concurrent.futures import ThreadPoolExecutor
import pyproj
import gc
import logging
from tqdm import tqdm

class TileClipper:
    def __init__(self, base_url, bbox, output_folder, max_workers=10, aws_access_key=None, aws_secret_key=None, s3_bucket=None,use_s3=False):
        self.base_url = base_url
        self.bbox = bbox
        self.output_folder = output_folder
        self.max_workers = max_workers
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.s3_bucket = s3_bucket
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def are_coordinates_in_epsg4326(self, bbox):
        min_lon, min_lat, max_lon, max_lat = bbox
        return (-180 <= min_lon <= 180) and (-90 <= min_lat <= 90) and (-180 <= max_lon <= 180) and (-90 <= max_lat <= 90)

    def convert_epsg3857_to_epsg4326(self, minx, miny, maxx, maxy):
        in_proj = pyproj.CRS('EPSG:3857')
        out_proj = pyproj.CRS('EPSG:4326')
        transformer = pyproj.Transformer.from_crs(in_proj, out_proj, always_xy=True)
        min_lon, min_lat = transformer.transform(minx, miny)
        max_lon, max_lat = transformer.transform(maxx, maxy)
        return min_lon, min_lat, max_lon, max_lat

    def long2tile(self, lon, zoom):
        return floor((lon + 180) / 360 * (2 ** zoom))

    def lat2tile(self, lat, zoom):
        return floor((1 - log(tan(lat * pi / 180) + 1 / cos(lat * pi / 180)) / pi) / 2 * (2 ** zoom))

    def bbox2tiles(self, zoom, bbox):
        min_lon, min_lat, max_lon, max_lat = bbox
        x_min = self.long2tile(min_lon, zoom)
        y_min = self.lat2tile(max_lat, zoom)
        x_max = self.long2tile(max_lon, zoom)
        y_max = self.lat2tile(min_lat, zoom)
        return range(x_min, x_max + 1), range(y_min, y_max + 1)

    def download_tile(self, x, y, zoom):
      self.logger.info(f"Zoom Level: {zoom}")
      tile_url = self.base_url.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
      response = requests.get(tile_url)
      if response.status_code == 200:
          directory = os.path.join(self.output_folder, f"{zoom}/{x}/")
          os.makedirs(directory, exist_ok=True)
          filename = tile_url.split('/')[-1] + '.png'
          with open(os.path.join(directory, filename), 'wb') as file:
              file.write(response.content)
          self.logger.info(f"Tile downloaded successfully to: {directory}{filename}")
      else:
          pass

    def download_tiles(self, zoom_start, zoom_end):
        epsg3857_bbox = self.bbox
        min_lon, min_lat, max_lon, max_lat = self.convert_epsg3857_to_epsg4326(*epsg3857_bbox) if not self.are_coordinates_in_epsg4326(epsg3857_bbox) else epsg3857_bbox
        bbox_coords = (min_lon, min_lat, max_lon, max_lat)
        self.logger.info(f"BBOX COORDS: {bbox_coords}")

        for zoom_level in range(zoom_start, zoom_end + 1):
            x_tiles, y_tiles = self.bbox2tiles(zoom_level, bbox_coords)
            total_tiles = len(x_tiles) * len(y_tiles)
            with tqdm(total=total_tiles, desc=f"Downloading Zoom Level {zoom_level}", unit="tiles") as pbar:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self.download_tile_with_progress, x, y, zoom_level, pbar) for x in x_tiles for y in y_tiles]
                    for future in futures:
                        future.result()
                    del futures
                    gc.collect()

    def download_tile_with_progress(self, x, y, zoom, progress_bar):
        self.logger.info(f"Zoom Level: {zoom}")
        tile_url = self.base_url.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
        response = requests.get(tile_url)
        if response.status_code == 200:
            directory = os.path.join(self.output_folder, f"{zoom}/{x}/")
            os.makedirs(directory, exist_ok=True)
            filename = tile_url.split('/')[-1] + '.png'
            with open(os.path.join(directory, filename), 'wb') as file:
                file.write(response.content)
            self.logger.info(f"Tile downloaded successfully to: {directory}{filename}")
        else:
            pass
        progress_bar.update(1)