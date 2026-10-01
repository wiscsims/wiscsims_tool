# Quick Start recordings

## Retained videos and GIFs

- [Complete Quick Start MP4](../../img/readme/quick-start-complete.mp4): the original 30 fps QGIS recording.
- [Complete Quick Start GIF](../../img/readme/quick-start-complete.gif): converted from that MP4 at 25 fps.
- [Pixel Size MP4](../../img/readme/pixel-size-measurement.mp4): the measurement section extracted from the complete video.
- [Pixel Size GIF](../../img/readme/pixel-size-measurement.gif): converted from the extracted MP4.

The MP4 files are kept as the source recordings. GIF conversion does not delete or replace them. Full-color MP4 playback preserves gradients without GIF's 256-color limit.

## Reproduce the recording

The recorder needs QGIS with its Python bindings, Pillow, GDAL, and FFmpeg with the `libx264`, `palettegen`, and `paletteuse` filters. It uses the current plugin source. Run it in a **disposable QGIS profile**, since it creates and clears a demo project. Configure `auth/use_password_helper=false` in that profile's settings before starting QGIS to avoid a system keychain prompt during offscreen recording.

Set these environment variables before starting QGIS with `--nologo --noversioncheck --noplugins --profiles-path <temporary-profile-root> --profile quickstart --lang en --code <absolute-path-to-record_quick_start.py>`:

| Variable | Value |
| --- | --- |
| `WISCSIMS_RECORD_ROOT` | Absolute path to this plugin repository |
| `WISCSIMS_RECORD_SESSION` | A temporary `wiscsims-quick-start-.../SIMS-session` folder |
| `WISCSIMS_FFMPEG` | Absolute path to the FFmpeg executable |
| `QT_QPA_PLATFORM` | `offscreen` |

[record_quick_start.py](record_quick_start.py) continuously captures the QGIS window while the real plugin controls receive mouse and keyboard events. A 30 fps clock fills any missed capture intervals. The pointer follows interpolated paths with gradual acceleration and deceleration, including map movements and moves between controls. File dialogs show only the temporary SIMS folder in their sidebar and history, keeping account names out of the recording. The spot diameter example changes the initial 10 µm value to 12 µm.

The recorder saves an MP4 with H.264 at CRF 12, then writes [quick-start-recording.json](quick-start-recording.json) with chapter timings, measured distance, spot diameter settings, anonymized dialog count, and the post-reload spot count. It checks the clicked measurement endpoints, the five shapefile companion files, placement counts, spot corrections, and project reopening.

Then run `python3 docs/media/make_quick_start_gifs.py` with `WISCSIMS_FFMPEG` set. The converter first retains a separate MP4 of the Pixel Size section, then generates both GIFs from the MP4 files in two passes. Palette generation uses changing regions, and palette application uses Sierra dithering. Temporary palette images are removed; the videos remain in `img/readme`.

The supplied microscopy image is preserved as the source asset. For the demo project, its TIFF copy uses one map unit per source pixel. The assigned demonstration coordinates do not establish real-world image coordinates.
