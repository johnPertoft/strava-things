import argparse
from datetime import datetime
import glob
import itertools
import logging
import math
import os
import tempfile
import time
from typing import List, Tuple

from bs4 import BeautifulSoup
import folium
import moviepy.editor as mpy
from selenium import webdriver


logger = logging.getLogger(__file__)
logging.basicConfig(format="[%(levelname)s] [%(asctime)s] %(message)s")
logger.setLevel(logging.INFO)

Position = Tuple[float, float]

_CITY_BOUNDS = {
    "stockholm": [[59.303377, 18.030198], [59.361293, 18.154801]]
}


def _load_gpx_file(gpx_file: str) -> Tuple[List[Position], datetime]:
    logger.info(f"Loading {gpx_file}")
    with open(gpx_file) as f:
        content = BeautifulSoup(f.read(), "lxml")
        start_time = content.find("metadata").find("time").text
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        positions = content.find("trk").find("trkseg").find_all("trkpt")
        positions = [(float(p.attrs["lat"]), float(p.attrs["lon"])) for p in positions]

    return positions, start_time


def _distance(p1: Position, p2: Position) -> float:
    # TODO: Handle points on either side of meridian (?)
    # TODO: Haversine distance?
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _append_route(
    m: folium.Map,
    positions: List[Position],
    filter_irregular_paths: bool,
    distance_threshold: float,
    min_positions_per_segment: int
) -> None:
    def add_line(positions):
        line = folium.PolyLine(positions, color="orange")
        line.add_to(m)

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


class _VideoWriter:
    def __init__(self, map_bounds: Tuple[Position, Position]):
        options = webdriver.FirefoxOptions()
        options.headless = True
        self._browser = webdriver.Firefox(options=options)
        self._output_dir = tempfile.mkdtemp()
        self._map_bounds = map_bounds
        self._frame_index = itertools.count()

    def add_frame(self, m: folium.Map) -> None:
        frame_index = next(self._frame_index)

        logger.info(f"Adding video frame {frame_index}")

        # TODO: Can we output a png directly from here instead?
        html_output_file = f"{frame_index}.html"
        html_output_file = os.path.join(self._output_dir, html_output_file)
        m.fit_bounds(self._map_bounds)
        m.save(html_output_file)
        
        png_output_file = f"{frame_index}.png"
        png_output_file = os.path.join(self._output_dir, png_output_file)
        self._browser.get("file://" + html_output_file)
        time.sleep(1)
        self._browser.get_screenshot_as_file(png_output_file)

    def write_video(self) -> None:
        paths = glob.glob(os.path.join(self._output_dir, "*.png"))
        paths = sorted(paths, key=lambda p: int(os.path.basename(p)[:-4]))

        clips = [mpy.ImageClip(p).set_duration(1) for p in paths]
        video = mpy.concatenate_videoclips(clips, method="compose")
        video.write_videofile("combined-routes.mp4", fps=2)


def _append_routes(
    m: folium.Map,
    gpx_files: List[str],
    filter_irregular_paths: bool = True,
    distance_threshold: float = 0.001,
    min_positions_per_segment: int = 5,
    output_video: bool = False,
    map_bounds: Tuple[Position, Position] = None
) -> None:
    if output_video:
        assert map_bounds is not None, "Need explicit map bounds for video output."
        video_writer = _VideoWriter(map_bounds)

    activities = [_load_gpx_file(gpx_file) for gpx_file in gpx_files]
    activities = sorted(activities, key=lambda a: a[1])

    for positions, _start_time in activities:
        _append_route(
            m,
            positions,
            filter_irregular_paths,
            distance_threshold,
            min_positions_per_segment)
        
        if output_video:
            video_writer.add_frame(m)

    if output_video:
        video_writer.write_video()


def main(args):
    m = folium.Map(
        tiles="CartoDB dark_matter" if not args.light else "Stamen toner",
        prefer_canvas=True,
        max_zoom=20)

    if args.bounds is None:
        map_bounds = None
    else:
        # TODO: Support both passing a city as well as custom bounds.
        map_bounds = _CITY_BOUNDS[args.bounds]

    gpx_files = glob.glob(os.path.join(args.gpx_dir, "*.gpx"))
    if not gpx_files:
        exit("No .gpx files found. Exiting")

    _append_routes(
        m,
        gpx_files,
        output_video=args.video,
        map_bounds=map_bounds)

    m.fit_bounds(map_bounds or m.get_bounds())
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
    
    arg_parser.add_argument(
        "--video",
        action="store_true",
        help="Whether to output a video.")
    
    arg_parser.add_argument(
        "--bounds",
        help="Custom coordinate bounds.")

    main(arg_parser.parse_args())
