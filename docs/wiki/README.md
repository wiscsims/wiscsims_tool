# Quick Start source and update

- [Original Markdown](WiscSIMS-Tool-Quick-Start.original.md): the original [WiscSIMS Tool Quick Start](https://github.com/wiscsims/wiscsims_tool/wiki/WiscSIMS-Tool-Quick-Start), retrieved from the Wiki Git repository at commit `b06d68d`. This file preserves the source text and its original Wiki image links.
- [Updated Quick Start](WiscSIMS-Tool-Quick-Start.md): the original workflow updated for the current development UI, including Pixel Size measurement, Point, Line, Grid, spot corrections, and session saving.
- [Pixel Size measurement](Estimate-Pixel-Size-of-the-image.md): the detailed measurement example using the supplied microscopy image and its 1000 µm scale bar.

The updated pages use relative links to the repository's `img/readme` assets. The complete Quick Start is recorded from real QGIS 3.44.13 and plugin interactions in a disposable project at 30 frames per second. Its captions follow the guide's six numbered sections. The blue circle is a recording overlay showing the pointer position, with interpolated motion between controls and map positions. Native dialogs are composited over the QGIS window with a soft shadow so they remain visible in the recording. File dialog sidebars and history show only the temporary SIMS folder.

The original MP4 recording is retained alongside the GIF. The Pixel Size MP4 clip is extracted from that recording and also retained. Both GIFs are converted from the saved videos at 25 frames per second, using a generated palette and dithering to preserve soft shadows and smooth text edges. The Quick Start embeds the complete animation once and links to the short clip in the detailed Pixel Size page. See [recording and conversion instructions](../media/README.md) for the scripts and timing metadata.

The demonstration image is saved as a TIFF with one map unit per source pixel. Its assigned demonstration coordinates are for this recording; they do not establish real-world image coordinates. Pixel Size measurement calibrates these units from the printed 1000 µm scale bar. The recorded workflow saves and reopens the project, checking that the image and 23 preset spots remain available.

To publish these local pages to the GitHub Wiki, change repository-relative image links to the corresponding Wiki image URLs and Markdown page links to Wiki page links.
