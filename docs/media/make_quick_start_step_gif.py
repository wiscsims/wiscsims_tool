"""Convert the short first-point recording to a GIF; retain the MP4."""

import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / "img/readme"
FFMPEG = os.environ["WISCSIMS_FFMPEG"]
VIDEO = ASSETS / "quick-start-first-point.mp4"


def run(*args):
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


with tempfile.TemporaryDirectory(prefix="wiscsims-first-point-palette-") as temporary:
    palette = pathlib.Path(temporary) / "palette.png"
    # Trim the edge where the next pointer preview leaves the recorded area.
    resize = "crop=iw-16:ih-16:0:0,fps=20,scale=540:-1:flags=lanczos"
    run("-i", VIDEO, "-vf", resize + ",palettegen=stats_mode=full:max_colors=256",
        "-frames:v", "1", "-update", "1", palette)
    run("-i", VIDEO, "-i", palette, "-filter_complex",
        f"[0:v]{resize}[v];[v][1:v]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
        "-loop", "0", ASSETS / "quick-start-05-first-point.gif")
print("Saved the first-point GIF and retained its source MP4.")
