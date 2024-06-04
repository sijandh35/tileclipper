import os
import ast
import boto3
import argparse
import requests
import pyproj
import gc
import logging
from math import floor, pi, log, tan, cos
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from urllib.parse import urlparse

class TileClipper:
    def __init__(self, 
                 base_url, 
                 bbox, 
                 output_folder, 
                 max_workers=10, 
                 use_s3=False,
                 aws_access_key=None, 
                 aws_secret_key=None, 
                 s3_bucket=None,
                 tile_layer_name=None
                 ):
        self.base_url = base_url
        self.bbox = bbox
        self.output_folder = output_folder
        self.max_workers = max_workers
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.s3_bucket = s3_bucket
        self.use_s3 = use_s3
        self.tile_layer_name = tile_layer_name
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
      parsed_url = urlparse(tile_url)
      filename = os.path.basename(parsed_url.path)
      response = requests.get(tile_url)
      if response.status_code == 200:
          directory = os.path.join(self.output_folder, f"{zoom}/{x}/")
          os.makedirs(directory, exist_ok=True)
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
                    futures = [executor.submit(self.download_tile_with_progress_s3 if self.use_s3 else self.download_tile_with_progress_local, x, y, zoom_level, pbar) for x in x_tiles for y in y_tiles]
                    for future in futures:
                        future.result()
                    del futures
                    gc.collect()

    def download_tile_with_progress_local(self, x, y, zoom, progress_bar):
        self.logger.info(f"Zoom Level: {zoom}")
        tile_url = self.base_url.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
        parsed_url = urlparse(tile_url)
        filename = os.path.basename(parsed_url.path)
        response = requests.get(tile_url)
        if response.status_code == 200:
            directory = os.path.join(self.output_folder, f"{zoom}/{x}/")
            os.makedirs(directory, exist_ok=True)
            local_file_path = os.path.join(directory, filename)

            with open(local_file_path, 'wb') as file:
                file.write(response.content)
            self.logger.info(f"Tile downloaded successfully to: {self.output_folder}/{zoom}/{x}/{filename}")
        else:
            pass
        progress_bar.update(1)

    def download_tile_with_progress_s3(self, x, y, zoom, progress_bar):
        self.logger.info(f"Zoom Level: {zoom}")
        tile_url = self.base_url.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
        parsed_url = urlparse(tile_url)
        filename = os.path.basename(parsed_url.path)
        response = requests.get(tile_url)
        if response.status_code == 200:
            s3_client = boto3.client(
                service_name='s3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            if self.tile_layer_name:
                s3_client.put_object(Body=response.content, Bucket=self.s3_bucket, Key=f"{self.tile_layer_name}/{zoom}/{x}/{filename}")
            else:
                s3_client.put_object(Body=response.content, Bucket=self.s3_bucket, Key=f"{zoom}/{x}/{filename}")
            self.logger.info(f"Tile downloaded and uploaded successfully to S3: {self.s3_bucket}/{zoom}/{x}/{filename}")
        else:
            pass
        progress_bar.update(1)



def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Download the tiles for the area from url")
    parser.add_argument("--base_url", required=True, help="Tile url for the tiles you want to download")
    parser.add_argument("--bbox", required=True, help="The bbox for the area you want to download tiles ")
    parser.add_argument(
        "-o", "--output_folder", required=False, help="Output folder name"
    )
    parser.add_argument("-w", "--max_workers", default=10, help="No of workers you want to run")

    parser.add_argument("--zoom_level", required=True, help="The zoom level for which you want to download tiles. Pass in this format:  10-15")

    parser.add_argument("--use_s3", default=False, help="If you want to download tiles into s3 bucket")
    parser.add_argument("--aws_key", required=False, help="Your AWS Key to connect with aws")
    parser.add_argument("--aws_secret", required=False, help="Your aws secret to connect with aws")
    parser.add_argument("--bucket" ,required=False, help="S3 bucket where you want to download the tiles")
    parser.add_argument("--layer", required=False, help="The layer name in s3 bucket where you want the tiles")

    args = parser.parse_args()

    if not args.base_url:
        log.error("You need to specify a base url")
        parser.print_help()
        quit()

    if not args.bbox:
        log.error("You need to provide bbox for the area where you want the tiles")
        parser.print_help()
        quit()

    if not (args.output_folder or args.use_s3):
        log.error("You need to pass the output folder where you want to download tiles if you don't want to use s3")
        parser.print_help()
        quit()

    tile_clipper = TileClipper(args.base_url,
                               ast.literal_eval(args.bbox),
                               args.output_folder,
                               int(args.max_workers),
                               ast.literal_eval(args.use_s3),
                               args.aws_key,
                               args.aws_secret,
                               args.bucket,
                               args.layer)

    zoom_levels = args.zoom_level.split("-")
    tile_clipper.download_tiles(int(zoom_levels[0]), int(zoom_levels[1]))


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone. """
    main()
