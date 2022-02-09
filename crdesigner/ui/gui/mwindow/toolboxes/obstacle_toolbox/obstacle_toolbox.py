from typing import List
import matplotlib as mpl
import numpy as np
import math
import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.geometry.polyline_util import *
from commonroad.geometry.shape import Rectangle, Circle, Polygon
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle, StaticObstacle, ObstacleType, DynamicObstacle
from commonroad.scenario.trajectory import State, Trajectory

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

from crdesigner.ui.gui.mwindow.toolboxes.obstacle_toolbox.obstacle_toolbox_ui import ObstacleToolboxUI

from commonroad.prediction.prediction import Prediction, Occupancy, SetBasedPrediction, TrajectoryPrediction


class ObstacleToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, callback, tmp_folder, text_browser):
        super().__init__("Obstacle Toolbox")

        self.current_scenario = current_scenario
        self.callback = callback
        self.obstacle_toolbox_ui = ObstacleToolboxUI(text_browser)
        self.adjust_ui()
        self.connect_gui_elements()
        self.tmp_folder = tmp_folder
        self.text_browser = text_browser
        self.update_ongoing = False
        self.init_canvas()
        self.amount_obstacles = 0

        # for profile visualisation
        self.sel_point = None
        self.xyova = []
        self.pos = []
        self.temp_obstacle = None

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=tmp_folder)
        else:
            self.sumo_simulation = None

    def init_canvas(self):
        """
        so profile visualization canvas can handle events
        """
        self.obstacle_toolbox_ui.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.obstacle_toolbox_ui.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.obstacle_toolbox_ui.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def adjust_ui(self):
        """
        Updates GUI properties like width, etc.
        """
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.obstacle_toolbox_ui)
        self.obstacle_toolbox_ui.setMinimumWidth(450)

    def connect_gui_elements(self):
        """
        adds functionality to gui elements like buttons, menus etc
        """
        self.initialize_obstacle_information()

        self.obstacle_toolbox_ui.selected_obstacle.currentTextChanged.connect(
                lambda: self.update_obstacle_information())
        self.obstacle_toolbox_ui.button_update_obstacle.clicked.connect(lambda: self.update_obstacle())

        self.obstacle_toolbox_ui.obstacle_state_variable.currentTextChanged.connect(
                lambda: self.plot_obstacle_state_profile())

        self.obstacle_toolbox_ui.button_remove_obstacle.clicked.connect(lambda: self.remove_obstacle())

        self.obstacle_toolbox_ui.button_add_static_obstacle.clicked.connect(lambda: self.add_obstacle())
        
        self.obstacle_toolbox_ui.obstacle_shape.currentTextChanged.connect(
            lambda: self.obstacle_toolbox_ui.toggle_sections())
        
        self.obstacle_toolbox_ui.obstacle_dyn_stat.currentTextChanged.connect(
            lambda: self.obstacle_toolbox_ui.toggle_dynamic_static())

        if SUMO_AVAILABLE:
            self.obstacle_toolbox_ui.button_start_simulation.clicked.connect(lambda: self.start_sumo_simulation())

    def collect_obstacle_ids(self) -> List[int]:
        """
        Collects IDs of all obstacles within a CommonRoad scenario.
        @return:
        """
        if self.current_scenario is not None:
            return [obs.obstacle_id for obs in self.current_scenario.obstacles]
        else:
            return []

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def static_obstacle_details(self, obstacle_id: int):
        """
        Creates static obstacles
        :param obstacle_id: id of static obstacle to be created
        """
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            static_obstacle = StaticObstacle(obstacle_id=obstacle_id,
                                             obstacle_type=ObstacleType(
                                                     self.obstacle_toolbox_ui.obstacle_type.currentText()),
                                             obstacle_shape=Rectangle(
                                                     length=float(self.obstacle_toolbox_ui.obstacle_length.text()),
                                                     width=float(self.obstacle_toolbox_ui.obstacle_width.text())),
                                             initial_state=State(**{'position': np.array(
                                                     [float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                                                      float(self.obstacle_toolbox_ui.obstacle_y_Position.text())]),
                                                 'orientation': math.radians(float(
                                                         self.obstacle_toolbox_ui.obstacle_orientation.text())),
                                                 'time_step': 1}))
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            static_obstacle = StaticObstacle(obstacle_id=obstacle_id,
                                             obstacle_type=ObstacleType(
                                                     self.obstacle_toolbox_ui.obstacle_type.currentText()),
                                             obstacle_shape=Circle(
                                                     radius=float(self.obstacle_toolbox_ui.obstacle_radius.text())),
                                             initial_state=State(**{'position': np.array(
                                                     [float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                                                      float(self.obstacle_toolbox_ui.obstacle_y_Position.text())]),
                                                 'orientation': 0, 'time_step': 1}))
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            static_obstacle = StaticObstacle(
                obstacle_id=obstacle_id,

                obstacle_type=ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape=Polygon(
                    vertices=self.polygon_array()
                ),

                initial_state=State(**{'position': np.array([
                                        0,
                                        0
                                    ]),
                                    'orientation': 0, 
                                    'time_step': 1
                                    })
            )
        self.current_scenario.add_objects(static_obstacle)
        self.callback(self.current_scenario)

    def dynamic_obstacle_details(self, obstacle_id: int):
        """
        creates dynamic obstacles
        :param obstacle_id: id of static obstacle to be created
        """
        if self.xyova:
            initial_position = np.array([self.xyova[0][0], self.xyova[0][1]])
            state_dictionary = {'position': initial_position,
                                'velocity': self.xyova[0][3],
                                'orientation': self.xyova[0][2], 'time_step': 0}

            if self.xyova[0][4] is not None:
                state_dictionary.update({'acceleration': self.xyova[0][4]})
            if self.xyova[0][5] is not None:
                state_dictionary.update({'yaw_rate': self.xyova[0][5]})
            if self.xyova[0][6] is not None:
                state_dictionary.update({'slip_angle': self.xyova[0][6]})

        elif self.temp_obstacle is not None: # is not None during an update
            initial_position = np.array([self.temp_obstacle.initial_state.__getattribute__("position")[0],
                                        self.temp_obstacle.initial_state.__getattribute__("position")[1]])
            state_dictionary = {'position': initial_position,
                                'velocity': self.temp_obstacle.initial_state.__getattribute__("velocity"),
                                'orientation': self.temp_obstacle.initial_state.__getattribute__("orientation"),
                                'time_step': 0}

            if "acceleration" in self.temp_obstacle.initial_state.attributes:
                state_dictionary.update({'acceleration': self.temp_obstacle.initial_state.__getattribute__("acceleration")})
            if "yaw_rate" in self.temp_obstacle.initial_state.attributes:
                state_dictionary.update({'yaw_rate': self.temp_obstacle.initial_state.__getattribute__("yaw_rate")})
            if "slip_angle" in self.temp_obstacle.initial_state.attributes:
                state_dictionary.update({'slip_angle': self.temp_obstacle.initial_state.__getattribute__("slip_angle")})

        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            dynamic_obstacle = DynamicObstacle(
                obstacle_id=obstacle_id,

                obstacle_type=ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape=Rectangle(
                    length=float(self.obstacle_toolbox_ui.obstacle_length.text()),
                    width=float(self.obstacle_toolbox_ui.obstacle_width.text()),
                    orientation=float(self.obstacle_toolbox_ui.obstacle_orientation.text())
                ),

                initial_state=State(**state_dictionary),
                prediction=TrajectoryPrediction(
                    shape=Rectangle(float(self.obstacle_toolbox_ui.obstacle_length.text()),
                                    width=float(self.obstacle_toolbox_ui.obstacle_width.text())),
                    trajectory=Trajectory(
                        initial_time_step=1,
                        state_list=self.calc_state_list()
                    )
                )
            )

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            dynamic_obstacle = DynamicObstacle(
                obstacle_id=obstacle_id,

                obstacle_type=ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape=Circle(
                    radius=float(self.obstacle_toolbox_ui.obstacle_radius.text())
                ),

                initial_state=State(**state_dictionary),
                prediction=TrajectoryPrediction(
                    shape=Circle(float(self.obstacle_toolbox_ui.obstacle_radius.text())),
                    trajectory=Trajectory(
                        initial_time_step=1,
                        state_list=self.calc_state_list()
                    )
                )
            )

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            dynamic_obstacle = DynamicObstacle(
                obstacle_id=obstacle_id,

                obstacle_type=ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape=Polygon(

                    vertices=self.polygon_array()
                ),

                initial_state=State(**state_dictionary),
                prediction=TrajectoryPrediction(
                    shape=Polygon(vertices=self.polygon_array()),
                    trajectory=Trajectory(
                        initial_time_step=1,
                        state_list=self.initial_trajectory()
                    )
                )

            )
        self.current_scenario.add_objects(dynamic_obstacle)       
        self.callback(self.current_scenario)

    def calc_state_list(self):
        """
        Calculates the trajectory, orientation, yaw_rate, slip_angle, etc
        for the dynamic obstacle based on changes in profile visualization.
        If no changes just reuse the old values
        :return: state_list which is an array of states
        """
        state_list = []

        # if updating positions in profile visualisation
        if self.xyova:
            for j in range(1, len(self.xyova)):
                new_position = np.array([self.xyova[j][0], self.xyova[j][1]])
                state_dictionary = {'position': new_position, 'velocity': self.xyova[j][3],
                                    'orientation': self.xyova[j][2], 'time_step': j}

                if self.xyova[j][4] is not None:
                    state_dictionary.update({'acceleration': self.xyova[j][4]})
                if self.xyova[j][5] is not None:
                    state_dictionary.update({'yaw_rate': self.xyova[j][5]})
                if self.xyova[j][6] is not None:
                    state_dictionary.update({'slip_angle': self.xyova[j][6]})

                new_state = State(**state_dictionary)
                state_list.append(new_state)
            return state_list

        else:
            for state in self.temp_obstacle.prediction.trajectory.state_list:
                new_position = np.array([state.__getattribute__("position")[0],
                                            state.__getattribute__("position")[1]])
                state_dictionary = {'position': new_position,
                                    'velocity': state.__getattribute__("velocity"),
                                    'orientation': state.__getattribute__("orientation"),
                                    'time_step': state.__getattribute__("time_step")}

                if "acceleration" in state.attributes:
                    state_dictionary.update({'acceleration': state.__getattribute__("acceleration")})
                if "yaw_rate" in state.attributes:
                    state_dictionary.update({'yaw_rate': state.__getattribute__("yaw_rate")})
                if "slip_angle" in state.attributes:
                    state_dictionary.update({'slip_angle': state.__getattribute__("slip_angle")})

                new_state = State(**state_dictionary)
                state_list.append(new_state)
            return state_list

    def polygon_array(self):
        """
        Stores values from gui menu as floats (vertice coordinates)
        :return: a list of the vertices from the gui menu
        """
        vertices = []
        for i in range(self.obstacle_toolbox_ui.amount_vertices):
            if self.obstacle_toolbox_ui.vertices_x[i].text() != "" and \
                    self.obstacle_toolbox_ui.vertices_y[i].text() != "":
                temp = [float(self.obstacle_toolbox_ui.vertices_x[i].text()),
                        float(self.obstacle_toolbox_ui.vertices_y[i].text())]
                vertices.append(temp)

        if len(vertices) < 3:
            self.text_browser.append("At least 3 vertices are needed to create a polygon")
            return

        vertices = np.asarray(vertices)
        return vertices

    def get_current_obstacle(self):
        """
        :return: current selected obstacle
        """
        obstacle_id = self.get_current_obstacle_id()
        selected_obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
        return selected_obstacle

    def get_current_obstacle_id(self):
        """
        :return: obstacle_id of current selected obstacle
        """
        return int(self.obstacle_toolbox_ui.selected_obstacle.currentText())

    def add_obstacle(self):
        """
        generates an object_id (id for obstacle) and then calls function
        to create a static or dynamic obstacle
        """
        obstacle_id = self.current_scenario.generate_object_id()
        self.amount_obstacles = self.current_scenario.generate_object_id()

        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Dynamic":
            try:
                self.dynamic_obstacle_details(obstacle_id)
            except Exception as e:
                self.text_browser.append("Error when adding dynamic obstacle")
        elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Static":
            try:
                self.static_obstacle_details(obstacle_id)
            except Exception as e:
                self.text_browser.append("Error when adding static obstacle")

    def update_obstacle(self):
        """
        updates obstacle by deleting it and then adding it again with same id
        """

        selected_obstacle = self.get_current_obstacle()
        obstacle_id = self.get_current_obstacle_id()
        self.temp_obstacle = selected_obstacle

        if selected_obstacle:
            self.current_scenario.remove_obstacle(selected_obstacle)

        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Static":
            try:
                self.static_obstacle_details(obstacle_id)
            except Exception as e:
                self.text_browser.append("Error when updating static obstacle")

        elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Dynamic":
            try:
                self.dynamic_obstacle_details(obstacle_id)
                self.xyova.clear()
            except Exception as e:
                self.text_browser.append("Error when updating dynamic obstacle")

        self.temp_obstacle = None

    def initialize_toolbox(self):
        self.initialize_obstacle_information()

    def calc_velocity(self, point1: float, point2: float):
        """
        calculates velocity based on two points
        :return: velocity between two points
        """
        distance = math.dist(point1, point2)
        velocity = distance / self.current_scenario.dt
        return velocity

    def calc_acceleration(self, velocity1: float, velocity2: float):
        """calculates acceleration based on the velocity at 2 points"""
        delta_v = velocity2 - velocity1
        acceleration = delta_v / self.current_scenario.dt
        return acceleration

    def initialize_obstacle_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.clear_obstacle_fields()

        self.obstacle_toolbox_ui.selected_obstacle.clear()
        self.obstacle_toolbox_ui.selected_obstacle.addItems(
                ["None"] + [str(item) for item in self.collect_obstacle_ids()])
        self.obstacle_toolbox_ui.selected_obstacle.setCurrentIndex(0)

    def delete_point(self):
        """
        deletes right clicked point
         """
        time = []
        profile = []
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()

        if self.sel_point:
            if not self.xyova:
                self.calculate_xyova()
            self.xyova.pop(self.sel_point[0])
            # removes point at specified timestep
            self.pos.pop(self.sel_point[0])

            for i in self.pos:
                time.append(i[0])
                profile.append(i[1])

        self.draw_plot(time, profile, self.xmin, self.xmax, self.ymin, self.ymax)

        self.sel_point = None

    def on_button_press(self, event):
        """"
        when left or right mouse button is pressed
        """
        if event.inaxes is None:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        # if using zoom or move tool (0 is standard cursor)
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return
        self.sel_point = self.selected_point(event)
        # if no point is selected (pressed too far away from point)
        if self.sel_point is None:
            return
        if event.button == 3:
            self.delete_point()

    def on_button_release(self, event):
        """
        Updates obstacle when left mouse button is released
        if xyova already exists: save changed values to that array
        otherwise create the array and store changes
        """
        if event.button != 1:
            return
        if self.sel_point is None:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return

        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        i = 0
        k = 1
        # so all not updated changes are saved (when switching profile)
        if self.xyova:
            for j in self.xyova:
                if state_variable_name == "x-position":
                    j[0] = self.pos[i][1]
                    # change velocity based on changes in x-position
                    self.xyova[k][3] = self.calc_velocity([self.pos[k-1][1], self.xyova[k-1][1]],
                                                          [self.pos[k][1], self.xyova[k][1]])
                    # change acceleration based on changes in velocity
                    if self.xyova[i][4] is not None:
                        self.xyova[k][4] = self.calc_acceleration(self.xyova[k-1][3], self.xyova[k][3])
                elif state_variable_name == "y-position":
                    j[1] = self.pos[i][1]

                    self.xyova[k][3] = self.calc_velocity([self.xyova[k-1][0], self.pos[k-1][1]], 
                        [self.xyova[k][0], self.pos[k][1]])
                    if self.xyova[i][4] is not None:
                        self.xyova[k][4] = self.calc_acceleration(self.xyova[k-1][3], self.xyova[k][3])

                elif state_variable_name == "orientation":
                    j[2] = self.pos[i][1]
                    if j[2] == self.xyova[0][2]:
                        self.obstacle_toolbox_ui.obstacle_orientation.setText(str(j[2]))
                elif state_variable_name == "velocity":
                    j[3] = self.pos[i][1]
                elif state_variable_name == "acceleration":
                    j[4] = self.pos[i][1]
                elif state_variable_name == "yaw_rate":
                    j[5] = self.pos[i][1]
                elif state_variable_name == "slip_angle":
                    j[6] = self.pos[i][1]
                i += 1
                if k < len(self.xyova) - 1:
                    k += 1
        else:
            self.calculate_xyova()

        self.sel_point = None

    def on_mouse_move(self, event):
        """
        update position of selected point by moving mouse
        and holding down left mouse button
        """
        if self.sel_point is None:
            return
        if event.button != 1:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return

        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        time = []
        profile = []
    
        self.calculate_pos()
        self.sel_point[1] = event.ydata
        self.pos[self.sel_point[0]][1] = self.sel_point[1]
    
        for i in self.pos:
            time.append(i[0])
            profile.append(i[1])

        self.draw_plot(time, profile, self.xmin, self.xmax, self.ymin, self.ymax)

    def calculate_xyova(self):
        """
        calculate xyova array which keeps track of not updated changes
        Eg, if change orientation by dragging the points, those changes
        are stored in this array
        """
        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        i = 0
        k = 1

        if state_variable_name == "x-position":
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            o = selected_obstacle.initial_state.__getattribute__("orientation")
            try:
                a = selected_obstacle.initial_state.__getattribute__("acceleration")
            except:
                a = None
            try:
                yaw_rate = selected_obstacle.initial_state.__getattribute__("yaw_rate")
            except:
                yaw_rate = None
            try:
                slip_angle = selected_obstacle.initial_state.__getattribute__("slip_angle")
            except:
                slip_angle = None

            v = self.calc_velocity([self.pos[k-1][1], y], [self.pos[k][1], y])
            self.xyova.append([self.pos[i][1], y, o, v, a, yaw_rate, slip_angle])

        elif state_variable_name == "y-position":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            o = selected_obstacle.initial_state.__getattribute__("orientation")
            try:
                a = selected_obstacle.initial_state.__getattribute__("acceleration")
            except:
                a = None
            try:
                yaw_rate = selected_obstacle.initial_state.__getattribute__("yaw_rate")
            except:
                yaw_rate = None
            try:
                slip_angle = selected_obstacle.initial_state.__getattribute__("slip_angle")
            except:
                slip_angle = None

            v = self.calc_velocity([x, self.pos[k-1][1]], [x, self.pos[k][1]])
            self.xyova.append([x, self.pos[i][1], o, v, a, yaw_rate, slip_angle])

        elif state_variable_name == "orientation":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            v = selected_obstacle.initial_state.__getattribute__("velocity")
            try:
                a = selected_obstacle.initial_state.__getattribute__("acceleration")
            except:
                a = None
            try:
                yaw_rate = selected_obstacle.initial_state.__getattribute__("yaw_rate")
            except:
                yaw_rate = None
            try:
                slip_angle = selected_obstacle.initial_state.__getattribute__("slip_angle")
            except:
                slip_angle = None

            self.xyova.append([x, y, self.pos[i][1], v, a, yaw_rate, slip_angle])

        elif state_variable_name == "yaw_rate":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            v = selected_obstacle.initial_state.__getattribute__("velocity")
            o = selected_obstacle.initial_state.__getattribute__("orientation")
            try:
                a = selected_obstacle.initial_state.__getattribute__("acceleration")
            except:
                a = None
            try:
                slip_angle = selected_obstacle.initial_state.__getattribute__("slip_angle")
            except:
                slip_angle = None

            self.xyova.append([x, y, o, v, a, self.pos[i][1], slip_angle])

        elif state_variable_name == "slip_angle":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            v = selected_obstacle.initial_state.__getattribute__("velocity")
            o = selected_obstacle.initial_state.__getattribute__("orientation")
            try:
                a = selected_obstacle.initial_state.__getattribute__("acceleration")
            except:
                a = None
            try:
                yaw_rate = selected_obstacle.initial_state.__getattribute__("yaw_rate")
            except:
                yaw_rate = None

            self.xyova.append([x, y, o, v, a, yaw_rate, self.pos[i][1]])

        i += 1
        k += 1

        for state in selected_obstacle.prediction.trajectory.state_list:
            if state_variable_name == "x-position":
                y = state.__getattribute__("position")[1]
                o = state.__getattribute__("orientation")
                try:
                    yaw_rate = state.__getattribute__("yaw_rate")
                except:
                    yaw_rate = None
                try:
                    slip_angle = state.__getattribute__("slip_angle")
                except:
                    slip_angle = None
                
                v_previous = v
                v = self.calc_velocity([self.pos[k-1][1], y], [self.pos[k][1], y])
                if a is not None: # if accelaration is a part of the state
                    a = self.calc_acceleration(v_previous, v)

                self.xyova.append([self.pos[i][1], y, o, v, a, yaw_rate, slip_angle])

            elif state_variable_name == "y-position":
                x = state.__getattribute__("position")[0]
                o = state.__getattribute__("orientation")
                try:
                    yaw_rate = state.__getattribute__("yaw_rate")
                except:
                    yaw_rate = None
                try:
                    slip_angle = state.__getattribute__("slip_angle")
                except:
                    slip_angle = None

                v_previous = v
                v = self.calc_velocity([x, self.pos[k-1][1]], [x, self.pos[k][1]])
                if a is not None:
                    a = self.calc_acceleration(v_previous, v)
                   
                self.xyova.append([x, self.pos[i][1], o, v, a, yaw_rate, slip_angle])

            elif state_variable_name == "orientation":
                x = state.__getattribute__("position")[0]
                y = state.__getattribute__("position")[1]
                v = state.__getattribute__("velocity")
                try:
                    a = state.__getattribute__("acceleration")
                except:
                    a = None
                try:
                    yaw_rate = state.__getattribute__("yaw_rate")
                except:
                    yaw_rate = None
                try:
                    slip_angle = state.__getattribute__("slip_angle")
                except:
                    slip_angle = None

                self.xyova.append([x, y, self.pos[i][1], v, a, yaw_rate, slip_angle])

            elif state_variable_name == "yaw_rate":
                x = state.__getattribute__("position")[0]
                y = state.__getattribute__("position")[1]
                v = state.__getattribute__("velocity")
                o = state.__getattribute__("orientation")
                try:
                    a = state.__getattribute__("acceleration")
                except:
                    a = None
                try:
                    slip_angle = state.__getattribute__("slip_angle")
                except:
                    slip_angle = None

                self.xyova.append([x, y, o, v, a, self.pos[i][1], slip_angle])

            elif state_variable_name == "slip_angle":
                x = state.__getattribute__("position")[0]
                y = state.__getattribute__("position")[1]
                v = state.__getattribute__("velocity")
                o = state.__getattribute__("orientation")
                try:
                    a = state.__getattribute__("acceleration")
                except:
                    a = None
                try:
                    yaw_rate = state.__getattribute__("yaw_rate")
                except:
                    slip_angle = None

                self.xyova.append([x, y, o, v, a, yaw_rate, self.pos[i][1]])
            i += 1
            if k < len(selected_obstacle.prediction.trajectory.state_list): 
                k += 1

    def calculate_pos(self):
        """
        calculates the self.pos array which is the array that
        contains the data that is displayed in the plot
        """
        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        self.pos.clear()
        t = 0
        if self.xyova:
            for i in self.xyova: 
                if state_variable_name == "x-position":
                    x = i[0]
                    self.pos.append([t,x])
                elif state_variable_name == "y-position":
                    y = i[1]
                    self.pos.append([t,y])
                elif state_variable_name == "orientation":
                    o = i[2]
                    self.pos.append([t,o])
                elif state_variable_name == "yaw_rate":
                    yaw_rate = i[5]
                    self.pos.append([t,yaw_rate])
                elif state_variable_name == "slip_angle":
                    slip_angle = i[6]
                    self.pos.append([t,slip_angle])
                t += 1
        else:

            if state_variable_name == "x-position":
                x = selected_obstacle.initial_state.__getattribute__("position")[0]
                self.pos.append([t,x])
            elif state_variable_name == "y-position":
                y = selected_obstacle.initial_state.__getattribute__("position")[1]
                self.pos.append([t,y])
            elif state_variable_name == "orientation":
                o = selected_obstacle.initial_state.__getattribute__("orientation")
                self.pos.append([t,o])
            elif state_variable_name == "yaw_rate":
                yaw_rate = selected_obstacle.initial_state.__getattribute__("yaw_rate")
                self.pos.append([t,yaw_rate])
            elif state_variable_name == "slip_angle":
                slip_angle = selected_obstacle.initial_state.__getattribute__("slip_angle")
                self.pos.append([t,slip_angle])

            for state in selected_obstacle.prediction.trajectory.state_list:
                t = state.__getattribute__("time_step")
                if state_variable_name == "x-position":
                    x = state.__getattribute__("position")[0]
                    self.pos.append([t,x])
                elif state_variable_name == "y-position":
                    y = state.__getattribute__("position")[1]
                    self.pos.append([t,y])
                elif state_variable_name == "orientation":
                    o = state.__getattribute__("orientation")
                    self.pos.append([t,o])
                elif state_variable_name == "yaw_rate":
                    yaw_rate = state.__getattribute__("yaw_rate")
                    self.pos.append([t,yaw_rate])
                elif state_variable_name == "slip_angle":
                    slip_angle = state.__getattribute__("slip_angle")
                    self.pos.append([t,slip_angle])

    def on_xlim_change(self, event):
        self.xmin, self.xmax = event.get_xlim()
    
    def on_ylim_change(self, event):
        self.ymin, self.ymax = event.get_ylim()

    def selected_point(self, event):
        """
        get the time step of the where the point is located
        :return: sel_point, the time step of the selected point
        """

        pos = []
        sel_point = None

        self.calculate_pos()

        # calculate nearest point from mouse click
        for i in range(0, len(self.pos)):
            # distance between cursor and points
            distance = math.dist(self.pos[i], [event.xdata, event.ydata])
            if i == 0:
                smallest_distance = distance
            if distance < 1 and distance <= smallest_distance: 
                smallest_distance = distance
                sel_point = self.pos[i]
        return sel_point

    def plot_obstacle_state_profile(self):
        """
        Gets the values based on which profile is selected.
        If non updated changes, these values come from the xyova array,
        otherwise directly from the obstacle state_list
        """
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"] and not self.update_ongoing:
            obstacle = self.get_current_obstacle()
            state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
            if state_variable_name == "x-position":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("position")[0]]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[0] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("position")[0]]
                        profile += [state.__getattribute__("position")[0]
                                for state in obstacle.prediction.trajectory.state_list]
            elif state_variable_name == "y-position":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("position")[1]]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[1] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("position")[1]]
                        profile += [state.__getattribute__("position")[1]
                                for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "velocity" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[3] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("velocity")]
                    profile += [state.__getattribute__("velocity")
                            for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "acceleration" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[4] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("acceleration")]
                    profile += [state.__getattribute__("acceleration")
                        for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "yaw_rate" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[5] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("yaw_rate")]
                    profile += [state.__getattribute__("yaw_rate")
                        for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "slip_angle" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[6] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("slip_angle")]
                    profile += [state.__getattribute__("slip_angle")
                        for state in obstacle.prediction.trajectory.state_list]
            
            elif state_variable_name == "orientation":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("orientation")]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[2] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("orientation")]
                        profile += [state.__getattribute__("orientation")
                                for state in obstacle.prediction.trajectory.state_list]
        
            if isinstance(obstacle, DynamicObstacle):
                if self.xyova:
                    time = [i for i in range(0, len(self.xyova))]
                else:
                    time = [obstacle.initial_state.time_step]
                    time += [state.time_step for state in obstacle.prediction.trajectory.state_list]
            else:
                time = [0]

            self.xmin = None
            self.xmax = None 
            self.ymin = None 
            self.ymax = None
            self.draw_plot(time, profile)

    @staticmethod
    def resolve_y_label(state_variable_name: str) -> str:
        """
        Creates y-label of state variable.

        @param state_variable_name: State variable from commonroad-io.
        @return: State variable with unit for visualization.
        """
        if state_variable_name == "x-position":
            return "x-position [m]"
        elif state_variable_name == "y-position":
            return "y-position [m]"
        elif state_variable_name == "orientation":
            return "orientation [rad]"
        elif state_variable_name == "velocity":
            return "velocity [m/s]"
        elif state_variable_name == "acceleration":
            return "acceleration [m/s^2]"
        else:
            return ""

    def update_obstacle_information(self):
        """
        retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox
        """
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:

            self.update_ongoing = True
            obstacle = self.get_current_obstacle()
            if isinstance(obstacle.obstacle_shape, Rectangle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Rectangle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(0)

                self.obstacle_toolbox_ui.obstacle_width.setText(str(obstacle.obstacle_shape.width))
                self.obstacle_toolbox_ui.obstacle_length.setText(str(obstacle.obstacle_shape.length))
                if isinstance(obstacle, StaticObstacle):
                    self.obstacle_toolbox_ui.obstacle_x_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[0]))
                    self.obstacle_toolbox_ui.obstacle_y_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[1]))
                    self.obstacle_toolbox_ui.obstacle_orientation.setText(
                        str(math.degrees(obstacle.initial_state.__getattribute__("orientation"))))
                else:
                    self.obstacle_toolbox_ui.obstacle_orientation.setText(
                        str(math.degrees(obstacle.obstacle_shape.__getattribute__("orientation"))))

            elif isinstance(obstacle.obstacle_shape, Circle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Circle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(1)

                self.obstacle_toolbox_ui.obstacle_radius.setText(str(obstacle.obstacle_shape.radius))
                if isinstance(obstacle, StaticObstacle):
                    self.obstacle_toolbox_ui.obstacle_x_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[0]))
                    self.obstacle_toolbox_ui.obstacle_y_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[1]))

            elif isinstance(obstacle.obstacle_shape, Polygon):
                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Polygon":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(2)

                    # because numpy array has weird formatting I want to get rid of
                temp = obstacle.obstacle_shape.vertices
                vertices = temp.tolist()

                # remove extra vertice(s) in toolbox
                if len(vertices) - 1 < self.obstacle_toolbox_ui.amount_vertices:
                    j = self.obstacle_toolbox_ui.amount_vertices - (len(vertices) - 1)
                    for i in range(j):
                        self.obstacle_toolbox_ui.remove_vertice(i)

                for i in range(len(vertices) - 1):
                    # adds another vertice if there are too few in the toolbox
                    if i >= self.obstacle_toolbox_ui.amount_vertices:
                        self.obstacle_toolbox_ui.add_vertice()

                    vertice_string_x = str(vertices[i][0])
                    vertice_string_y = str(vertices[i][1])
                    self.obstacle_toolbox_ui.vertices_x[i].setText(vertice_string_x)
                    self.obstacle_toolbox_ui.vertices_y[i].setText(vertice_string_y)
            
            if isinstance(obstacle, DynamicObstacle):

                if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() != "Dynamic":
                    self.obstacle_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(1)

            elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() != "Static":
                self.obstacle_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(0)

            self.obstacle_toolbox_ui.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
            self.obstacle_toolbox_ui.obstacle_state_variable.clear()
            state_variables = [var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]]

            if "position" in obstacle.initial_state.attributes:
                state_variables += ["x-position", "y-position"]

            self.obstacle_toolbox_ui.obstacle_state_variable.addItems(state_variables)
            self.update_ongoing = False
            # clear xyo if switch to another obstacle
            self.xyova.clear()
            self.plot_obstacle_state_profile()

        # if set to "None": clear QLineEdits
        else:
            self.clear_obstacle_fields()
            self.obstacle_toolbox_ui.obstacle_state_variable.clear()
            self.obstacle_toolbox_ui.figure.clear()
            self.obstacle_toolbox_ui.canvas.draw()

    def clear_obstacle_fields(self):
        """
        clears the obstacle QLineEdits
        """
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            self.obstacle_toolbox_ui.obstacle_radius.setText("")

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            self.obstacle_toolbox_ui.obstacle_width.setText("")
            self.obstacle_toolbox_ui.obstacle_length.setText("")
            self.obstacle_toolbox_ui.obstacle_orientation.setText("")

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            for i in range(self.obstacle_toolbox_ui.amount_vertices):
                self.obstacle_toolbox_ui.vertices_x[i].setText("")
                self.obstacle_toolbox_ui.vertices_y[i].setText("")
        if (self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Static" and
        self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Polygon"):
            self.obstacle_toolbox_ui.obstacle_x_Position.setText("")
            self.obstacle_toolbox_ui.obstacle_y_Position.setText("")

    def start_sumo_simulation(self):
        num_time_steps = self.obstacle_toolbox_ui.sumo_simulation_length.value()
        self.sumo_simulation.set_simulation_length(num_time_steps)
        self.sumo_simulation.simulate()
        self.callback(self.sumo_simulation.simulated_scenario.value)

    def remove_obstacle(self):
        """
        Removes the selected obstacle from the scenario.
        """
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:
            try:
                selected_obstacle = self.get_current_obstacle()
                self.current_scenario.remove_obstacle(selected_obstacle)
                self.callback(self.current_scenario)
                self.amount_obstacles -=1
            except Exception as e:
                self.text_browser.append("Error when removing obstacle")

    def draw_plot(self, time, profile, xmin: float = None,
                  xmax: float = None, ymin: float = None, ymax: float = None):
        """
        draws the state plot in the obstacle toolbox
        :param time: time steps
        :param profile: the profile to be drawn, eg orientation
        :param xmin: x lower bound to be drawn
        :param xmax: x upper bound to be drawn
        :param ymin: y lower bound to be drawn
        :param: ymax: y upper bound to be drawn
        """
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        # clear previous profile
        self.obstacle_toolbox_ui.figure.clear()
        # create an axis
        ax = self.obstacle_toolbox_ui.figure.add_subplot(111)
        
        # plot data
        ax.plot(time, profile, '.-', markersize=4)
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.1f}'))
        ax.set_xlabel("time [s]")
        ax.set_ylabel(self.resolve_y_label(state_variable_name))
        self.obstacle_toolbox_ui.figure.tight_layout()

        # to get reasonable limits. If the difference is very small: it will be difficult to make changes
        ax.set_ylim([min(profile)-0.5, max(profile)+0.5])
        # if zoomed in the new plot should be drawn with previous x and y limits
        # (so it doesnt zoom out on mouse event if zoomed in)
        if (self.xmin and self.xmax and self.ymin and self.ymax):
            ax.set_xlim([self.xmin, self.xmax])
            ax.set_ylim([self.ymin, self.ymax])
        # refresh canvas
        self.obstacle_toolbox_ui.canvas.draw()
        ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        ax.callbacks.connect('ylim_changed', self.on_ylim_change)
