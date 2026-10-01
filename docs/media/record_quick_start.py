"""Record the current plugin in a disposable, native QGIS session."""
import io, os, pathlib, sys, traceback, subprocess, time, json, tempfile
from PIL import Image
from osgeo import gdal
from qgis.utils import iface
from qgis.core import QgsApplication, QgsProject, QgsCoordinateReferenceSystem, QgsPointXY, QgsRectangle
from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QPointF, Qt, QTimer, QMimeData, QUrl
from qgis.PyQt.QtGui import QPainter, QColor, QDragEnterEvent, QDropEvent, QImage
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication, QLabel, QToolBar, QDockWidget, QScrollArea, QFileDialog, QLineEdit, QMessageBox, QToolTip, QDialogButtonBox
ROOT=pathlib.Path(os.environ['WISCSIMS_RECORD_ROOT']).resolve()
SESSION=pathlib.Path(os.environ['WISCSIMS_RECORD_SESSION']).resolve()
temporary_roots=[pathlib.Path('/private/tmp'),pathlib.Path(tempfile.gettempdir()).resolve()]
if not any(SESSION.is_relative_to(p) for p in temporary_roots) or not SESSION.parent.name.startswith('wiscsims-quick-start-'):
 raise ValueError('Recording session must be a dedicated wiscsims-quick-start-... temporary folder.')
FFMPEG=os.environ['WISCSIMS_FFMPEG']
VIDEO=ROOT/'img/readme/quick-start-complete.mp4'
sys.path.insert(0,str(ROOT.parent))
QApplication.setAttribute(Qt.AA_DontUseNativeDialogs,True)
frames=[]; durations=[]; chapters=[]
recorder=None; recording_dialog=None; recording_busy=False; written_frames=0
FPS=30
anonymized_file_dialogs=0


def record():
 global window, canvas, banner, pointer, plugin, dock
 try:
  SESSION.mkdir(parents=True,exist_ok=True)
  for p in SESSION.glob('preset.*'):p.unlink()
  for p in SESSION.glob('session.qgz*'):p.unlink()
  image_path=SESSION/'sample-reflected-light.tif'
  ds=gdal.Translate(str(image_path),str(ROOT/'img/readme/pixel-size-source.png'),format='GTiff',creationOptions=['COMPRESS=LZW'])
  ds.SetGeoTransform((0,1,0,0,0,-1));crs=QgsCoordinateReferenceSystem('EPSG:3857');ds.SetProjection(crs.toWkt());ds=None
  window=iface.mainWindow();window.resize(1460,1100)
  for toolbar in window.findChildren(QToolBar):
   toolbar.setVisible(toolbar.objectName() in ('mFileToolBar','mMapNavToolBar'))
  for d in window.findChildren(QDockWidget):
   if 'Browser' in d.windowTitle():d.hide()
  tree=iface.layerTreeView();tree.parentWidget().setMinimumWidth(190)
  canvas=iface.mapCanvas();canvas.setCanvasColor(QColor('white'))
  guide=QToolBar('Quick Start recording',window);guide.setMovable(False)
  banner=QLabel('',guide);banner.setStyleSheet('padding: 9px; background: #e8f0fb; color: #123456; font-size: 16px; font-weight: bold;')
  guide.addWidget(banner);window.addToolBar(Qt.TopToolBarArea,guide);window.insertToolBarBreak(guide)
  pointer=QLabel('◉',window);pointer.resize(28,28);pointer.setAttribute(Qt.WA_TransparentForMouseEvents)
  pointer.setStyleSheet('color: #1269ec; background: transparent; font-size: 26px;');pointer.show();pointer.raise_()
  window.show();settle(True);start_video()
  chapter('1 / 6   Prepare a SIMS folder with reflected light images. Project > New.')
  iface.actionNewProject().trigger();settle(True);capture(1800)
  chapter('1 / 6   Save the blank QGIS project in the SIMS folder.')
  QTimer.singleShot(200,lambda:handle_file_dialog('session.qgz'))
  iface.actionSaveProject().trigger();settle(True);capture(1500)
  assert pathlib.Path(QgsProject.instance().fileName()).name=='session.qgz'
  chapter('1 / 6   Add the reflected light image from the same folder to the map canvas.')
  mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(image_path))]);pos=QPoint(canvas.width()//2,canvas.height()//2)
  indicate(canvas.viewport(),pos);capture(1100)
  pos=canvas.viewport().mapTo(window,pos)
  enter=QDragEnterEvent(pos,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
  QApplication.sendEvent(window,enter)
  drop=QDropEvent(QPointF(pos),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
  QApplication.sendEvent(window,drop);QTest.qWait(600);settle(True)
  rasters=[l for l in QgsProject.instance().mapLayers().values() if l.name()=='sample-reflected-light']
  assert len(rasters)==1,[(l.name(),l.type()) for l in QgsProject.instance().mapLayers().values()]
  raster=rasters[0];canvas.setExtent(raster.extent());settle(True);capture(1800)
  from wiscsims_tool_class.wiscsims_tool import WiscSIMSTool
  plugin=WiscSIMSTool(iface);plugin.initGui();plugin.toolbar.show()
  chapter('1 / 6   Open WiscSIMS Tool with its toolbar button.')
  tool_button=plugin.toolbar.widgetForAction(plugin.wiscsims_tool_action)
  click(tool_button);dock=plugin.dockwidget;dock.setMinimumWidth(420);dock.setMaximumWidth(420)
  plugin.preset.show_tooltip=lambda *_args:None;plugin.pxsizetool.show_tooltip=lambda:None
  iface.messageBar().clearWidgets();settle(True);capture(1800)
  chapter('2 / 6   Preset > Destination layer > New layer…')
  select_tab(dock.Tab_Tool,1);capture(1200)
  QTimer.singleShot(200,lambda:handle_file_dialog('preset.shp'))
  click(dock.Btn_Create_Preset_Layer);layer=plugin.preset.get_preset_layer();assert layer and layer.isValid();capture(2000)
  assert all((SESSION/('preset'+ext)).exists() for ext in ['.shp','.shx','.dbf','.prj','.cpg'])
  chapter('3 / 6   Pixel Size: zoom in until both scale bar end ticks are visible.')
  select_tab(dock.Tab_Tool,2);canvas.setExtent(QgsRectangle(330,-1170,1660,-180));settle(True);capture(1700)
  chapter('3 / 6   Click the left black tick, then the right black tick of the 1000 µm bar.')
  left=map_pos(QgsPointXY(422.5,-711));right=map_pos(QgsPointXY(1571,-711))
  move_map(QPoint(left.x()-25,left.y()-25),left,4);capture(600);click(canvas.viewport(),left);capture(1000)
  move_map(left,right,9);capture(600);click(canvas.viewport(),right);capture(1600)
  measured=dock.SPN_PST_ScaleBar_Len_Px.value();assert 1140<measured<1160,measured
  rendered_line=plugin.pxsizetool.pxsize_line.asGeometry().asPolyline()
  assert rendered_line[0]==plugin.pxsizetool.pxsize_start_point
  assert rendered_line[-1]==plugin.pxsizetool.pxsize_end_point
  assert abs(rendered_line[-1].y()-rendered_line[0].y())<1
  snapshot().save('/private/tmp/quick-start-aligned-scale.png')
  chapter('3 / 6   Enter the printed real length: 1000 µm. Result: approximately 0.87 µm / unit.')
  enter_value(dock.SPN_PST_ScaleBar_Len_um,'1000');capture(2000);assert dock.SPN_PST_PixelSize.value()==0.87
  chapter('3 / 6   Apply pixel size to Preset. The Preset tab opens with the calibrated value.')
  click(dock.Btn_PST_Set);assert dock.Spn_Preset_Pixel_Size.value()==0.87;capture(2100)
  assert dock.Spn_Preset_Spot_Size.value()==10
  chapter('4 / 6   Usual spot size: 10 µm. Change to 12 µm here only to demonstrate the control.')
  enter_value(dock.Spn_Preset_Spot_Size,'12');enter_value(dock.Tbx_Comment,'spot-{:04}');capture(1800)
  chapter('4 / 6   Auto-number spots is enabled. Next number 1 produces spot-0001, spot-0002…')
  indicate(dock.Spn_Current_Number,dock.Spn_Current_Number.rect().center());capture(1900)
  chapter('5 / 6   Point: preview the spot outline and comment before clicking to add a spot.')
  select_tab(dock.Tab_Preset_Mode,0)
  if not dock.Opt_Comment_Preview.isChecked():click(dock.Opt_Comment_Preview,QPoint(10,dock.Opt_Comment_Preview.height()//2))
  canvas.setExtent(QgsRectangle(650,-620,1290,-70));settle(True)
  pts=[QgsPointXY(870,-315),QgsPointXY(1000,-355),QgsPointXY(1120,-460)]
  for pt in pts:
   end=map_pos(pt);move_map(end-QPoint(35,20),end,4);capture(500);click(canvas.viewport(),end);capture(950)
  assert layer.featureCount()==3,layer.featureCount()
  chapter('5 / 6   Optional: Confirm comment on add opens an editor before adding each spot.')
  click(dock.Opt_Comment_Popup,QPoint(10,dock.Opt_Comment_Popup.height()//2))
  QTimer.singleShot(200,handle_new_comment)
  click(canvas.viewport(),map_pos(QgsPointXY(900,-490)));capture(1300)
  click(dock.Opt_Comment_Popup,QPoint(10,dock.Opt_Comment_Popup.height()//2));assert layer.featureCount()==4
  chapter('5 / 6   Correct a spot: hold Shift and drag the existing spot to a new position.')
  before=list(layer.getFeatures())[0];original=before.geometry().asPoint();target=QgsPointXY(original.x()+35,original.y()-30)
  start=map_pos(original);end=map_pos(target);indicate(canvas.viewport(),start);QTest.keyPress(canvas,Qt.Key_Shift);capture(700)
  QTest.mousePress(canvas.viewport(),Qt.LeftButton,Qt.ShiftModifier,start);move_map(start,end,6)
  QTest.mouseRelease(canvas.viewport(),Qt.LeftButton,Qt.ShiftModifier,end);QTest.keyRelease(canvas,Qt.Key_Shift);settle(True);capture(1800)
  moved=next(layer.getFeatures());assert moved.geometry().asPoint().distance(original)>20
  chapter('5 / 6   Hold Option / Alt and click an existing spot to edit its comment.')
  QTimer.singleShot(200,handle_edit_comment)
  QTest.keyPress(canvas,Qt.Key_Alt);click(canvas.viewport(),map_pos(moved.geometry().asPoint()),mod=Qt.AltModifier);QTest.keyRelease(canvas,Qt.Key_Alt);settle(True);capture(1700)
  assert layer.featureCount()==4;assert any(f['Comment']=='spot-0001-check' for f in layer.getFeatures())
  chapter('5 / 6   Hold Option / Alt + Shift and click a spot to delete it, then confirm.')
  QTimer.singleShot(200,handle_delete)
  QTest.keyPress(canvas,Qt.Key_Alt);QTest.keyPress(canvas,Qt.Key_Shift)
  click(canvas.viewport(),map_pos(moved.geometry().asPoint()),mod=Qt.AltModifier|Qt.ShiftModifier)
  QTest.keyRelease(canvas,Qt.Key_Shift);QTest.keyRelease(canvas,Qt.Key_Alt);settle(True);capture(1600);assert layer.featureCount()==3
  chapter('5 / 6   Undo last edit restores the deleted spot. Additions, moves and comment edits are also undoable.')
  click(dock.Btn_Undo_Add_Preset_Point);settle(True);capture(1800);assert layer.featureCount()==4
  chapter('5 / 6   Line: choose Fixed step and set the exact spacing in µm.')
  select_tab(dock.Tab_Preset_Mode,1);click(dock.Opt_Line_Step_Size,QPoint(10,dock.Opt_Line_Step_Size.height()//2))
  enter_value(dock.Spn_Line_Step_Size,'20');capture(1400)
  chapter('5 / 6   Click the line start and end. Fixed step prioritizes spacing over the endpoint.')
  a=map_pos(QgsPointXY(750,-190));b=map_pos(QgsPointXY(750+130/0.87,-190))
  click(canvas.viewport(),a);capture(700);move_map(a,b,7);click(canvas.viewport(),b);capture(2000)
  assert len(plugin.preset.preset_points)==7,len(plugin.preset.preset_points)
  chapter('5 / 6   130 µm line / 20 µm step: 7 spots at 0–120 µm. Click Add line spots.')
  click(dock.Btn_Line_Add_Points);settle(True);capture(1800);assert layer.featureCount()==11
  chapter('5 / 6   Grid: set X / Y steps, Columns, Rows, and Analysis order.')
  select_tab(dock.Tab_Preset_Mode,2)
  enter_value(dock.Spn_Grid_Step_Size_X,'30');enter_value(dock.Spn_Grid_Step_Size_Y,'-30')
  enter_value(dock.Spn_Grid_N_Point_X,'4');enter_value(dock.Spn_Grid_N_Point_Y,'3')
  dock.Cmb_Grid_Move_Order.setCurrentIndex(1);indicate(dock.Cmb_Grid_Move_Order,dock.Cmb_Grid_Move_Order.rect().center());capture(1800)
  chapter('5 / 6   Click the first grid position. Review the 4 × 3 preview, then Add grid spots.')
  click(canvas.viewport(),map_pos(QgsPointXY(1040,-150)));capture(1900)
  assert len(plugin.preset.preset_points)==12;click(dock.Btn_Grid_Add_Points);settle(True);capture(1800);assert layer.featureCount()==23
  chapter('6 / 6   Save the QGIS project. Keep it with the image and every shapefile companion file.')
  # Let QGIS save the plugin settings to the project before checking reopening.
  iface.actionSaveProject().trigger();settle(True);capture(2100)
  saved_file=QgsProject.instance().fileName();assert pathlib.Path(saved_file).exists()
  plugin.unload();QgsProject.instance().setDirty(False);iface.actionNewProject().trigger();settle(True)
  assert QgsProject.instance().read(saved_file);settle(True)
  reloaded=[l for l in QgsProject.instance().mapLayers().values() if l.name()=='Preset']
  assert len(reloaded)==1 and reloaded[0].featureCount()==23
  assert all(l.isValid() for l in QgsProject.instance().mapLayers().values())
  plugin=WiscSIMSTool(iface);plugin.initGui();plugin.wiscsims_tool_action.trigger();dock=plugin.dockwidget
  dock.setMinimumWidth(420);dock.setMaximumWidth(420);plugin.preset.show_tooltip=lambda *_args:None;settle(True)
  chapter('6 / 6   Reopen session.qgz and confirm the image and all 23 planned spots load correctly.')
  capture(2400)
  chapter('6 / 6   Share the SIMS folder: project + image + .shp, .shx, .dbf, .prj and .cpg.')
  dlg=QFileDialog(window,'SIMS folder: files to keep together',str(SESSION));dlg.setOption(QFileDialog.DontUseNativeDialog);dlg.setViewMode(QFileDialog.Detail);dlg.resize(920,470)
  dlg.show();settle();capture(3500,dlg);dlg.close()
  chapter('Quick Start complete. Refer to the updated Markdown guide for controls and examples.')
  capture(2200);encode()
  print('COMPLETE_QUICK_START_OK',len(frames),sum(durations),measured,'23 spots survive project reload',flush=True)
  (ROOT/'docs/media/quick-start-recording.json').write_text(json.dumps({'video':'../../img/readme/quick-start-complete.mp4','fps':FPS,'frames':written_frames,'duration_seconds':round(written_frames/FPS,3),'measurement_map_units':measured,'spots_after_reload':23,'default_spot_diameter_um':10,'example_spot_diameter_um':12,'anonymized_file_dialogs':anonymized_file_dialogs,'chapters':chapters},indent=2)+'\n')
  os._exit(0)
 except Exception:
  traceback.print_exc();sys.stdout.flush();sys.stderr.flush()
  try:capture(1000);frames[-1].save('/private/tmp/quick-start-failure.png')
  except Exception:pass
  os._exit(1)


def settle(render=False):
 QToolTip.hideText();QApplication.processEvents();QTest.qWait(30)
 if render:canvas.refresh();canvas.waitWhileRendering();QApplication.processEvents()

def snapshot(dialog=None):
 pix=window.grab()
 dialog=dialog or recording_dialog or QApplication.activeModalWidget()
 if dialog and dialog.isVisible():
  if isinstance(dialog,QFileDialog):anonymize_file_dialog(dialog)
  painter=QPainter(pix);dp=dialog.grab();x=(pix.width()-dp.width())//2;y=(pix.height()-dp.height())//2
  # A soft compositing shadow replaces the previous solid gray rectangle.
  painter.setPen(Qt.NoPen)
  for spread in range(28,0,-1):
   painter.setBrush(QColor(0,0,0,2))
   painter.drawRoundedRect(x-spread//2,y-spread//2+7,dp.width()+spread,dp.height()+spread,8,8)
  painter.drawPixmap(x,y,dp);painter.end()
 return pix

def write_video_frame():
 global written_frames,recording_busy
 if recording_busy:return
 recording_busy=True
 try:
  QToolTip.hideText()
  pix=snapshot();image=pix.toImage().convertToFormat(QImage.Format_RGBA8888)
  assert image.width()==video_width and image.height()==video_height
  data=image.bits().asstring(image.byteCount())
  target=int((time.monotonic()-video_started)*FPS)+1
  while written_frames<target:
   encoder.stdin.write(data);written_frames+=1
 finally:recording_busy=False

def start_video():
 global encoder,recorder,video_started,video_width,video_height,video_log
 pix=window.grab();video_width=pix.width();video_height=pix.height()
 video_log=open('/private/tmp/quick-start-video-encoder.log','wb')
 encoder=subprocess.Popen([FFMPEG,'-hide_banner','-loglevel','error','-y',
  '-f','rawvideo','-pixel_format','rgba','-video_size',f'{video_width}x{video_height}',
  '-framerate',str(FPS),'-i','pipe:0','-an','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2',
  '-c:v','libx264','-preset','veryfast','-crf','12','-pix_fmt','yuv420p',
  '-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE,stderr=video_log)
 video_started=time.monotonic();recorder=QTimer(window)
 recorder.timeout.connect(write_video_frame);recorder.start(round(1000/FPS))

def capture(duration=1000,dialog=None):
 global recording_dialog
 settle();recording_dialog=dialog
 pix=snapshot(dialog)
 data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.WriteOnly);assert pix.save(buffer,'PNG')
 with Image.open(io.BytesIO(bytes(data))) as f:frames.append(f.convert('RGB'))
 durations.append(duration)
 QTest.qWait(duration)
 recording_dialog=None

def chapter(text):
 banner.setText(text);settle();chapters.append({'time_seconds':round(written_frames/FPS,3),'text':text});print('CHAPTER',text,flush=True)

def reveal(widget):
 parent=widget.parentWidget()
 while parent:
  if isinstance(parent,QScrollArea):parent.ensureWidgetVisible(widget,5,5)
  parent=parent.parentWidget()
 settle()

def animate_pointer(widget,pt,duration=500):
 target=widget.mapTo(window,pt);origin=pointer.pos()+QPoint(14,14)
 if (target-origin).manhattanLength()<2:return
 steps=max(12,round(duration*FPS/1000));started=time.monotonic()
 for n in range(1,steps+1):
  u=n/steps;eased=u*u*(3-2*u)
  position=QPoint(round(origin.x()+(target.x()-origin.x())*eased),round(origin.y()+(target.y()-origin.y())*eased))
  pointer.move(position.x()-14,position.y()-14);pointer.raise_()
  if widget is canvas.viewport():
   local=canvas.viewport().mapFrom(window,position)
   if canvas.viewport().rect().contains(local):QTest.mouseMove(canvas.viewport(),local)
  elif n==steps:QTest.mouseMove(widget,pt)
  delay=max(1,round(started*1000+duration*n/steps-time.monotonic()*1000))
  QTest.qWait(delay)

def indicate(widget,pt):
 animate_pointer(widget,pt)


def anonymize_file_dialog(dialog):
 global anonymized_file_dialogs
 if dialog.property('recordingAnonymized'):return
 dialog.setDirectory(str(SESSION))
 dialog.setSidebarUrls([QUrl.fromLocalFile(str(SESSION))])
 dialog.setHistory([str(SESSION)])
 assert [url.toLocalFile() for url in dialog.sidebarUrls()]==[str(SESSION)]
 dialog.setProperty('recordingAnonymized',True)
 anonymized_file_dialogs+=1
 dialog.grab().save(f'/private/tmp/quick-start-private-dialog-{anonymized_file_dialogs}.png')

def click(widget,pt=None,mod=Qt.NoModifier):
 reveal(widget);pt=pt or widget.rect().center();indicate(widget,pt);QTest.mouseClick(widget,Qt.LeftButton,mod,pt);settle(True)

def select_tab(tabs,index):
 bar=tabs.tabBar();click(bar,bar.tabRect(index).center())

def enter_value(widget,text):
 reveal(widget);click(widget);widget.selectAll();capture(300)
 edit=widget.lineEdit() if hasattr(widget,'lineEdit') else widget
 QTest.keyClicks(edit,text);QTest.keyClick(edit,Qt.Key_Return);settle(True);capture(650)

def map_pos(pt):
 p=canvas.getCoordinateTransform().transform(pt);return QPoint(round(p.x()),round(p.y()))

def move_map(start,end,count=6):
 # Interpolate actual mouse events on the map instead of jumping between
 # a few screenshots. The same eased motion is used for controls and tabs.
 animate_pointer(canvas.viewport(),start,450)
 duration=max(650,min(1500,round((end-start).manhattanLength()*2)))
 animate_pointer(canvas.viewport(),end,duration)


def handle_file_dialog(name,attempt=0):
 if QApplication.activeModalWidget() is None and attempt<40:
  QTimer.singleShot(100,lambda:handle_file_dialog(name,attempt+1));return
 try:
  dlg=QApplication.activeModalWidget();assert isinstance(dlg,QFileDialog),type(dlg)
  anonymize_file_dialog(dlg);dlg.resize(920,470);dlg.setViewMode(QFileDialog.Detail);settle();capture(1400,dlg)
  edit=dlg.findChild(QLineEdit,'fileNameEdit');assert edit
  edit.selectAll();QTest.keyClicks(edit,name);settle();capture(1500,dlg)
  buttons=dlg.findChild(QDialogButtonBox);save=next(b for b in buttons.buttons() if buttons.buttonRole(b)==QDialogButtonBox.AcceptRole);QTest.mouseClick(save,Qt.LeftButton)
 except Exception:
  traceback.print_exc();os._exit(2)

def handle_new_comment(attempt=0):
 if QApplication.activeModalWidget() is None and attempt<40:
  QTimer.singleShot(100,lambda:handle_new_comment(attempt+1));return
 try:
  dlg=QApplication.activeModalWidget();assert dlg
  capture(1200,dlg);edit=dlg.findChild(QLineEdit);assert edit;edit.selectAll();QTest.keyClicks(edit,'reference-area');capture(1300,dlg);dlg.accept()
 except Exception:traceback.print_exc();os._exit(3)

def handle_edit_comment(attempt=0):
 if QApplication.activeModalWidget() is None and attempt<40:
  QTimer.singleShot(100,lambda:handle_edit_comment(attempt+1));return
 try:
  dlg=QApplication.activeModalWidget();assert dlg and hasattr(dlg,'Txt_NewComment')
  capture(1400,dlg);dlg.Txt_NewComment.selectAll();QTest.keyClicks(dlg.Txt_NewComment,'spot-0001-check');capture(1400,dlg);QTest.mouseClick(dlg.Btn_OK,Qt.LeftButton)
 except Exception:traceback.print_exc();os._exit(4)

def handle_delete(attempt=0):
 if QApplication.activeModalWidget() is None and attempt<40:
  QTimer.singleShot(100,lambda:handle_delete(attempt+1));return
 try:
  dlg=QApplication.activeModalWidget();assert isinstance(dlg,QMessageBox),type(dlg)
  capture(1800,dlg);QTest.mouseClick(dlg.button(QMessageBox.Yes),Qt.LeftButton)
 except Exception:traceback.print_exc();os._exit(5)

def encode():
 recorder.stop();write_video_frame();encoder.stdin.close()
 assert encoder.wait(timeout=30)==0, 'Video encoding failed; see encoder log.'
 video_log.close()
 for n,(chapter_frame,chapter_meta) in enumerate(zip(frames,chapters)):
  if n%5==0:chapter_frame.save(f'/private/tmp/quick-start-video-frame-{n:02}.png')
 print('VIDEO_SAVED',VIDEO,VIDEO.stat().st_size,written_frames/FPS,flush=True)

QTimer.singleShot(1800,record)
