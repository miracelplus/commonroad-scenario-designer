from crdesigner.input_output.gui.gui_resources.MainWindow import Ui_mainWindow
from crdesigner.input_output.gui.gui_resources.scenario_saving_dialog import ScenarioDialog
from crdesigner.input_output.gui.misc.commonroad_viewer import AnimatedViewer
from meta.CONSTANTS import *
from gui.mwindow.service_layer.general_services import setup_tmp
from gui.mwindow.service_layer.general_services import setup_mwindow
from gui.mwindow.service_layer.file_actions import create_file_actions
from gui.mwindow.service_layer.setting_actions import create_setting_actions
from gui.mwindow.service_layer.help_actions import create_help_actions
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from typing import Union
from crdesigner.input_output.gui.settings import config
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle
from gui.mwindow.toolbar.toolbar import create_toolbar
from gui.mwindow.console.console import create_console
from gui.mwindow.toolboxes.road_network_toolbox.create_road_network_toolbox import create_road_network_toolbox
from gui.mwindow.toolboxes.converter_toolbox.create_converter_toolbox import create_converter_toolbox
from gui.mwindow.toolboxes.obstacle_toolbox.create_obstacle_toolbox import create_obstacle_toolbox
from gui.mwindow.service_layer.file_actions import file_new
from gui.mwindow.service_layer.file_actions import open_commonroad_file
from gui.mwindow.service_layer.file_actions import file_save
import logging
import copy
from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings
from crdesigner.input_output.gui.gui_src import CR_Scenario_Designer  # do not remove!!!  #TODO ask why

from PyQt5.QtWidgets import *


class MWindow(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        # init or set all attributes here
        self.tmp_folder = MWINDOW_TMP_FOLDER_PATH
        self.filename = None
        self.slider_clicked = False
        # Scenario + Lanelet variables
        self.scenarios = []
        self.current_scenario_index = -1
        # GUI attributes
        self.road_network_toolbox = None
        self.obstacle_toolbox = None
        self.map_converter_toolbox = None
        self.console = None
        self.play_activated = False
        self.text_browser = None
        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        # init any objects here
        self.scenario_saving_dialog = ScenarioDialog()
        self.cr_viewer = AnimatedViewer(self, self.viewer_callback)

        # call the setup methods in the service layer
        setup_tmp(tmp_folder_path=self.tmp_folder)
        setup_mwindow(self)
        self.fileNewAction, self.fileOpenAction, self.separator, self.fileSaveAction, self.exitAction = create_file_actions(mwindow=self)
        self.osm_settings, self.opendrive_settings, self.gui_settings, self.sumo_settings = create_setting_actions(mwindow=self)
        self.open_web, self.open_forum = create_help_actions(mwindow=self)
        self.create_viewer_dock()
        self.button_play_pause, self.label1, self.label2 = create_toolbar(mwindow=self,
                                                                          file_new=file_new,
                                                                          open_commonroad_file=open_commonroad_file,
                                                                          file_save=file_save)

        self.console, self.text_browser = create_console(mwindow=self)
        self.road_network_toolbox = create_road_network_toolbox(mwindow=self)
        self.obstacle_toolbox = create_obstacle_toolbox(mwindow=self)
        self.converter_toolbox = create_converter_toolbox(mwindow=self)

        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        #
        menu_bar = self.menuBar()  # instant of menu
        menu_file = menu_bar.addMenu('File')  # add menu 'file'
        menu_file.addAction(self.fileNewAction)
        menu_file.addAction(self.fileOpenAction)
        menu_file.addAction(self.fileSaveAction)
        menu_file.addAction(self.separator)
        menu_file.addAction(self.exitAction)

        menu_setting = menu_bar.addMenu('Setting')  # add menu 'Setting'
        menu_setting.addAction(self.gui_settings)
        menu_setting.addAction(self.sumo_settings)
        menu_setting.addAction(self.osm_settings)

        menu_help = menu_bar.addMenu('Help')  # add menu 'Help'
        menu_help.addAction(self.open_web)
        menu_help.addAction(self.open_forum)

        self.center()

        if path:
            self.open_path(path)

    # below here the functionality of the mwindow

    def viewer_callback(self, selected_object: Union[Lanelet, Obstacle], output: str):
        """
            TODO find out what this method does.
        """
        if isinstance(selected_object, Lanelet):
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_two.setCurrentText(
                    self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.currentText())
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.setCurrentText(
                    str(selected_object.lanelet_id))
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_update.setCurrentText(
                    str(selected_object.lanelet_id))
        elif isinstance(selected_object, Obstacle):
            self.obstacle_toolbox.obstacle_toolbox.selected_obstacle.setCurrentText(str(selected_object.obstacle_id))
        if output != "":
            self.text_browser.append(output)

    def create_viewer_dock(self):
        """Create the viewer dock."""
        self.viewer_dock = QWidget(self)
        toolbar = NavigationToolbar(self.cr_viewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.cr_viewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.setCentralWidget(self.viewer_dock)

    def update_view(self, focus_on_network=None):
        """ update all components."""
        # reset selection of all other selectable elements
        if self.cr_viewer.current_scenario is None:
            return
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.cr_viewer.update_plot(focus_on_network=focus_on_network)

    def toolbox_callback(self, scenario):
        """
        TODO find out why this is here.
        """
        if scenario is not None:
            self.cr_viewer.open_scenario(scenario)
            self.update_view(focus_on_network=True)
            self.update_max_step()
            self.store_scenario()

    def update_max_step(self, value: int = -1):
        """
        Update the max steps.
        """
        logging.info('update_max_step')
        value = value if value > -1 else self.cr_viewer.max_timestep
        self.label2.setText(' / ' + str(value))
        self.slider.setMaximum(value)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def store_scenario(self):
        self.scenarios.append(copy.deepcopy(self.cr_viewer.current_scenario))
        self.current_scenario_index += 1
        self.update_toolbox_scenarios()

    def update_toolbox_scenarios(self):
        scenario = self.cr_viewer.current_scenario
        self.road_network_toolbox.refresh_toolbox(scenario)
        self.obstacle_toolbox.refresh_toolbox(scenario)
        self.map_converter_toolbox.refresh_toolbox(scenario)
        if SUMO_AVAILABLE:
            self.obstacle_toolbox.sumo_simulation.scenario = scenario
            self.map_converter_toolbox.sumo_simulation.scenario = scenario