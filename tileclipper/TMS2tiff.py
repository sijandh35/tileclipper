import urllib.request
import os
import glob
import shutil
from conversion import bbox_to_xyz, tile_edges
import argparse

class tms_to_tiff:

    def __init__(self, temp_dir=os.path.join(os.getcwd(), "temp")):
        self.temp_dir = temp_dir

    def fetch_tile(self, x, y, z, tile_source):
        url = (
            tile_source.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(z))
        )

        if not tile_source.startswith("http"):
            return url.replace("file:///", "")

        path = f"{self.temp_dir}/{x}_{y}_{z}.png"
        req = urllib.request.Request(url,data=None)
        g = urllib.request.urlopen(req)
        with open(path, "b+w") as f:
            f.write(g.read())
        return path

    def merge_tiles(self, input_pattern, output_path):
        from osgeo import gdal
        vrt_path = self.temp_dir + "/tiles.vrt"
        gdal.BuildVRT(vrt_path, glob.glob(input_pattern))
        gdal.Translate(output_path, vrt_path)


    def georeference_raster_tile(self, x, y, z, path, tms):
        from osgeo import gdal
        bounds = tile_edges(x, y, z, tms)
        gdal.Translate(
            os.path.join(self.temp_dir, f"{self.temp_dir}/{x}_{y}_{z}.tif"),
            path,
            outputSRS="EPSG:4326",
            outputBounds=bounds,
        )


    def convert(self, tile_source, output_dir, bounding_box, zoom):
        lon_min, lat_min, lon_max, lat_max = bounding_box
        parts = tile_source.split("/")
        tms = parts[-1].split(".")[0].strip("{}")

        if tms.startswith("-"):
            tile_source = tile_source.replace("-", "")
            tms = True

        else:
            tms = False

        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        x_min, x_max, y_min, y_max = bbox_to_xyz(
            lon_min, lon_max, lat_min, lat_max, zoom, tms
        )

        print(
            f"Fetching & georeferencing {(x_max - x_min + 1) * (y_max - y_min + 1)} tiles"
        )

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                try:
                    png_path = self.fetch_tile(x, y, zoom, tile_source)
                    print(f"{x},{y} fetched")
                    self.georeference_raster_tile(x, y, zoom, png_path, tms)
                except OSError:
                    print(f"Error, failed to get {x},{y}")
                    pass

        print("Resolving and georeferencing of raster tiles complete")

        print("Merging tiles")
        self.merge_tiles(self.temp_dir + "/*.tif", output_dir + "/merged.tif")
        print("Merge complete")

        shutil.rmtree(self.temp_dir)

def main():
    parser = argparse.ArgumentParser("TMS2tiff", "python TMS2tiff https://tileserver-url.com/{z}/{x}/{y}.png 21.49147 65.31016 21.5 65.31688 -o output -z 20")
    parser.add_argument("tile_source", type=str, help="Local directory pattern or URL pattern to a slippy maps tile source. Ability to use {-y} in the URL to specify a TMS service", )
    parser.add_argument("lng_min", type=float, help="Min longitude of bounding box")
    parser.add_argument("lat_min", type=float, help="Min latitude of bounding box")
    parser.add_argument("lng_max", type=float, help="Max longitude of bounding box")
    parser.add_argument("lat_max", type=float, help="Max latitude of bounding box")
    parser.add_argument("-z", "--zoom", type=int, help="Tilesource zoom level", default=14)
    parser.add_argument("-o", "--output", type=str, help="Output directory", required=True)

    args = parser.parse_args()

    tile_source = args.tile_source if args.tile_source.startswith("http") else "file:///" + args.tile_source

    converter = tms_to_tiff()
    converter.convert(tile_source, args.output, [args.lng_min, args.lat_min, args.lng_max, args.lat_max], args.zoom)

if __name__ == "__main__":
    main()
