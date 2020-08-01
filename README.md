# WiscSIMS Tool 3

A QGIS3 plugin for external/internal WiscSIMS users.

## Table of Contents

<!-- TOC -->

- [WiscSIMS Tool 3](#wiscsims-tool-3)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
    - [QGIS3](#qgis3)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Import Data](#import-data)
    - [Preset](#preset)
      - [Comments](#comments)
      - [Layer](#layer)
      - [Scale](#scale)
      - [Preset Mode](#preset-mode)
      - [Undo](#undo)

<!-- /TOC -->

## Features

WiscSIMS Tool has two features.

1. Importing Excel spreadsheets into QGIS maps.
2. Pre-selecting (preset) SIMS spots on QGIS maps.

## Requirements

### [QGIS3](https://www.qgis.org/)

  - [mac](https://qgis.org/downloads/macos/qgis-macos-ltr.dmg)
  - [windows](https://qgis.org/downloads/QGIS-OSGeo4W-3.10.8-1-Setup-x86_64.exe) (64 bit)
  - [windows](https://qgis.org/downloads/QGIS-OSGeo4W-3.10.8-1-Setup-x86.exe) (32 bit)

## Installation

1. Download `WiscSIMS Tool 3`  (**wiscsims_tool3.zip**) from [WiscSIMS GitHub repository](https://github.com/wiscsims/wiscsims_tool/releases/latest).

2. Open QGIS.

3. From the QGIS menu, select `Plugins` > `Manege and Install Plugins`

4. Select `Intall from ZIP` and hit `...` button to select downloaded `wiscsims_tool3.zip` file.

5. Hit `Install Plugin` to install `WiscSIMS Tool 3`.

6. Select `Installed Plugins` to make sure `WiscSIMS Tool 3` was correctlly installed and check the checkbox if it is unchecked.

## Usage

Activate **`WiscSIMS Tool 3`** from toolbar or menu `plugins` > `WiscSIMS` > `WiscSIMS Tool 3`.

### Import Data

_To be updated_

### Preset

You can select spots for SIMS analysis with three selecting modes: Point, Line and Grid. All or part of selected spots can be exported to Excel file (WiscSIMS session file) for manual/automated analysis.

#### Comments

You can set comment as you want. Comments are saved with preset point into selected layer. `{}` in the comment will be replaced by incremented numbers. Incremented numbers can be formatted using Python's [Format Specification Mini-Language](https://docs.python.org/2.7/library/string.html#format-specification-mini-language). For example, {:04} (four characters padded with zeros) will be formatted as '0001'.

#### Layer

Layers for preset must be vector layer and have a column/field named `Comment` (first letter should be capital). You can use pre-existing layers or create a new layer for preset spots. Hit refresh button when you added layer for preset manually to update layer list.

#### Scale

You can define the scale of image as a `Pixel Size`. In WiscSIMS Tool 3, pixel size has unit of **`µm/map_unit`**. If you have `aligment file (.json)` used in your WiscSIMS session and loaded in `Import` panel, `Pixel Size` will be automatically updated.
If you don't know the pixel size of the image, you can use **1 µm** for now. If the spot size displayed is too large or too small, adjust the pixel size appropriately. This scale will be used to preset spots in WiscSIMS Tool.

#### Preset Mode

There are three types of preset mode, Point, Line and Grid in WiscSIMS Tool. You can change those three modes with tabs in Preset Mode section in Preset panel.

- **Point Mode**

  In Point Mode, SIMS spots are added by clicking on your sample images on a QGIS map. If you want to change the comment for each spot, the "pop up comment box" option is helpful. A small window will appear right after you click on it and you can edit your comment.

- **Line**

  In Line Mode, you can add spots along the line defined by two spots. At first, you can select a start-point of line by left click, then select a end-point by right click. You will see previews of red spots and comments in gray square ballon. Note that red circles only show positions of the spots to be added, circle size is not to scale. Secondly, you can modify step size or number of spots as you want. Preview will be updated automatically with your modification. Finally, hit `Add Points` button at the bottom of `Preset Mode` section to addf points to the selected layer.

- **Grid**

  In Grid Mode, you can add spots as a grid (m x n). Left click defines the first spot of the grid. Preview will show up as well as `Line Mode`. You can modify step sizes and number of spots for vertical and horizontal. You can also choose analysis order in the grid from two options (`Vertical, then Horizontal` or `Horizontal, then Vertical`). Thin red line in the preview indicates chosen analysis order. After hit `Add Points`, poins are stored in the selected layer.

#### Undo

Undo for last added point(s) is avaiable when `undo` button is active. There is no mulitiple `undo`, only one `undo` is available.
