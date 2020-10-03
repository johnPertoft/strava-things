import argparse
import glob
import math
import os
import re
from typing import List, Tuple

import folium


def _distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _load_positions(gpx_file: str) -> List[Tuple[float, float]]:
    number_pattern = re.compile("[-]?[0-9]*[.]?[0-9]+")
    positions = []
    with open(gpx_file) as f:
        for line in f:
            if line.strip().startswith("<trkpt"):
                lat, lng = re.findall(number_pattern, line)
                positions.append((float(lat), float(lng)))
    return positions


def append_route(
    m: folium.Map,
    gpx_file: str,
    filter_irregular_paths: bool = True,
    distance_threshold: float = 0.001,
    min_positions_per_segment: int = 5
) -> None:
    print(f"Parsing {gpx_file}")
    
    def add_line(positions):
        line = folium.PolyLine(positions, color="orange", tooltip=f"From file {gpx_file}")
        line.add_to(m)

    positions = _load_positions(gpx_file)

    if not filter_irregular_paths:
        add_line(positions)
    else:
        # Find the "more contiguous" segments. I.e. if an activity has two neighboring
        # positions that are very far apart we split these into two different segments.
        distances = [_distance(p1, p2) for p1, p2 in zip(positions, positions[1:])]
        segment_end_indices = [i for i, d in enumerate(distances) if d > distance_threshold]
        segment_start_indices = [i + 1 for i in segment_end_indices]
        segment_indices = zip([0] + segment_start_indices, segment_end_indices + [len(positions) - 1])
        for s, e in segment_indices:
            segment_positions = positions[s : e + 1]
            if len(segment_positions) >= min_positions_per_segment:
                add_line(segment_positions)


def main(args):
    m = folium.Map(
        tiles="CartoDB dark_matter" if not args.light else "Stamen toner",
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

    arg_parser.add_argument(
        "--light",
        action="store_true",
        default=False,
        help="Whether to output a map with light background.")

    main(arg_parser.parse_args())

