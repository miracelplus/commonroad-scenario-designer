import copy
from typing import List, Union, Set

import scipy.version
from PyQt5.QtWidgets import QSizePolicy
from PyQt5 import QtCore
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import interp1d
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.common.util import Interval
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.geometry.shape import Circle
from commonroad.scenario.obstacle import StaticObstacle, DynamicObstacle
from commonroad.scenario.lanelet import Lanelet, LaneletType
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import PosB

from .helper import _merge_dict, calculate_closest_vertices, calculate_euclidean_distance, angle_between
from .service_layer import update_draw_params_dynamic_only_based_on_zoom
from .service_layer import update_draw_params_based_on_zoom
from .service_layer import update_draw_params_based_on_scenario
from .service_layer import update_draw_params_dynamic_based_on_scenario
from .service_layer import resize_lanelet_network
from crdesigner.ui.gui.mwindow.service_layer import config


from ...service_layer.map_creator import MapCreator

ZOOM_FACTOR = 1.2


class DynamicCanvas(FigureCanvas):
    """
    This canvas provides zoom with the mouse wheel.
    """
    obstacle_color_array = []
    scenario = None
    control_key = False

    def __init__(self, parent=None, width=5, height=5, dpi=100, animated_viewer=None):

        self.animated_viewer = animated_viewer
        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)
        self.drawer.set_facecolor('None')
        self.drawer.set_edgecolor('None')
        self.rnd = MPRenderer(ax=self.ax)

        self._handles = {}
        self.initial_parameter_config_done = False  # This is used to only once set the parameter based on the scenario
        self.draw_params = None  # needed later - here for reference
        self.draw_params_dynamic_only = None  # needed later - here for reference
        # used for efficiently monitoring of we switched from detailed to undetailed params
        self.selected_l_ids = []
        self.selected_lanelets = []
        self.last_changed_sth = False
        self.latest_mouse_pos = None  # used to store the last mouse position where a lanelet was clicked
        self.motion_notify_event_cid = None  # store mpl function to (dis-)connect event

        self.preview_line_object = None  # preview line when splitting a lanelet
        self.split_index = None  # index at which to split in the array

        self.l_network = None

        self.draw_lanelet_first_point = None  # drawing mode
        self.draw_lanelet_first_point_object = None
        self.draw_lanelet_preview = None
        self.draw_append_lanelet_preview = None
        self.add_to_selected_preview = None
        self.add_to_selected = None

        self.draw_temporary_points = {}
        self.num_lanelets = 0

        super().__init__(self.drawer)

        self.parent = parent
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set focus on canvas to detect key press events
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()

        # any callbacks for interaction per mouse
        self.button_press_event_cid = self.mpl_connect('button_press_event', self.dynamic_canvas_click_callback)
        self.button_release_event_cid = self.mpl_connect('button_release_event', self.dynamic_canvas_release_callback)
        self.mpl_connect('scroll_event', self.zoom)

        # any callbacks for interaction per keyboard
        self.mpl_connect('key_press_event', self.dynamic_canvas_ctrl_press_callback)
        self.mpl_connect('key_release_event', self.dynamic_canvas_ctrl_release_callback)

        self.clear_axes()

    def clear_axes(self, keep_limits=False, clear_artists=False):
        if clear_artists:
            self.rnd.clear()

        if self.ax:
            limits = self.get_limits()
            self.ax.clear()
        else:
            limits = None
            self.ax = self.drawer.add_subplot(111)

        self.ax.set_aspect("equal", "datalim")
        self.ax.set_axis_off()
        self.draw_idle()
        if keep_limits and limits:
            self.update_plot(limits)

    def get_axes(self):
        return self.ax

    def get_limits(self) -> List[float]:
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()
        return [x_lim[0], x_lim[1], y_lim[0], y_lim[1]]

    def update_plot(self, limits: List[float] = None):
        if limits:
            self.ax.set(xlim=limits[0:2])
            self.ax.set(ylim=limits[2:4])
        self.draw_idle()

    def zoom(self, event):
        """
        Zoom in / out function in Dynamic Canvas by using mouse wheel.
        """
        if self.animated_viewer.original_lanelet_network is None:
            return  # if no scenario was loaded or no map was created yet

        center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()

        # enlarge / shrink limits
        if event.button == 'up':
            new_x_dim = x_dim / ZOOM_FACTOR
            new_y_dim = y_dim / ZOOM_FACTOR
        elif event.button == 'down':
            new_x_dim = x_dim * ZOOM_FACTOR
            new_y_dim = y_dim * ZOOM_FACTOR
        else:
            return

        # new center sensitive to mouse position of zoom event
        mouse_pos = (event.xdata, event.ydata)
        if mouse_pos[0] and mouse_pos[1]:
            new_center_diff_x = (center[0] - mouse_pos[0]) / 6
            new_center_diff_y = (center[1] - mouse_pos[1]) / 6
            if event.button == 'up':
                new_center_x = center[0] - new_center_diff_x
                new_center_y = center[1] - new_center_diff_y
            else:
                new_center_x = center[0] + new_center_diff_x
                new_center_y = center[1] + new_center_diff_y
            # new limits should include old limits if zooming out
            # old limits should include new limits if zooming in
            dim_diff_x = abs(new_x_dim - x_dim)
            dim_diff_y = abs(new_y_dim - y_dim)
            new_center_x = min(max(center[0] - dim_diff_x, new_center_x), center[0] + dim_diff_x)
            new_center_y = min(max(center[1] - dim_diff_y, new_center_y), center[1] + dim_diff_y)
        else:
            new_center_x = center[0]
            new_center_y = center[1]
        # update the parameters for drawing based on the zoom -> this is for performance,
        # not all details need to be rendered when you are zoomed out
        self.draw_params = update_draw_params_based_on_zoom(x=new_x_dim, y=new_y_dim)
        self.draw_params_dynamic_only = update_draw_params_dynamic_only_based_on_zoom(x=new_x_dim, y=new_y_dim)
        lanelet_network, resized_lanelet_network = resize_lanelet_network(
                original_lanelet_network=self.animated_viewer.original_lanelet_network, center_x=new_center_x,
                center_y=new_center_y, dim_x=x_dim, dim_y=y_dim)
        self.animated_viewer.current_scenario.replace_lanelet_network(copy.deepcopy(lanelet_network))
        self.update_plot([new_center_x - new_x_dim, new_center_x + new_x_dim, new_center_y - new_y_dim,
                          new_center_y + new_y_dim])
        if resized_lanelet_network or self.last_changed_sth:
            self.animated_viewer.update_plot()
        self.last_changed_sth = resized_lanelet_network
        # now also show any selected
        self._select_lanelet(True)

    def draw_scenario(self, scenario: Scenario, pps: PlanningProblemSet = None, draw_params=None, plot_limits=None,
                      draw_dynamic_only=False):
        """[summary]
        :param scenario: [description]
        :param pps: PlanningProblemSet of the scenario,defaults to None
        :type pps: PlanningProblemSet
        :type scenario: Scenario
        :param draw_params: [description], defaults to None
        :type draw_params: [type], optional
        :param plot_limits: [description], defaults to None
        :type plot_limits: [type], optional
        :param draw_dynamic_only: reuses static artists
        """
        # want to update immediatly if change gui settings
        self.draw_params = update_draw_params_based_on_scenario(lanelet_count=len(scenario.lanelet_network.lanelets),
                                                                traffic_sign_count=len(
                                                                        scenario.lanelet_network.traffic_signs))

        DynamicCanvas.scenario = scenario
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        # update the parameters based on the number of lanelets and traffic signs - but only once during starting
        if not self.initial_parameter_config_done:
            self.draw_params = update_draw_params_based_on_scenario(
                    lanelet_count=len(scenario.lanelet_network.lanelets),
                    traffic_sign_count=len(scenario.lanelet_network.traffic_signs))
            self.draw_params_dynamic_only = update_draw_params_dynamic_based_on_scenario(
                    lanelet_count=len(scenario.lanelet_network.lanelets),
                    traffic_sign_count=len(scenario.lanelet_network.traffic_signs))
            self.initial_parameter_config_done = True
        if draw_dynamic_only is True:
            self.rnd.remove_dynamic()  # self.rnd.ax.clear()  # self.ax.clear()
        else:
            self.ax.clear()
        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)
        self.rnd.plot_limits = plot_limits
        self.rnd.ax = self.ax
        if draw_dynamic_only is True:
            draw_params_merged = _merge_dict(self.draw_params_dynamic_only.copy(), draw_params)
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(scenario=scenario, draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=True)
        else:
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            if pps is not None:
                pps.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(scenario=scenario, draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=False)

        if not plot_limits:
            self.ax.set(xlim=xlim)
            self.ax.set(ylim=ylim)

        self.rnd.ax.set_facecolor(draw_params['colorscheme']['secondbackground'])

        if draw_params['colorscheme']['axis'] == 'Left/ Bottom':
            self.ax.spines['bottom'].set_color(draw_params['colorscheme']['color'])
            self.ax.spines['left'].set_color(draw_params['colorscheme']['color'])
            self.ax.spines['top'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.spines['right'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.tick_params(axis='x', colors=draw_params['colorscheme']['color'])
            self.ax.tick_params(axis='y', colors=draw_params['colorscheme']['color'])

        elif draw_params['colorscheme']['axis'] == 'None':
            self.ax.spines['bottom'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.spines['left'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.spines['top'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.spines['right'].set_color(draw_params['colorscheme']['secondbackground'])
            self.ax.tick_params(axis='x', colors=draw_params['colorscheme']['secondbackground'])
            self.ax.tick_params(axis='y', colors=draw_params['colorscheme']['secondbackground'])
        else:
            self.ax.spines['bottom'].set_color(draw_params['colorscheme']['color'])
            self.ax.spines['left'].set_color(draw_params['colorscheme']['color'])
            self.ax.spines['top'].set_color(draw_params['colorscheme']['color'])
            self.ax.spines['right'].set_color(draw_params['colorscheme']['color'])
            self.ax.tick_params(axis='x', colors=draw_params['colorscheme']['color'])
            self.ax.tick_params(axis='y', colors=draw_params['colorscheme']['color'])



    def update_obstacles(self, scenario: Scenario, draw_params=None, plot_limits=None):
        """
        Redraw only the dynamic obstacles. This gives a large performance boost, when playing an animation
        :param scenario: The scenario containing the dynamic obstacles
        :param draw_params: CommonRoad DrawParams for visualization
        :param plot_limits: Matplotlib plot limits
        """
        # redraw dynamic obstacles
        obstacles = scenario.obstacles_by_position_intervals([Interval(plot_limits[0], plot_limits[1]),
                                                              Interval(plot_limits[2], plot_limits[
                                                                  3])]) if plot_limits else scenario.obstacles

        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)

        self.rnd.ax = self.ax
        for obj in obstacles:
            obj.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.rnd.render(show=True)

    def dynamic_canvas_click_callback(self, mouse_clicked_event):
        """
        General callback for clicking in the dynamic canvas, two things are checked:
        1. If the lanelet network of the current network should be resized.
        2. When a lanelet was selected execute the logic behind it.
        b) Select lanelets by clicking on the canvas. Selects only one of the lanelets that contains the click
        position.
        This order is important - first the resizing and then the lanelet selection - otherwise the lanelets of the old
        map are selected and then not visualized.

        :params mouse_clicked_event:
        """
        # when the mouse is clicked we remember where this was -> use this for lanelet selection
        self.latest_mouse_pos = np.array([mouse_clicked_event.xdata, mouse_clicked_event.ydata])
        # update the map
        self._update_map()
        # now do the lanelet selection
        self._select_lanelet()

        # call callback_function with latest mouse position to check if a position button is pressed
        temp_point_updated = self.animated_viewer.callback_function(PosB(str(self.latest_mouse_pos[0]), str(self.latest_mouse_pos[1])), "", self.draw_temporary_points)
        if temp_point_updated:
            self.draw_temporary_point()


    def dynamic_canvas_release_callback(self, mouse_clicked_event):
        """
        When the mouse button is released update the map and also select lanelets (with old mouse pos).
        :params mouse_clicked_event:
        """
        # update the map
        self._update_map()
        # now do the lanelet selection
        self._select_lanelet(release=True)

    def dynamic_canvas_ctrl_press_callback(self, key_event):
        """
        Check whether control key is pressed
        """
        if key_event.key == "control":
            self.control_key = True

    def dynamic_canvas_ctrl_release_callback(self, key_event):
        if key_event.key == "control":
            self.control_key = False

    def _update_map(self):
        """
        Resized the map if necessary for performance improvement.
        """

        if self.initial_parameter_config_done:
            center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()
            resized_lanelet_network, resize_necessary = resize_lanelet_network(
                    original_lanelet_network=self.animated_viewer.original_lanelet_network, center_x=center[0],
                    center_y=center[1], dim_x=x_dim, dim_y=y_dim)
            if resize_necessary:
                self.animated_viewer.current_scenario.replace_lanelet_network(resized_lanelet_network)
                self.animated_viewer.update_plot()

    def _select_lanelet(self, release: bool = False, lane_ids: list = None):
        """
        Select a lanelet and display the details in the GUI.

        :param release Boolean indicating whether function is called by click release callback
        :param lane_ids List indicating to select specified lanelets
        """
        if self.animated_viewer.current_scenario is None:
            return
        # as long as no new lanelet is added after adding a temporary position, no lanelet can be selected (because calling update_plot removes all temporary lanelets)
        if len(self.animated_viewer.current_scenario.lanelet_network.lanelets) - self.num_lanelets != 0 or self.parent.road_network_toolbox.updated_lanelet:
            self.parent.road_network_toolbox.updated_lanelet = False
            self.draw_temporary_points = {}


        self.l_network = self.animated_viewer.current_scenario.lanelet_network
        if not lane_ids:
            # check if any mousepos was setted before
            if self.latest_mouse_pos is None:
                return
            click_shape = Circle(radius=0.01, center=self.latest_mouse_pos)

            selected_l_id = self.l_network.find_lanelet_by_shape(click_shape)

            if not self.control_key:
                self.selected_l_ids = []

            if selected_l_id not in self.selected_l_ids and selected_l_id:
                self.selected_l_ids.append(selected_l_id)
                self.selected_l_ids = sorted(self.selected_l_ids)
        else:
            self.selected_l_ids = lane_ids

        self.enable_lanelet_operations(len(self.selected_l_ids))
        self.selected_lanelets = [self.l_network.find_lanelet_by_id(lid[0]) for lid in self.selected_l_ids]
        selected_obstacles = [obs for obs in self.animated_viewer.current_scenario.obstacles if obs.occupancy_at_time(
                self.animated_viewer.time_step.value) is not None and obs.occupancy_at_time(
                self.animated_viewer.time_step.value).shape.contains_point(self.latest_mouse_pos)]
        if len(self.selected_lanelets) > 0 and len(selected_obstacles) == 0:
            self.animated_viewer.update_plot(sel_lanelets=self.selected_lanelets,
                                             time_step=self.animated_viewer.time_step.value)
        else:
            self.animated_viewer.update_plot(sel_lanelets=None, time_step=self.animated_viewer.time_step.value)

        if not release:
            if len(self.selected_lanelets) + len(selected_obstacles) > 1:
                output = "__Info__: More than one object can be selected! Lanelets: "
                if len(self.selected_lanelets) > 0:
                    for la in self.selected_lanelets:
                        output += str(la.lanelet_id) + ", "
                output = output[:len(output) - 1]
                if len(selected_obstacles) > 0:
                    output += ". Obstacles: "
                    for obs in selected_obstacles:
                        output += str(obs.obstacle_id) + ", "
                output = output[:len(output) - 1]
                output += "."
            else:
                output = ""

            if len(selected_obstacles) > 0:
                selection = " Obstacle with ID " + str(selected_obstacles[0].obstacle_id) + " is selected."
                self.animated_viewer.callback_function(selected_obstacles[0], output + selection)
            elif len(self.selected_lanelets) == 1:
                selection = " Lanelet with ID " + str(self.selected_lanelets[0].lanelet_id) + " is selected."
                self.animated_viewer.callback_function(self.selected_lanelets[0], output + selection)
        self.draw_temporary_point()

    def get_center_and_axes_values(self) -> ((float, float), float, float, (float, float), (float, float)):
        """
        Used to get the new dimensions of the current Dynamic Canvas and other meta-data about it.

        :returns :
        center := tuple (x,y) of center,
        x_dim := absolut size of x-axis,
        y_dim := absolut size of y-axis,
        xlim := tuple of x-axis limits (x_min, x_max),
        ylim := tuple of y-axis limits (y_min, y_max)
        """
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
        x_dim = (x_max - x_min) / 2
        y_dim = (y_max - y_min) / 2
        return center, x_dim, y_dim, (x_min, x_max), (y_min, y_max)

    def draw_obstacles(self, scenario: Scenario, draw_params: str = None):
        """
        draws the obstacles
        :param scenario: current scenario
        :param: draw_params: scenario draw params, Note: does not contain
            dynamic obstacle related parameters
        """
        for obj in scenario.obstacles:
            # this is for getting the index of where the object_id is located
            try:
                result = next(c for c in DynamicCanvas.obstacle_color_array if c[0] == obj.obstacle_id)
                obstacle_draw_params = result[1]
                draw_params_merged = _merge_dict(draw_params.copy(), obstacle_draw_params.copy())
            except Exception:
                draw_params_merged = draw_params

            obj.draw(renderer=self.rnd, draw_params=draw_params_merged)

    def set_static_obstacle_color(self, obstacle_id: int, color: str = None):
        """
        sets static_obstacle color
        :param obstacle_id: id of obstacle that is to be added/updated
        :param color: color of the obstacle, None if default color
        """
        if not color:
            color = "#d95558"
        draw_params = {"static_obstacle": {"occupancy": {
            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                      "circle": {"facecolor": color}}}}}
        DynamicCanvas.obstacle_color_array.append([obstacle_id, draw_params, color])

    def set_dynamic_obstacle_color(self, obstacle_id: int, color: str = None):
        """
        sets dynamic_obstacle color
        :param obstacle_id: id of obstacle that is to be added/updated
        :param color: color of the obstacle, None if default color
        """
        if not color:
            color = "#1d7eea"
        draw_params = {"dynamic_obstacle": {"vehicle_shape": {"occupancy": {
            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                      "circle": {"facecolor": color}}}}, 'show_label': config.DRAW_OBSTACLE_LABELS,
            'draw_icon': config.DRAW_OBSTACLE_ICONS, 'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
            'draw_signals': config.DRAW_OBSTACLE_SIGNALS}}
        DynamicCanvas.obstacle_color_array.append([obstacle_id, draw_params, color])

    def update_obstacle_trajectory_params(self):
        """
        updates obstacles' draw params when gui settings are changed
        """

        if DynamicCanvas.scenario is not None:
            for obj in DynamicCanvas.scenario.obstacles:
                try:  # check if obstacle is in obstacle_color_array
                    result = next(c for c in DynamicCanvas.obstacle_color_array if c[0] == obj.obstacle_id)
                    color = result[2]
                    if isinstance(obj, DynamicObstacle):
                        draw_params = {"dynamic_obstacle": {"vehicle_shape": {"occupancy": {
                            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                                      "circle": {"facecolor": color}}}}, 'show_label': config.DRAW_OBSTACLE_LABELS,
                            'draw_icon': config.DRAW_OBSTACLE_ICONS, 'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
                            'draw_signals': config.DRAW_OBSTACLE_SIGNALS}}
                    elif isinstance(obj, StaticObstacle):
                        draw_params = {"static_obstacle": {"occupancy": {
                            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                                      "circle": {"facecolor": color}}}}}

                    i = DynamicCanvas.obstacle_color_array.index(result)
                    DynamicCanvas.obstacle_color_array.pop(i)
                    DynamicCanvas.obstacle_color_array.append([obj.obstacle_id, draw_params, color])

                except Exception:
                    if isinstance(obj, DynamicObstacle):
                        color = "#1d7eea"
                        draw_params = {"dynamic_obstacle": {"vehicle_shape": {"occupancy": {
                            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                                      "circle": {"facecolor": color}}}}, 'show_label': config.DRAW_OBSTACLE_LABELS,
                            'draw_icon': config.DRAW_OBSTACLE_ICONS, 'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
                            'draw_signals': config.DRAW_OBSTACLE_SIGNALS}}
                    elif isinstance(obj, StaticObstacle):
                        color = "#d95558"
                        draw_params = {"static_obstacle": {"occupancy": {
                            "shape": {"polygon": {"facecolor": color}, "rectangle": {"facecolor": color},
                                      "circle": {"facecolor": color}}}}}
                    DynamicCanvas.obstacle_color_array.append([obj.obstacle_id, draw_params, color])

    def get_color(self, obstacle_id: int) -> Union[int, bool]:
        """
        :param obstacle_id: id of selected obstacle
        :return: color of current selected obstacle
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvas.obstacle_color_array.index(result)
            return DynamicCanvas.obstacle_color_array[i][2]
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            return False

    def remove_obstacle(self, obstacle_id: int):
        """
        removes obstacle from obstacle_color_array

        :param: id of obstacle to be removed
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvas.obstacle_color_array.index(result)
            DynamicCanvas.obstacle_color_array.pop(i)
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            pass

    def activate_split_lanelet(self, is_checked: bool):
        if is_checked:
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.motion_notify_event_cid = self.mpl_connect('motion_notify_event', self.draw_line)
            self.button_press_event_cid = self.mpl_connect("button_press_event", self.split_lane)
        else:
            if self.preview_line_object:
                self.preview_line_object.pop(0).remove()
                self.update_plot()
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_press_event_cid)
            self.button_release_event_cid = self.mpl_connect('button_release_event',
                                                             self.dynamic_canvas_release_callback)
            self.button_press_event_cid = self.mpl_connect('button_press_event', self.dynamic_canvas_click_callback)

    def draw_line(self, mouse_move_event):
        x = mouse_move_event.xdata
        y = mouse_move_event.ydata

        if x and y and self.selected_l_ids:
            mouse_pos = np.array([x, y])
            mouse_shape = Circle(radius=0.01, center=mouse_pos)
            hovered_lanes_ids = self.l_network.find_lanelet_by_shape(mouse_shape)

            # Do not draw as long as we do not hover the selected Lanelet
            if not hovered_lanes_ids or hovered_lanes_ids[0] != self.selected_l_ids[0][0]:
                self.remove_line()
                return
            selected_lane = self.l_network.find_lanelet_by_id(self.selected_l_ids[0][0])
            shortest_distance_index = calculate_closest_vertices([x, y], selected_lane.left_vertices)
            if self.split_index == shortest_distance_index:  # No need to redraw line if split index stays the same
                return
            self.remove_line()
            if shortest_distance_index == 0 or shortest_distance_index == len(selected_lane.left_vertices) - 1:
                # when we hover the first or last index we are not able to split
                return

            self.split_index = shortest_distance_index
            left_adj_lane = selected_lane
            while left_adj_lane.adj_left:
                left_adj_lane = self.l_network.find_lanelet_by_id(left_adj_lane.adj_left)

            right_adj_lane = selected_lane
            while right_adj_lane.adj_right:
                right_adj_lane = self.l_network.find_lanelet_by_id(right_adj_lane.adj_right)

            left_vertex = left_adj_lane.left_vertices[self.split_index]
            right_vertex = right_adj_lane.right_vertices[self.split_index]

            self.preview_line_object = self.ax.plot([left_vertex[0], right_vertex[0]],
                                                    [left_vertex[1], right_vertex[1]], linestyle='dashed', color="blue",
                                                    linewidth=5, zorder=21)
            self.update_plot()

        elif self.preview_line_object:
            self.remove_line()

    def remove_line(self):
        self.split_index = None
        if not self.preview_line_object:
            return
        self.preview_line_object.pop(0).remove()
        self.update_plot()

    def split_lane(self, mouse_click):
        if self.split_index:
            current_lanelet = self.l_network.find_lanelet_by_id(self.selected_l_ids[0][0])
            MapCreator.split_lanelet(current_lanelet, self.split_index, self.scenario, self.l_network)
            self.parent.road_network_toolbox.callback(self.scenario)
            self.reset_toolbar()

    def enable_lanelet_operations(self, number_of_selected_lanelets):
        """
        Enable or disable operations depending on the number of lanelets selected
        """
        self.parent.top_bar_wrapper.toolbar_wrapper.enable_toolbar(number_of_selected_lanelets)

    def reset_toolbar(self):
        self.parent.top_bar_wrapper.toolbar_wrapper.reset_toolbar()

    def add_adjacent(self, left_adj: bool, same_direction: bool = True):
        added_adjacent_lanelets = []
        for lanelet in self.selected_lanelets:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(left_adj, lanelet, self.scenario.generate_object_id(),
                                                                  same_direction, 3.0, lanelet.lanelet_type,
                                                                  lanelet.predecessor, lanelet.successor,
                                                                  traffic_signs=lanelet.traffic_signs,
                                                                  traffic_lights=lanelet.traffic_lights)
            if not adjacent_lanelet:
                output = f"Adjacent for Lanelet {lanelet.lanelet_id} already exists!"
                self.parent.crdesigner_console_wrapper.text_browser.append(output)
            else:
                added_adjacent_lanelets.append(adjacent_lanelet)
        self.scenario.add_objects(added_adjacent_lanelets)
        self.parent.road_network_toolbox.callback(self.scenario)

    def merge_lanelets(self):
        neighboured_lanelets = self.selected_lanelets.copy()
        last_merged_index = None
        while neighboured_lanelets:
            lanelet = neighboured_lanelets.pop()
            for n_lanelet in neighboured_lanelets:
                if n_lanelet.lanelet_id in lanelet.predecessor or n_lanelet.lanelet_id in lanelet.successor:
                    neighboured_lanelet = self.l_network.find_lanelet_by_id(n_lanelet.lanelet_id)
                    connected_lanelet = Lanelet.merge_lanelets(neighboured_lanelet, lanelet)
                    neighboured_lanelets.append(connected_lanelet)
                    for succ in connected_lanelet.successor:
                        self.l_network.find_lanelet_by_id(succ).add_predecessor(connected_lanelet.lanelet_id)
                    for pred in connected_lanelet.predecessor:
                        self.l_network.find_lanelet_by_id(pred).add_successor(connected_lanelet.lanelet_id)
                    self.scenario.add_objects(connected_lanelet)
                    neighboured_lanelets.remove(n_lanelet)
                    self.scenario.remove_lanelet(n_lanelet)
                    self.scenario.remove_lanelet(lanelet)
                    last_merged_index = connected_lanelet.lanelet_id
                    break
        if last_merged_index:
            self._select_lanelet(False, [[last_merged_index]])
        self.parent.road_network_toolbox.callback(self.scenario)

    def activate_drawing_mode(self, is_active):
        if is_active:
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.button_press_event_cid = self.mpl_connect('button_press_event', self.draw_lanelet)
            self.motion_notify_event_cid = self.mpl_connect('motion_notify_event', self.drawing_mode_preview_line)
        else:
            if self.draw_lanelet_preview:
                self.draw_lanelet_preview.pop(0).remove()
                self.draw_lanelet_first_point_object.pop(0).remove()
                self.draw_lanelet_first_point = None
                self.add_to_selected = None
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.button_release_event_cid = self.mpl_connect('button_release_event',
                                                             self.dynamic_canvas_release_callback)
            self.button_press_event_cid = self.mpl_connect('button_press_event', self.dynamic_canvas_click_callback)
            self.reset_toolbar()
            self.update_plot()

    def draw_lanelet(self, mouse_event):
        x = mouse_event.xdata
        y = mouse_event.ydata

        if mouse_event.button == MouseButton.RIGHT:
            self.activate_drawing_mode(False)
            return

        if not self.draw_lanelet_first_point:
            if self.add_to_selected_preview:
                append_point = self.add_to_selected_preview.center_vertices[-1]
                x = append_point[0]
                y = append_point[1]
                self.add_to_selected = self.add_to_selected_preview
            self.draw_lanelet_first_point_object = self.ax.plot(x, y, marker="x", color="blue", zorder=21)
            self.draw_lanelet_first_point = [x, y]
            self.update_plot()
        else:
            lanelet_type = {LaneletType(ty) for ty in ["None"] if ty != "None"}
            draw_lanelet_second_point = [x, y]
            lanelet_length = calculate_euclidean_distance(self.draw_lanelet_first_point, draw_lanelet_second_point)
            num_vertices = max([1, round(lanelet_length * 2)])
            try:
                if self.add_to_selected:
                    created_lanelet = MapCreator.create_straight(3.0, lanelet_length, num_vertices, 10000, lanelet_type)
                else:
                    created_lanelet = MapCreator.create_straight(3.0, lanelet_length, num_vertices,
                                                                 self.scenario.generate_object_id(), lanelet_type)
            except AssertionError:
                output = "Length of Lanelet must be at least 1"
                self.parent.crdesigner_console_wrapper.text_browser.append(output)
                return

            drawn_vector = [draw_lanelet_second_point[0] - self.draw_lanelet_first_point[0],
                            draw_lanelet_second_point[1] - self.draw_lanelet_first_point[1]]
            horizontal_vector = [1, 0]
            angle = angle_between(drawn_vector, horizontal_vector)

            created_lanelet.translate_rotate(np.array([0, 0]), angle)
            if self.add_to_selected:
                created_lanelet.translate_rotate(np.array(draw_lanelet_second_point), 0)
                created_lanelet = MapCreator.connect_lanelets(self.add_to_selected, created_lanelet,
                                                              self.scenario.generate_object_id())
                created_lanelet.successor = []
                self.add_to_selected.add_successor(created_lanelet.lanelet_id)
            else:
                created_lanelet.translate_rotate(np.array(self.draw_lanelet_first_point), 0)
            self.add_to_selected = created_lanelet
            self.scenario.add_objects([created_lanelet])
            self.parent.road_network_toolbox.callback(self.scenario)
            self.parent.road_network_toolbox.last_added_lanelet_id = created_lanelet.lanelet_id

            self.draw_lanelet_first_point = draw_lanelet_second_point
            self.draw_lanelet_first_point_object.pop(0).remove()
            self.draw_lanelet_first_point_object = self.ax.plot(x, y, marker="x", color="blue", zorder=21)

            self.update_plot()

    def drawing_mode_preview_line(self, mouse_move_event):
        x = mouse_move_event.xdata
        y = mouse_move_event.ydata
        if not x:
            return
        if self.draw_append_lanelet_preview:
            self.draw_append_lanelet_preview.pop(0).remove()
            self.draw_append_lanelet_preview = None
            self.add_to_selected_preview = None
            self.update_plot()
        if self.draw_lanelet_preview or (self.draw_lanelet_preview and not x and not y):
            self.draw_lanelet_preview.pop(0).remove()
        if self.draw_lanelet_first_point:
            self.draw_lanelet_preview = self.ax.plot([x, self.draw_lanelet_first_point[0]],
                                                     [y, self.draw_lanelet_first_point[1]], color="blue", zorder=21)
        else:
            self.latest_mouse_pos = np.array([x, y])
            click_shape = Circle(radius=0.01, center=self.latest_mouse_pos)
            selected_l_ids = self.l_network.find_lanelet_by_shape(click_shape)
            if not selected_l_ids:
                return
            selected_l_id = selected_l_ids[0]
            selected_l = self.l_network.find_lanelet_by_id(selected_l_id)
            if not selected_l.successor:
                center_distance = calculate_euclidean_distance(self.latest_mouse_pos, selected_l.center_vertices[-1])
                left_distance = calculate_euclidean_distance(self.latest_mouse_pos, selected_l.left_vertices[-1])
                right_distance = calculate_euclidean_distance(self.latest_mouse_pos, selected_l.right_vertices[-1])
                if center_distance <= 1 or left_distance <= 1 or right_distance <= 1:
                    left_v = selected_l.left_vertices[-1]
                    right_v = selected_l.right_vertices[-1]
                    self.add_to_selected_preview = selected_l
                    self.draw_append_lanelet_preview = self.ax.plot([left_v[0], right_v[0]], [left_v[1], right_v[1]],
                                                             linewidth=3, color="blue", zorder=21)
        self.update_plot()

    def draw_temporary_point(self):
        if self.animated_viewer.current_scenario is None:
            return
        for key in self.draw_temporary_points:
            (x, y) = self.draw_temporary_points[key]
            self.ax.plot(x, y, marker="x", color="blue", zorder=21)
        self.update_plot()
        self.num_lanelets = len(self.animated_viewer.current_scenario.lanelet_network.lanelets)

