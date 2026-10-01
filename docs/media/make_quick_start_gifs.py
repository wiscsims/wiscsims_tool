"""Convert the retained screen recording to GIFs; keep both MP4 videos."""
import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
FFMPEG = os.environ['WISCSIMS_FFMPEG']
ASSETS = ROOT / 'img/readme'
metadata = json.loads((ROOT / 'docs/media/quick-start-recording.json').read_text())
chapters = metadata['chapters']
start = next(c['time_seconds'] for c in chapters if c['text'].startswith('3 / 6'))
end = next(c['time_seconds'] for c in chapters if c['text'].startswith('4 / 6'))
master = ASSETS / 'quick-start-complete.mp4'
pixel = ASSETS / 'pixel-size-measurement.mp4'


def run(*args):
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True)


def make_gif(video, output, palette):
    # Two passes avoid buffering a whole recording. Dithering preserves soft
    # shadow gradients and antialiased text within GIF's 256-color limit.
    run('-i', video, '-vf', 'fps=25,palettegen=stats_mode=diff:max_colors=256',
        '-frames:v', '1', '-update', '1', palette)
    run('-i', video, '-i', palette, '-filter_complex',
        '[0:v]fps=25[v];[v][1:v]paletteuse=dither=sierra2_4a:diff_mode=rectangle',
        '-loop', '0', output)


run('-ss', start, '-i', master, '-t', round(end - start, 3),
    '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', pixel)
with tempfile.TemporaryDirectory(prefix='wiscsims-gif-palette-') as tmp:
    make_gif(master, ASSETS / 'quick-start-complete.gif', pathlib.Path(tmp) / 'complete.png')
    make_gif(pixel, ASSETS / 'pixel-size-measurement.gif', pathlib.Path(tmp) / 'pixel.png')
print('Retained MP4 recordings and updated both GIFs.')
