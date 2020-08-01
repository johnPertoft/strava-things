import argparse
import glob
import os
import re

import folium


def append_route(m: folium.Map, gpx_file: str) -> None:
    print(f"Parsing {gpx_file}")
    number_pattern = re.compile("[-]?[0-9]*[.]?[0-9]+")
    positions = []
    with open(gpx_file) as f:
        for line in f:
            if line.strip().startswith("<trkpt"):
                lat, lng = re.findall(number_pattern, line)
                positions.append((float(lat), float(lng)))

    line = folium.PolyLine(positions, color="orange", tooltip=f"From file {gpx_file}")
    line.add_to(m)


def main(args):
    m = folium.Map(
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
        max_zoom=20)

    gpx_files = glob.glob(os.path.join(args.gpx_dir, "*.gpx"))
    if not gpx_files:
        exit("No .gpx files found. Exiting")

    for gpx_file in gpx_files:
        append_route(m, gpx_file)

    m.fit_bounds(m.get_bounds())
    m.save(args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Generate an html map with combined Strava activities.")

    arg_parser.add_argument(
        "--gpx-dir",
        required=True,
        help="Directory of .gpx files.")
    
    arg_parser.add_argument(
        "--output",
        default="combined-routes.html",
        help="The output html file.")

    main(arg_parser.parse_args())

