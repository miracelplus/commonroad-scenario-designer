import sys
import os
from lxml import etree

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.scenario.scenario import Scenario, LaneletNetwork

from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.V3_0.gui_toolbox import UpperToolbox
from crmapconverter.io.V3_0.gui_cr_viewer import AnimatedViewer
from crmapconverter.io.V3_0.converter_modules.osm_interface import OSMInterface
from crmapconverter.io.V3_0.converter_modules.opendrive_interface import (
    OpenDRIVEInterface)
from crmapconverter.io.V3_0.gui_settings import GUISettings
from crmapconverter.io.V3_0.SUMO_modules.sumo_settings import SUMOSettings
from crmapconverter.io.V3_0.SUMO_modules.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.viewer import LaneletList, IntersectionList, find_intersection_by_id
from crmapconverter.io.V3_0 import config


class MWindow(QMainWindow, Ui_mainWindow):
    """The Mainwindow of CR Scenario Designer."""
    def __init__(self, path=None):
        super(MWindow, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(True)

        # attributes
        self.filename = None
        self.crviewer = AnimatedViewer(self)
        self.lanelet_list = LaneletList(self.update_view, self)
        self.intersection_list = IntersectionList(self.update_view, self)
        self.count = 0
        self.timer = None
        self.ani_path = None
        self.slider_clicked = False

        # GUI attributes
        self.tool1 = None
        self.tool2 = None
        self.toolBox = None
        self.console = None
        self.textBrowser = None
        self.sumobox = SUMOSimulation()
        self.viewer_dock = None
        self.lanelet_list_dock = None
        self.intersection_list_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        # when the current scenario was simulated, load it in the gui
        self.sumobox.simulated_scenario.subscribe(self.open_scenario)

        # build and connect GUI
        self.create_file_actions()
        self.create_import_actions()
        self.create_export_actions()
        self.create_setting_actions()
        self.create_help_actions()
        self.create_viewer_dock()
        self.create_toolbar()
        self.create_console()
        self.create_toolbox()

        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        menu_bar = self.menuBar()  # instant of menu
        menu_file = menu_bar.addMenu('File')  # add menu 'file'
        menu_file.addAction(self.fileNewAction)
        menu_file.addAction(self.fileOpenAction)
        menu_file.addAction(self.fileSaveAction)
        menu_file.addAction(self.separator)
        menu_file.addAction(self.exitAction)

        menu_import = menu_bar.addMenu('Import')  # add menu 'Import'
        menu_import.addAction(self.importfromOpendrive)
        menu_import.addAction(self.importfromOSM)
        # menu_import.addAction(self.importfromSUMO)

        menu_export = menu_bar.addMenu('Export')  # add menu 'Export'
        menu_export.addAction(self.exportAsCommonRoad)
        # menu_export.addAction(self.export2SUMO)

        menu_setting = menu_bar.addMenu('Setting')  # add menu 'Setting'
        menu_setting.addAction(self.gui_settings)
        menu_setting.addAction(self.sumo_settings)
        menu_setting.addAction(self.osm_settings)
        # menu_setting.addAction(self.opendrive_settings)

        menu_help = menu_bar.addMenu('Help')  # add menu 'Help'
        menu_help.addAction(self.open_web)

        self.center()

        if path is not None:
            self.open_path(path)

    def show_osm_settings(self):
        osm_interface = OSMInterface(self)
        osm_interface.show_settings()

    def show_opendrive_settings(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.show_settings()

    def show_gui_settings(self):
        self.gui_settings = GUISettings(self)

    def show_sumo_settings(self):
        self.sumo_settings = SUMOSettings(self, config=self.suombox.config)

    def create_toolbox(self):
        """ Create the Upper toolbox."""
        self.uppertoolBox = UpperToolbox()

        self.tool1 = QDockWidget("ToolBox")
        self.tool1.setFloating(True)
        self.tool1.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool1.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool1.setWidget(self.uppertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool1)
        self.create_sumobox()
        self.uppertoolBox.button_sumo_simulation.clicked.connect(
            self.tool_box2_show)
        # self.uppertoolBox.button_lanlist.clicked.connect(
        #    self.show_lanelet_list)
        # self.uppertoolBox.button_intersection_list.clicked.connect(
        #    self.show_intersection_list)
        self.uppertoolBox.button_save.clicked.connect(self.save_animation)

    def create_lanelet_list(self):
        """Create the lanelet_list and put it into right Dockwidget area."""

        def remove_selection_and_close(_):
            """ remove selection from plot when list is closed"""
            self.lanelet_list.reset_selection()
            self.update_view()

        if self.lanelet_list_dock is not None:
            self.lanelet_list_dock.close()
            self.lanelet_list_dock = None
        self.lanelet_list_dock = QDockWidget("Lanelets")
        self.lanelet_list_dock.setFloating(True)
        self.lanelet_list_dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.lanelet_list_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.lanelet_list_dock.setWidget(self.lanelet_list)
        self.lanelet_list_dock.closeEvent = remove_selection_and_close
        self.addDockWidget(Qt.RightDockWidgetArea, self.lanelet_list_dock)

    def show_lanelet_list(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.lanelet_list_dock is None:
            if self.crviewer.current_scenario is None:
                messbox = QMessageBox()
                messbox.warning(
                    self, "Warning",
                    "Please load or convert a CR Scenario firstly",
                    QtWidgets.QMessageBox.Ok)
                messbox.close()
            else:
                self.lanelet_list_dock.show()
        else:
            self.lanelet_list_dock.show()

    def create_intersection_list(self):
        """Create the lanelet_list and put it into right Dockwidget area."""

        def remove_selection_and_close(_):
            """ remove selection from plot when list is closed"""
            self.intersection_list.reset_selection()
            self.update_view()

        if self.intersection_list_dock is not None:
            self.intersection_list_dock.close()
            self.intersection_list_dock = None
        self.intersection_list_dock = QDockWidget("Intersections")
        self.intersection_list_dock.setFloating(True)
        self.intersection_list_dock.setFeatures(
            QDockWidget.AllDockWidgetFeatures)
        self.intersection_list_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.intersection_list_dock.setWidget(self.intersection_list)
        self.intersection_list_dock.closeEvent = remove_selection_and_close
        self.addDockWidget(Qt.RightDockWidgetArea, self.intersection_list_dock)

    def show_intersection_list(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.intersection_list_dock is None:
            if self.crviewer.current_scenario is None:
                messbox = QMessageBox()
                messbox.warning(
                    self, "Warning",
                    "Please load or convert a CR Scenario or first",
                    QtWidgets.QMessageBox.Ok)
                messbox.close()
            else:
                self.intersection_list_dock.show()
        else:
            self.intersection_list_dock.show()

    def create_sumobox(self):
        """Function to create the sumo toolbox(bottom toolbox)."""
        self.tool2 = QDockWidget("Sumo Simulation", self)
        self.tool2.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool2.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool2.setWidget(self.sumobox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool2)
        self.tool2.setMaximumHeight(400)

    def detect_slider_clicked(self):
        self.slider_clicked = True
        print(self.slider_clicked)
        self.crviewer.pause()
        self.crviewer.dynamic.update_plot()

    def detect_slider_release(self):
        self.slider_clicked = False
        print(self.slider_clicked)
        self.crviewer.pause()

    def timestep_change(self, value):
        if self.crviewer.current_scenario is not None:
            self.crviewer.set_time_step(value)
            self.label1.setText('Timestep: ' + str(value))
            self.crviewer.animation.event_source.start()

    def play_animation(self):
        """Function connected with the play button in the sumo-toolbox."""
        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            reply = messbox.warning(
                self, "Warning", "You should firstly load a animated scenario",
                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.open_commonroad_file()
        else:
            self.crviewer.play()

    def pause_animation(self):
        """Function connected with the pause button in Toolbar."""
        self.crviewer.pause()

    def save_animation(self):
        """Function connected with the save button in the Toolbar."""
        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            reply = messbox.warning(self, "Warning",
                                    "You should firstly load an animation",
                                    QMessageBox.Ok | QMessageBox.No,
                                    QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.open_commonroad_file()
            else:
                messbox.close()
        else:
            self.crviewer.save_animation(
                self.uppertoolBox.save_menu.currentText())

    def create_console(self):
        """Function to create the console."""
        self.console = QDockWidget(self)
        self.console.setTitleBarWidget(QWidget(
            self.console))  # no title of Dock
        self.textBrowser = QtWidgets.QTextBrowser()
        self.textBrowser.setMaximumHeight(80)
        self.textBrowser.setObjectName("textBrowser")
        self.console.setWidget(self.textBrowser)
        self.console.setFloating(False)  # set if console can float
        self.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)

    def create_toolbar(self):
        """Function to create toolbar of the main Window."""
        tb1 = self.addToolBar("File")
        action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File",
                             self)
        tb1.addAction(action_new)
        action_new.triggered.connect(self.file_new)
        action_open = QAction(QIcon(":/icons/open_file.png"), "open CR File",
                              self)
        tb1.addAction(action_open)
        action_open.triggered.connect(self.open_commonroad_file)
        action_save = QAction(QIcon(":/icons/save_file.png"), "save CR File",
                              self)
        tb1.addAction(action_save)
        action_save.triggered.connect(self.file_save)
        tb1.addSeparator()
        tb2 = self.addToolBar("ToolBox")
        toolbox = QAction(QIcon(":/icons/tools.ico"),
                          "show Toolbox for CR Scenario", self)
        tb2.addAction(toolbox)
        toolbox.triggered.connect(self.tool_box1_show)
        tb2.addSeparator()
        lanelet_list = QAction(QIcon(":/icons/lanelet_list.ico"),
                               "show Lanelet list", self)
        intersection_list = QAction(QIcon(":/icons/intersection_list.ico"),
                                    "show Intersection list", self)
        tb2.addAction(lanelet_list)
        lanelet_list.triggered.connect(self.show_lanelet_list)
        tb2.addAction(intersection_list)
        intersection_list.triggered.connect(self.show_intersection_list)

        tb3 = self.addToolBar("Animation Play")
        self.button_play = QAction(QIcon(":/icons/play.png"),
                                   "Play the animation", self)
        self.button_play.triggered.connect(self.play_animation)
        tb3.addAction(self.button_play)
        self.button_pause = QAction(QIcon(":/icons/pause.png"),
                                    "Pause the animation", self)
        self.button_pause.triggered.connect(self.pause_animation)
        tb3.addAction(self.button_pause)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(300)
        self.slider.setValue(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(99)
        # self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setToolTip(
            "Show corresponding Scenario at selected timestep")
        self.slider.valueChanged.connect(self.timestep_change)
        self.slider.sliderPressed.connect(self.detect_slider_clicked)
        self.slider.sliderReleased.connect(self.detect_slider_release)
        self.crviewer.timestep.subscribe(self.slider.setValue)
        tb3.addWidget(self.slider)

        self.label1 = QLabel('  Step: 0', self)
        tb3.addWidget(self.label1)

        self.label2 = QLabel('      Total Step:', self)
        tb3.addWidget(self.label2)

    def update_max_step(self):
        self.label2.setText('      Total Step: ' +
                            str(self.crviewer.max_timestep))
        self.slider.setMaximum(self.crviewer.max_timestep)

    def create_import_actions(self):
        """Function to create the import action in the menu bar."""
        self.importfromOpendrive = self.create_action(
            "From OpenDrive",
            icon="",
            checkable=False,
            slot=self.od_2_cr,
            tip="Convert from OpenDrive to CommonRoad",
            shortcut=None)
        self.importfromOSM = self.create_action(
            "From OSM",
            icon="",
            checkable=False,
            slot=self.osm_2_cr,
            tip="Convert from OSM to CommonRoad",
            shortcut=None)

    def cr_2_osm(self):
        osm_interface = OSMInterface(self)
        osm_interface.start_export()

    def osm_2_cr(self):
        osm_interface = OSMInterface(self)
        osm_interface.start_import()

    def od_2_cr(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.start_import()

    def cr_2_od(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.start_import()

    def create_export_actions(self):
        """Function to create the export action in the menu bar."""
        self.exportAsCommonRoad = self.create_action(
            "As CommonRoad",
            icon="",
            checkable=False,
            slot=self.file_save,
            tip="Save as CommonRoad File (the same function as Save)",
            shortcut=None)

    def create_setting_actions(self):
        """Function to create the export action in the menu bar."""
        self.osm_settings = self.create_action(
            "OSM Settings",
            icon="",
            checkable=False,
            slot=self.show_osm_settings,
            tip="Show settings for osm converter",
            shortcut=None)
        self.opendrive_settings = self.create_action(
            "OpenDRIVE Settings",
            icon="",
            checkable=False,
            slot=self.show_opendrive_settings,
            tip="Show settings for OpenDRIVE converter",
            shortcut=None)
        self.gui_settings = self.create_action(
            "GUI Settings",
            icon="",
            checkable=False,
            slot=self.show_gui_settings,
            tip="Show settings for the CR Scenario Designer",
            shortcut=None)
        self.sumo_settings = self.create_action(
            "SUMO Settings",
            icon="",
            checkable=False,
            slot=self.show_sumo_settings,
            tip="Show settings for the SUMO interface",
            shortcut=None)

    def create_help_actions(self):
        """Function to create the help action in the menu bar."""
        self.open_web = self.create_action("Open CR Web",
                                           icon="",
                                           checkable=False,
                                           slot=self.open_cr_web,
                                           tip="Open CommonRoad Web",
                                           shortcut=None)

    def create_viewer_dock(self):
        self.viewer_dock = QWidget(self)
        toolbar = NavigationToolbar(self.crviewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.crviewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.setCentralWidget(self.viewer_dock)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def create_file_actions(self):
        """Function to create the file action in the menu bar."""
        self.fileNewAction = self.create_action(
            "New",
            icon=QIcon(":/icons/new_file.png"),
            checkable=False,
            slot=self.file_new,
            tip="New Commonroad File",
            shortcut=QKeySequence.New)
        self.fileOpenAction = self.create_action(
            "Open",
            icon=QIcon(":/icons/open_file.png"),
            checkable=False,
            slot=self.open_commonroad_file,
            tip="Open Commonroad File",
            shortcut=QKeySequence.Open)
        self.separator = QAction(self)
        self.separator.setSeparator(True)

        self.fileSaveAction = self.create_action(
            "Save",
            icon=QIcon(":/icons/save_file.png"),
            checkable=False,
            slot=self.file_save,
            tip="Save Commonroad File",
            shortcut=QKeySequence.Save)
        self.separator.setSeparator(True)
        self.exitAction = self.create_action("Quit",
                                             icon=QIcon(":/icons/close.png"),
                                             checkable=False,
                                             slot=self.closeWindow,
                                             tip="Quit",
                                             shortcut=QKeySequence.Close)

    def create_action(self,
                      text,
                      icon=None,
                      checkable=False,
                      slot=None,
                      tip=None,
                      shortcut=None):
        """Function to create the action in the menu bar."""
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(icon))
        if checkable:
            # toggle, True means on/off state, False means simply executed
            action.setCheckable(True)
            if slot is not None:
                action.toggled.connect(slot)
        else:
            if slot is not None:
                action.triggered.connect(slot)
        if tip is not None:
            action.setToolTip(tip)  # toolbar tip
            action.setStatusTip(tip)  # statusbar tip
        if shortcut is not None:
            action.setShortcut(shortcut)  # shortcut
        return action

    def open_cr_web(self):
        """Function to open the webseite of CommonRoad."""
        QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))

    def file_new(self):
        """Function to create the action in the menu bar."""
        scenario = Scenario(0.1, 'new scenario')
        net = LaneletNetwork()
        scenario.lanelet_network = net
        self.open_scenario(scenario)
        self.status.showMessage("Creating New File")

    def open_commonroad_file(self):
        """ """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open a CommonRoad scenario",
            "",
            "CommonRoad scenario files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )
        if not path:
            return
        self.open_path(path)

    def open_path(self, path):
        """ """

        filename = os.path.basename(path)
        try:
            commonroad_reader = CommonRoadFileReader(path)
            scenario, _ = commonroad_reader.open()
        except Exception as e:
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n"
                + "Syntax Error: {}".format(e),
                QMessageBox.Ok,
            )
            return
        self.open_scenario(scenario, filename)

    def open_scenario(self, new_scenario, filename="new_scenario"):
        """  """
        if self.check_scenario(new_scenario) > 2:
            return
        print("opening scneario")
        self.filename = filename
        self.crviewer.open_scenario(new_scenario, self.sumobox.config)
        self.sumobox.scenario = self.crviewer.current_scenario
        self.update_view(focus_on_network=True)
        self.update_to_new_scenario()

    def update_to_new_scenario(self):
        """  """
        self.update_max_step()
        self.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
        if self.crviewer.current_scenario is not None:
            self.create_lanelet_list()
            self.create_intersection_list()
            self.setWindowTitle(self.filename)
            self.textBrowser.append("loading " + self.filename)
            self.textBrowser.append(
                "Benchmark-ID: " + self.crviewer.current_scenario.benchmark_id)
        else:
            self.lanelet_list_dock.close()
            self.intersection_list_dock.close()

    def check_scenario(self, scenario) -> int:
        """ 
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        :return: score
        """
        POSSIBLE_ERROR_CAUSE = 1
        verbose = True
        
        error_score = 0

        # check if lanelets are valid polylines
        lanelet_ids = []
        for lanelet in scenario.lanelet_network.lanelets:
            polygon = lanelet.convert_to_polygon().shapely_object
            if not polygon.is_valid:
                lanelet_ids.append(lanelet.lanelet_id)
                self.textBrowser.append(
                    "Warning: Lanelet {} is invalid polygon!".format(
                        lanelet.lanelet_id))
                error_score = max(error_score, POSSIBLE_ERROR_CAUSE)
        if lanelet_ids and verbose:
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "Scenario contains faulty lanelet(s): " + str(lanelet_ids),
                QMessageBox.Ok,
            )

        return error_score

    def file_save(self):
        """Function to save a CR .xml file."""

        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            messbox.warning(self, "Warning", "There is no file to save!",
                            QMessageBox.Ok, QMessageBox.Ok)
            messbox.close()
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select file to save scenario",
            self.filename + ".xml",
            "CommonRoad files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )
        if not file_path:
            return

        try:
            fd = open(file_path, "w")
            fd.close()
            writer = CommonRoadFileWriter(
                scenario=self.crviewer.current_scenario,
                planning_problem_set=None,
                author="",
                affiliation="",
                source="",
                tags="",
            )
            writer.write_scenario_to_file(file_path)
        except IOError as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad file was not saved due to an error.\n\n" +
                "{}".format(e),
                QMessageBox.Ok,
            )

    def processtrigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    def closeWindow(self):
        reply = QMessageBox.warning(self, "Warning",
                                    "Do you really want to quit?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            qApp.quit()

    def closeEvent(self, event):
        event.ignore()
        self.closeWindow()

    def tool_box1_show(self):
        self.tool1.show()

    def tool_box2_show(self):
        self.tool2.show()

    def update_view(self, caller=None, focus_on_network=None):
        """ update all compoments. triggered by the component caller"""

        # reset selection of all other selectable elements
        if caller is not None:
            if caller is not self.intersection_list:
                self.intersection_list.reset_selection()
            if caller is not self.lanelet_list:
                self.lanelet_list.reset_selection()
        
        self.lanelet_list.update(self.crviewer.current_scenario)
        self.intersection_list.update(self.crviewer.current_scenario)

        if self.crviewer.current_scenario is None:
            return
        if self.intersection_list.selected_id is not None:
            selected_intersection = find_intersection_by_id(
                self.crviewer.current_scenario,
                self.intersection_list.selected_id)
        else:
            selected_intersection = None
        if self.lanelet_list.selected_id is not None:
            selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                self.lanelet_list.selected_id)
        else:
            selected_lanelet = None
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.crviewer.update_plot(scenario=self.crviewer.current_scenario,
                                  sel_lanelet=selected_lanelet,
                                  sel_intersection=selected_intersection,
                                  focus_on_network=focus_on_network)

    def make_trigger_exclusive(self):
        """ 
        Only one component can trigger the plot update
        """
        if self.lanelet_list.new:
            self.lanelet_list.new = False
            self.intersection_list.reset_selection()
        elif self.intersection_list.new:
            self.intersection_list.new = False
            self.lanelet_list.reset_selection()
        else:
            # triggered by click on canvas
            self.lanelet_list.reset_selection()
            self.intersection_list.reset_selection()

def main():

    # application
    app = QApplication(sys.argv)
    w = MWindow()
    w.showMaximized()
    w.open_path("/home/max/Desktop/Planning/Maps/cr_files/ped/intersect_and_crossing3.xml")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
