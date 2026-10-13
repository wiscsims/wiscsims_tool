# WiscSIMS Tool Quick Start

Use WiscSIMS Tool to prepare a QGIS project containing your sample images and planned SIMS spots. For each sample mount, include at least one reflected light image.

This guide shows the updated interface with **Import**, **Preset**, and **Pixel Size** tabs. Screenshots and animations show the current development UI with QGIS 3.44.13. The version distributed through the QGIS Plugin Repository may show older controls.

## Watch the complete Quick Start

<a href="../../img/readme/quick-start-complete.gif"><img src="../../img/readme/quick-start-complete.gif" width="1000" alt="Complete Quick Start: prepare and save a QGIS project, add the sample image, create a preset layer, calibrate pixel size, configure comments, place Point, Line, and Grid spots, correct spots, and save the session"></a>

*This approximately two-minute animation follows all six sections below: project setup, layer creation, Pixel Size measurement, spot settings, Point / Line / Grid placement and corrections, and saving and reopening the session. The blue circle highlights the pointer and click locations. Click the GIF to view it at full resolution.*

[Watch the full-color MP4 recording](../../img/readme/quick-start-complete.mp4). The original MP4 recording is retained alongside the GIF.

## 1. Prepare your SIMS folder

1. Create a folder for the SIMS session and copy your reflected light images into it. We will call it the **SIMS folder**.
2. Open QGIS, choose **Project > New**, and save the project in the SIMS folder.
3. Drag a sample image from the SIMS folder onto the QGIS map canvas.
4. Open WiscSIMS Tool using its toolbar button or **Plugins > WiscSIMS > WiscSIMS Tool**. Keep this map tool active while selecting positions.

The dock can be widened. Scroll within a tab if some controls are below the visible area. To bring measured data back after exporting spots with MonkeyNavigator2 GLP, see [Import measured data with GLP](#import-measured-data-with-glp).

## 2. Create a layer for your spots

1. Select **Preset**.
2. Under **Destination layer**, click **New layer…** and save the ESRI Shapefile in the SIMS folder.
3. Confirm that your new layer is selected in the dropdown.

You can also select an existing point layer with a `Comment` field and a single symbol renderer. The list updates when layers are added or removed.

Keep the shapefile's companion files together: `.shp`, `.shx`, `.dbf`, `.prj`, and `.cpg`. Include all of them with the project and images when sharing the SIMS folder.

<a href="../../img/readme/preset-point-current.png"><img src="../../img/readme/preset-point-current.png" width="400" alt="Updated Preset Point interface showing destination layer, spot size, pixel size, comment numbering, and placement controls"></a>

## 3. Measure pixel size from a scale bar

Calibrate the image before choosing spots so their displayed diameter corresponds to the size in µm. If you already know the image's pixel size in µm per map unit, enter it directly under **Preset > Spot size and scale**. Loading a supported Stage Navigator alignment file in **Import** also updates this value.

For an image with a scale bar, use the dedicated **Pixel Size** tab. The example below uses a microscopy image whose scale bar is labeled **1000 µm**.

The complete Quick Start animation above includes this measurement. To review just this step, see the [Pixel Size guide and short demonstration](Estimate-Pixel-Size-of-the-image.md#watch-the-measurement).

1. Select **Pixel Size**.
2. Under **Measure on the map**, zoom in until you can see both small black vertical ticks at the ends of the scale bar. Left click the left tick, then the right tick. The plugin fills in **Start**, **End**, and **Measured distance**.
3. Under **Enter known length**, enter **1000** in **Real length of the scale bar**, matching the **1000 µm** label printed on this image.
4. Check the calculated pixel size under **Apply the result**, then click **Apply pixel size to Preset**. The plugin switches back to Preset and fills in **Pixel size**.

The calculation is **known length in µm ÷ measured distance in map units**. In the recording, approximately 1148.3 map units represent 1000 µm, giving approximately **0.87 µm per map unit**. The orange measurement line connects the two clicked end ticks and stays there after the second click. Use the measured distance reported for your own image. A map unit represents a pixel only when your map coordinates use image pixels.

Click the map again to start a new measurement.

## 4. Set spot size and comments

Back in **Preset**:

1. Set **Spot diameter** to the planned SIMS spot diameter in µm.
2. Confirm the calibrated **Pixel size**, shown in `µm / unit`.
3. Enter a **Spot comment**, such as `spot-{}`.
4. Enable **Auto-number spots** and choose the **Next number**. For example, `spot-{}` creates `spot-1`, `spot-2`, and so on. Use `spot-{:04}` for four-digit numbering.

The default spot diameter is 10 µm, which is the usual setting. The recording changes it to 12 µm only to demonstrate the control. Use the diameter planned for your analysis.

**Reset** returns the next number to 1. **Restart on comment change** restarts numbering when you edit the template.

Spot diameter in map units is `spot diameter in µm / pixel size`. Changing either size setting also changes the selected layer's symbol units to **Map Units**.

## 5. Place and adjust spots

### Point

Select **Point**, then left click the sample image to add a spot.

- **Preview spot at pointer** shows the spot outline before placement.
- **Preview comment at pointer** shows the next comment.
- **Confirm comment on add** opens a comment editor before adding each spot.

Choose suitable sample areas. Avoid edges, cracks, and dark inclusions or structures that could affect data quality.

### Line

1. Select **Line**.
2. Choose **Spot count** for evenly spaced spots including both endpoints, or **Fixed step** for an exact spacing in µm.
3. Left click the start, move the pointer to preview the line, then left or right click its end.
4. Check the preview and the number of spots ready to add. Click **Add line spots** to save them.

Fixed step takes priority over including the endpoint. For example, a 130 µm line with a 20 µm step creates seven spots at 0–120 µm from the start and leaves the last 10 µm empty.

<a href="../../img/readme/preset-line-current.png"><img src="../../img/readme/preset-line-current.png" width="900" alt="Line preview with a 20 micrometer fixed step over a 130 micrometer line, producing seven spots"></a>

### Grid

1. Select **Grid** and set the horizontal and vertical step sizes in µm, **Columns**, **Rows**, and **Analysis order**.
2. Left click the first spot's position. Review the preview and adjust the settings, or click another position to move the grid.
3. Click **Add grid spots** to save it.

Negative step sizes reverse direction. **Horizontal, then Vertical** numbers across rows; **Vertical, then Horizontal** numbers down columns. The preview follows the current map rotation.

<a href="../../img/readme/preset-grid-current.png"><img src="../../img/readme/preset-grid-current.png" width="900" alt="Grid preview with four columns and three rows, numbered down each column"></a>

Line and Grid each allow up to 5,000 spots per placement. A preview is saved when you click its add button; the button stays disabled until the preview is valid.

### Correct a spot

| Action | Control |
| --- | --- |
| Move an existing spot | Hold **Shift** and drag it |
| Edit its comment | Hold **Option / Alt** and click the spot |
| Delete it | Hold **Option / Alt + Shift** and click the spot, then confirm |
| Undo an addition, move, comment edit, or deletion | Click **Undo last edit** |

Option / Alt + click on empty space does nothing. The comment editor also offers deletion.

## 6. Save the session

Save the QGIS project in your SIMS folder and keep the project, sample images, and all shapefile files together. Reopen the project to check that its images and spot layers load correctly before sharing the folder.

For Excel session-data import and other details, see the plugin [README](../../README.md#usage). Exporting preset spots to a WiscSIMS Excel session workbook is not currently implemented in this development version.

## Import measured data with GLP

This optional step is separate from the six-step preparation workflow in the animation.

1. In **Import**, enable **Use alignment file** and open the MonkeyNavigator2 alignment `.json` used when exporting the spots. Keep the same reference coordinates and enabled references.
2. Set **Import conversion** to **GLP (MonkeyNavigator2)**. GLP needs at least four usable references. The default **Current (reference pairs)** remains available for exports made with the previous conversion.
3. Browse to the Excel session workbook and select the data range or comment filter.
4. Create a destination layer with **New layer…**, then click **Import selected data**. The progress dialog shows reading, checking coordinates/attributes, and writing points.

GLP verifies the inverse against MonkeyNavigator2's forward calculation. If the inverse fails or multiple matching positions are found, a review dialog appears before any points are added. Open **Show Details** for all affected files. **Cancel** leaves the layer unchanged; **Import … verified points** skips the affected files and imports only verified positions. The completion message reports how many were skipped. Use the same calibration and preserve stage-coordinate precision; rounded or measured coordinates need not land exactly on the originally planned point.

To include the affected files, choose **Use reference pairs for affected points**. Only the failed GLP points use the usual **Current (reference pairs)** conversion; the other points retain their verified GLP positions. The completion message reports the pair-converted count. Pair positions use a different model and are not verified GLP inverses. If pair conversion fails, the whole import stops before writing any points.

At boundaries where the nearest reference set changes, a stage coordinate can have no exact inverse. The error reports a forward residual when available; this mode does not automatically substitute an approximate location.

<a href="../../img/readme/import-current.png"><img src="../../img/readme/import-current.png" width="400" alt="Import tab showing the GLP conversion selector and alignment, workbook, and destination layer controls"></a>
