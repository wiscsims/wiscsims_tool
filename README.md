# WiscSIMS Tool

A QGIS 3 plugin for external and internal WiscSIMS users. It helps you import session data, pre-select SIMS spots on a map, and measure pixel size from a known scale bar.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
  - [QGIS 3](#qgis-3)
- [Installation](#installation)
  - [Install from QGIS Plugin Repository](#install-from-qgis-plugin-repository)
  - [Install from ZIP file](#install-from-zip-file)
- [Usage](#usage)
  - [Import Data](#import-data)
    - [Alignment file](#alignment-file)
    - [Excel file](#excel-file)
    - [Data range](#data-range)
  - [Preset (pre-select SIMS spots on QGIS maps)](#preset-pre-select-sims-spots-on-qgis-maps)
    - [Comments](#comments)
    - [Layer](#layer)
    - [Scale](#scale)
    - [Preset Mode](#preset-mode)
    - [Preview](#preview)
    - [Undo](#undo)
    - [Modify spot locations](#modify-spot-locations)
    - [Modify comment](#modify-comment)
  - [Pixel Size](#pixel-size)
- [Current limitations](#current-limitations)

## Features

WiscSIMS Tool has three main functions:

1. Import WiscSIMS session data from Excel workbooks into a QGIS point layer.
2. Pre-select SIMS spots on QGIS maps in the Preset tab.
3. Measure pixel size from a known length on the map and use it for preset spots.

## Requirements

### [QGIS 3](https://www.qgis.org/)

The plugin metadata declares QGIS 3.4 as the minimum version. The current automated tests run with QGIS 3.44.13; older versions are not covered by those tests. Download QGIS from the [official QGIS site](https://qgis.org/download/).

For Excel import, QGIS's Python environment needs `openpyxl` for `.xlsx` files or `xlrd` for `.xls` files.

## Installation

There are two ways to install WiscSIMS Tool. The screenshots below show an older QGIS interface; button placement may differ in your version.

### Install from QGIS Plugin Repository

1. Open QGIS and select **Plugins > Manage and Install Plugins**.

   <a href="img/readme/plugin_install_menu.png" target="_blank"><img src="img/readme/plugin_install_menu.png" width="500" alt="QGIS Plugins menu"></a>

2. Search for **WiscSIMS Tool** in the [QGIS Plugin Repository](https://plugins.qgis.org/plugins/wiscsims_tool/) and click **Install Plugin**.

   <a href="img/readme/search_and_install_WiscSIMSTool.png" target="_blank"><img src="img/readme/search_and_install_WiscSIMSTool.png" width="600" alt="Install WiscSIMS Tool from the plugin list"></a>

3. Check **Installed Plugins** to confirm that it is enabled. You should also see its icon in the QGIS toolbar.

The published repository package and this development checkout may be different versions. This checkout's `metadata.txt` currently names the plugin **WiscSIMS Tool2**; its QGIS menu action is **WiscSIMS Tool**.

### Install from ZIP file

Manual installation is also available.

1. Download a packaged plugin ZIP from the [WiscSIMS Tool releases](https://github.com/wiscsims/wiscsims_tool/releases), or package the version of this checkout that you want to use.
2. In QGIS, select **Plugins > Manage and Install Plugins**.
3. Select **Install from ZIP**, choose the ZIP file, and click **Install Plugin**.

   <a href="img/readme/plugin_install_zip.png" target="_blank"><img src="img/readme/plugin_install_zip.png" width="600" alt="Install a QGIS plugin from a ZIP file"></a>

4. Check **Installed Plugins** to confirm that it is enabled.

## Usage

Open the dock from its toolbar button or **Plugins > WiscSIMS > WiscSIMS Tool**. The dock has **Import**, **Preset**, and **Pixel Size** tabs. Keep the WiscSIMS Tool map tool active when selecting locations on the map.

### Import Data

After a WiscSIMS session, use the **Import** tab to add data from a session workbook to a QGIS point layer. You can convert stage coordinates with an alignment file or import coordinates directly.

#### Alignment file

If you have a Stage Navigator alignment `.json` file, load it under **Import Alignment File**. The plugin uses the alignment to transform stage coordinates to map coordinates. You can inspect the reference points in the dock, and loading the alignment updates the Preset pixel size.

If the workbook's `X` and `Y` values are already map coordinates, uncheck **Import Alignment File** to import them directly.

#### Excel file

1. Choose a `.xlsx` or `.xls` file under **Select Excel Workbook**. The workbook controls become available after a usable alignment is loaded or alignment is turned off.
2. The workbook needs a sheet named `Sum_table` or `Data`. Its first row supplies field names; data rows need a first-column filename such as `20240929@1.asc` and `X` and `Y` columns. **Comment Match** also needs a `Comment` column.
3. Select a compatible, visible point layer under **Select Layer to Import SIMS Data**, or click **Create…** to make a new ESRI Shapefile with fields from the workbook. **Spot Size for the Session** sets the symbol size of a new layer.
4. Click **Import Excel Data**. Valid rows are appended to the chosen layer; rows without usable numeric coordinates are skipped.

#### Data range

Use **Data Range** to import rows between selected `.asc` filenames. Alternatively, use **Comment Match** to filter the `Comment` column with a case-insensitive regular expression.

### Preset (pre-select SIMS spots on QGIS maps)

Use the **Preset** tab to place spots on a QGIS point layer before SIMS analysis. Choose **Point**, **Line**, or **Grid** under Preset Mode.

#### Comments

Comments are saved with preset points in the selected layer. With **Auto Number Increments** enabled, a Python format placeholder in the comment is replaced by the current number. For example, `spot-{:04}` produces `spot-0001` when the number is 1. See Python's [format specification](https://docs.python.org/3/library/string.html#format-specification-mini-language).

Use **Start with #** and **Reset** to control the sequence. **Reset when comment changes** starts the sequence again when you edit the comment template. **Auto pop-up comment box** opens an editor before each spot is added.

#### Layer

Preset layers must be point vector layers with a field named `Comment` and a single symbol renderer. Select an existing layer, or click **Layer > Create…** to create a new ESRI Shapefile. A new preset layer also has fields for spot size and pixel size. Use the refresh button if a layer you added manually does not appear in the list.

#### Scale

Set **Spot Size** in µm and **Pixel Size** in µm per map unit. The diameter saved for the spot symbol in map units is `spot size / pixel size`. Loading an alignment file in **Import** updates the Preset pixel size. You can also enter it manually or calculate it in the **Pixel Size** tab.

#### Preset Mode

- **Point:** Left click the sample image on the map to add a spot. With **Auto pop-up comment box** enabled, edit or confirm its comment before adding it.
- **Line:** Left click to set the start point. Move the pointer to preview the line, then left or right click to set its end point. Choose **N of Spots** to include both endpoints at even intervals, or **Step Size** in µm to place spots at that fixed interval from the start. In Step Size mode, the end point gets a spot only when it falls on the interval; a line shorter than one interval has just the start spot. Click **Add Points** to save the previewed spots.
- **Grid:** Left click to place the first spot. Set the horizontal and vertical step sizes in µm (negative values reverse direction), the number of spots in each direction, and the **Order of Analysis**. The preview follows the current map rotation. Click **Add Points** to save the previewed spots. Click another location to start a new grid before adding it.

Line and Grid each allow up to 5,000 spots per placement. The **Add Points** button stays disabled until a valid preview is ready.

#### Preview

In Point mode, **Preview** shows a spot circle at the pointer. **Preview (Text)** shows the next comment beside the pointer and works independently of the circle. The circle resizes after zooming, with a minimum on-screen diameter of 16 pixels so it stays visible when zoomed far out. This display minimum does not alter the spot size saved to the layer. Line and Grid show the candidate spots on the map before you click **Add Points**.

#### Undo

Click **Undo** to reverse a recent spot addition, movement, comment edit, or deletion. The button is enabled when there is an action to undo.

#### Modify spot locations

Hold **Shift** and drag an existing spot to move it. To move multiple features, use QGIS's built-in feature editing tools.

#### Modify comment

Hold **Alt** (or **Option** on macOS) and click an existing spot to open its comment editor. Clicking empty space does nothing. The dialog also offers deletion. To delete a spot directly, hold **Alt + Shift** (or **Option + Shift** on macOS) and click it; confirm the deletion when prompted.

### Pixel Size

Use the **Pixel Size** tab when you know the real length represented by a scale bar on the map:

1. Click the scale bar's start and end points on the map.
2. Enter the known **Scale Bar Length** in µm.
3. Check the calculated **Pixel Size**, then click **Set Pixel Size** to copy it to the **Preset** tab.

The calculation is `known length in µm / measured distance in map units`. The distance field is labeled `px` in the interface; that label is literal only when the map coordinates represent image pixels. Click the map again to start another measurement.

## Current limitations

- Exporting preset spots to a WiscSIMS Excel session workbook is not currently implemented in this checkout.
