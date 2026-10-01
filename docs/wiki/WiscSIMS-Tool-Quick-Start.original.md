## Preset SIMS spots

For the SIMS session at the WiscSIMS, we need QGIS project files which includes sample image and locations of SIMS spot. 
For each plug/sample mount, at least one reflected light image is required.

> __Create a new folder for SIMS session, and copy reflected light images to the folder. From now on, we will call this folder “_SIMS folder_”.__

### Steps 🚶‍♀️

- Open QGIS

- Create a blank project (Project > New) and save it to the SIMS folder.

  [[/images/image001.png]]

- Drag & Drop the reflected light image from the SIMS folder to the canvas (main white blank space in QGIS application).

- Activate WiscSIMS Tool by clicking plugin button in the Toolbar. 

  [[/images/image002.png]]

- Select “Preset” tab in the WiscSIMS Tool widget.

  [[/images/image003.png]]

- Create a new vector layer for preset points by clicking “New” button in the “Layer” section and save it to the SIMS folder. This process creates shape files with different extension (.cpg, .bdf, .prj, .shp, .shx). We will need all of them.

  [[/images/image004.png]]

- Type in pixel size of placed image. If you do not know the pixel size of the image, please leave it as is.

  [[/images/image005.png]]

- Select “Point” in the “Preset Mode” section.

  [[/images/image006.png]]

- Modify comment as you like. Comments are like IDs for SIMS spots.  

  [[/images/image007.png]]

- Click on the image to select SIMS spots.

  [[/images/image008.png]]

Please avoid edges, cracks and structures (black dots). They may affect quality of data.


You can find more details of the plugin in the [readme](https://github.com/wiscsims/wiscsims_tool#usage) of plugin’s GitHub page.



