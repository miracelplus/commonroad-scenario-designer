# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(990, 807)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 956, 1182))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName("gridLayout_2")
        
        self.label_9 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_9.setObjectName("label_9")
        self.gridLayout_2.addWidget(self.label_9, 27, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 15, 0, 1, 1)
        self.label_10 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)
        self.le_ego_ids = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.le_ego_ids.setText("")
        self.le_ego_ids.setObjectName("le_ego_ids")
        self.gridLayout_2.addWidget(self.le_ego_ids, 13, 2, 1, 1)
        self.sb_ego_veh_width = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_ego_veh_width.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_ego_veh_width.setProperty("value", 2.0)
        self.sb_ego_veh_width.setObjectName("doubleSpinBox_ego_veh_width")
        self.gridLayout_2.addWidget(self.sb_ego_veh_width, 10, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 12, 0, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_19.setObjectName("label_19")
        self.gridLayout_2.addWidget(self.label_19, 18, 0, 1, 1)
        self.sb_protection_margin = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_protection_margin.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_protection_margin.setMaximum(9999999.0)
        self.sb_protection_margin.setProperty("value", 2.0)
        self.sb_protection_margin.setObjectName("doubleSpinBox_protection_margin")
        self.gridLayout_2.addWidget(self.sb_protection_margin, 18, 2, 1, 1)
        self.sb_departure_time_ego = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_departure_time_ego.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_departure_time_ego.setMaximum(99999)
        self.sb_departure_time_ego.setProperty("value", 3)
        self.sb_departure_time_ego.setObjectName("sb")
        self.gridLayout_2.addWidget(self.sb_departure_time_ego, 15, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 11, 0, 1, 1)
        self.sb_random_seed = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_random_seed.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_random_seed.setMaximum(99999999)
        self.sb_random_seed.setProperty("value", 1234)
        self.sb_random_seed.setObjectName("spinBox_random_seed")
        self.gridLayout_2.addWidget(self.sb_random_seed, 28, 2, 1, 1)
        self.label_43 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_43.setObjectName("label_43")
        self.gridLayout_2.addWidget(self.label_43, 26, 0, 1, 1)
        self.label_25 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_25.setObjectName("label_25")
        self.gridLayout_2.addWidget(self.label_25, 33, 0, 1, 1)
        self.sb_lane_change_tol = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_lane_change_tol.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_lane_change_tol.setMaximum(99999999.0)
        self.sb_lane_change_tol.setObjectName("doubleSpinBox_lane_change_tol")
        self.gridLayout_2.addWidget(self.sb_lane_change_tol, 21, 2, 1, 1)
        self.label_compute_orientation = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_compute_orientation.setObjectName("label_compute_orientation")
        self.gridLayout_2.addWidget(self.label_compute_orientation, 3, 0, 1, 1)
        self.sb_lateral_resolution = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_lateral_resolution.setObjectName("spinBox_2")
        self.gridLayout_2.addWidget(self.sb_lateral_resolution, 2, 2, 1, 1)
        self.label_34 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_34.setObjectName("label_34")
        self.gridLayout_2.addWidget(self.label_34, 37, 0, 1, 1)
        self.label_29 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_29.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_29.setObjectName("label_29")
        self.gridLayout_2.addWidget(self.label_29, 24, 0, 1, 1)
        self.sb_vehicle_length_interval = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_vehicle_length_interval.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_vehicle_length_interval.setMaximum(99999999.0)
        self.sb_vehicle_length_interval.setProperty("value", 0.4)
        self.sb_vehicle_length_interval.setObjectName("doubleSpinBox_vehicle_length_interval")
        self.gridLayout_2.addWidget(self.sb_vehicle_length_interval, 30, 2, 1, 1)
        self.label_32 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_32.setObjectName("label_32")
        self.gridLayout_2.addWidget(self.label_32, 30, 0, 1, 1)
        self.sb_ego_start_time = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_ego_start_time.setMaximum(9999)
        self.sb_ego_start_time.setProperty("value", 10)
        self.sb_ego_start_time.setObjectName("spinBox_ego_start_time")
        self.gridLayout_2.addWidget(self.sb_ego_start_time, 14, 2, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_13.setObjectName("label_13")
        self.gridLayout_2.addWidget(self.label_13, 8, 0, 1, 1)
        self.label_28 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_28.setObjectName("label_28")
        self.gridLayout_2.addWidget(self.label_28, 23, 0, 1, 1)
        self.label_27 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_27.setFont(font)
        self.label_27.setObjectName("label_27")
        self.gridLayout_2.addWidget(self.label_27, 22, 0, 1, 1)
        self.label_18 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_18.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_18.setObjectName("label_18")
        self.gridLayout_2.addWidget(self.label_18, 17, 0, 1, 1)
        self.label_33 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_33.setObjectName("label_33")
        self.gridLayout_2.addWidget(self.label_33, 35, 0, 1, 1)
        self.label_24 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_24.setFont(font)
        self.label_24.setObjectName("label_24")
        self.gridLayout_2.addWidget(self.label_24, 32, 0, 1, 1)
        self.label_22 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_22.setObjectName("label_22")
        self.gridLayout_2.addWidget(self.label_22, 20, 0, 1, 1)
        self.sb_num_ego_vehicles = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_num_ego_vehicles.setMinimum(0)
        self.sb_num_ego_vehicles.setMaximum(999)
        self.sb_num_ego_vehicles.setProperty("value", 0)
        self.sb_num_ego_vehicles.setObjectName("sb_num_ego_vehicles")
        self.gridLayout_2.addWidget(self.sb_num_ego_vehicles, 12, 2, 1, 1)
        self.label_16 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_16.setObjectName("label_16")
        self.gridLayout_2.addWidget(self.label_16, 7, 0, 1, 1)
        self.label_21 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_21.setObjectName("label_21")
        self.gridLayout_2.addWidget(self.label_21, 19, 0, 1, 1)
        self.sb_ego_veh_length = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_ego_veh_length.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_ego_veh_length.setProperty("value", 5.0)
        self.sb_ego_veh_length.setObjectName("doubleSpinBox_ego_veh_length")
        self.gridLayout_2.addWidget(self.sb_ego_veh_length, 11, 2, 1, 1)
        self.label_lateral_resolution = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_lateral_resolution.setObjectName("label_lateral_resolution")
        self.gridLayout_2.addWidget(self.label_lateral_resolution, 2, 0, 1, 1)
        self.label_23 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_23.setObjectName("label_23")
        self.gridLayout_2.addWidget(self.label_23, 21, 0, 1, 1)
        self.label_unrestricted_max_speed_default = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_unrestricted_max_speed_default.setObjectName("label_unrestricted_max_speed_default")
        self.gridLayout_2.addWidget(self.label_unrestricted_max_speed_default, 6, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 14, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.sb_overwrite_speed_limit = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_overwrite_speed_limit.setMinimumSize(QtCore.QSize(200, 0))
        self.sb_overwrite_speed_limit.setMaximum(99999)
        self.sb_overwrite_speed_limit.setProperty("value", 130)
        self.sb_overwrite_speed_limit.setObjectName("spinBox_overwrite_speed_limit")
        self.horizontalLayout.addWidget(self.sb_overwrite_speed_limit)
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.gridLayout_2.addLayout(self.horizontalLayout, 5, 2, 1, 1)
        self.sb_vehicle_width_interval = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_vehicle_width_interval.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_vehicle_width_interval.setMaximum(9999999.0)
        self.sb_vehicle_width_interval.setProperty("value", 0.2)
        self.sb_vehicle_width_interval.setObjectName("doubleSpinBox_vehicle_width_interval")
        self.gridLayout_2.addWidget(self.sb_vehicle_width_interval, 31, 2, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.sb_lanelet_check_time_window = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_lanelet_check_time_window.setMinimumSize(QtCore.QSize(200, 0))
        self.sb_lanelet_check_time_window.setMaximum(99999)
        self.sb_lanelet_check_time_window.setProperty("value", 2)
        self.sb_lanelet_check_time_window.setObjectName("spinBox_lanelet_check_time_window")
        self.horizontalLayout_5.addWidget(self.sb_lanelet_check_time_window)
        self.label_8 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_5.addWidget(self.label_8)
        self.gridLayout_2.addLayout(self.horizontalLayout_5, 17, 2, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.sb_unrestricted_max_speed_default = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_unrestricted_max_speed_default.setMinimumSize(QtCore.QSize(200, 0))
        self.sb_unrestricted_max_speed_default.setMaximum(99999)
        self.sb_unrestricted_max_speed_default.setProperty("value", 120)
        self.sb_unrestricted_max_speed_default.setObjectName("spinBox_unrestricted_max_speed_default")
        self.horizontalLayout_2.addWidget(self.sb_unrestricted_max_speed_default)
        self.label_11 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_2.addWidget(self.label_11)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 6, 2, 1, 1)
        self.le_departure_interval_vehicles = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.le_departure_interval_vehicles.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.le_departure_interval_vehicles.setObjectName("le_departure_interval_vehicles")
        self.gridLayout_2.addWidget(self.le_departure_interval_vehicles, 25, 2, 1, 1)
        self.label_30 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_30.setObjectName("label_30")
        self.gridLayout_2.addWidget(self.label_30, 25, 0, 1, 1)
        self.label_26 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_26.setObjectName("label_26")
        self.gridLayout_2.addWidget(self.label_26, 34, 0, 1, 1)
        self.sb_delta_steps = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_delta_steps.setSuffix("")
        self.sb_delta_steps.setPrefix("")
        self.sb_delta_steps.setMaximum(199)
        self.sb_delta_steps.setProperty("value", 2)
        self.sb_delta_steps.setObjectName("spinBox_delta_steps")
        self.gridLayout_2.addWidget(self.sb_delta_steps, 1, 2, 1, 1)
        self.label_41 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_41.setObjectName("label_41")
        self.gridLayout_2.addWidget(self.label_41, 31, 0, 1, 1)
        self.sb_n_vehicles_max = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_n_vehicles_max.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_n_vehicles_max.setMaximum(999999999)
        self.sb_n_vehicles_max.setProperty("value", 30)
        self.sb_n_vehicles_max.setObjectName("spinBox_n_vehicles_max")
        self.gridLayout_2.addWidget(self.sb_n_vehicles_max, 26, 2, 1, 1)
        self.label_delta_steps = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_delta_steps.setObjectName("label_delta_steps")
        self.gridLayout_2.addWidget(self.label_delta_steps, 1, 0, 1, 1)
        self.label_31 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setFamily("Ubuntu")
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.label_31.setFont(font)
        self.label_31.setObjectName("label_31")
        self.gridLayout_2.addWidget(self.label_31, 29, 0, 1, 1)
        self.sb_consistency_window = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_consistency_window.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_consistency_window.setMaximum(99999999)
        self.sb_consistency_window.setProperty("value", 4)
        self.sb_consistency_window.setObjectName("spinBox_consistency_window")
        self.gridLayout_2.addWidget(self.sb_consistency_window, 19, 2, 1, 1)
        self.chk_lane_change_sync = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_lane_change_sync.setText("")
        self.chk_lane_change_sync.setObjectName("chk_lane_change_sync")
        self.gridLayout_2.addWidget(self.chk_lane_change_sync, 20, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 9, 0, 1, 1)
        self.sb_max_veh_per_km = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_max_veh_per_km.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_max_veh_per_km.setMaximum(9999999)
        self.sb_max_veh_per_km.setProperty("value", 70)
        self.sb_max_veh_per_km.setObjectName("spinBox_max_veh_per_km")
        self.gridLayout_2.addWidget(self.sb_max_veh_per_km, 27, 2, 1, 1)
        self.sb_veh_per_second = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_veh_per_second.setMaximum(9999999)
        self.sb_veh_per_second.setProperty("value", 50)
        self.sb_veh_per_second.setObjectName("spinBox_veh_per_second")
        self.gridLayout_2.addWidget(self.sb_veh_per_second, 24, 2, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.sb_unrestricted_speed_limit_default = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_unrestricted_speed_limit_default.setMinimumSize(QtCore.QSize(200, 0))
        self.sb_unrestricted_speed_limit_default.setMaximum(99999)
        self.sb_unrestricted_speed_limit_default.setProperty("value", 130)
        self.sb_unrestricted_speed_limit_default.setObjectName("spinBox_unrestricted_speed_limit_default")
        self.horizontalLayout_4.addWidget(self.sb_unrestricted_speed_limit_default)
        self.label_14 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_4.addWidget(self.label_14)
        self.gridLayout_2.addLayout(self.horizontalLayout_4, 8, 2, 1, 1)
        self.label_17 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_17.setFont(font)
        self.label_17.setObjectName("label_17")
        self.gridLayout_2.addWidget(self.label_17, 16, 0, 1, 1)
        self.sb_fringe_factor = QtWidgets.QSpinBox(self.scrollAreaWidgetContents)
        self.sb_fringe_factor.setMaximum(1000000009)
        self.sb_fringe_factor.setProperty("value", 1000000000)
        self.sb_fringe_factor.setObjectName("spinBox_fringe_factor")
        self.gridLayout_2.addWidget(self.sb_fringe_factor, 23, 2, 1, 1)
        self.chk_compute_orientation = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_compute_orientation.setText("")
        self.chk_compute_orientation.setObjectName("chk_compute_orientation")
        self.gridLayout_2.addWidget(self.chk_compute_orientation, 3, 2, 1, 1)
        self.label_20 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_20.setObjectName("label_20")
        self.gridLayout_2.addWidget(self.label_20, 13, 0, 1, 1)
        self.label_15 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_15.setObjectName("label_15")
        self.gridLayout_2.addWidget(self.label_15, 28, 0, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_6.setObjectName("label_6")
        self.gridLayout_2.addWidget(self.label_6, 10, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.sb_wait_pos_internal_junctions = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_wait_pos_internal_junctions.setMinimumSize(QtCore.QSize(250, 0))
        self.sb_wait_pos_internal_junctions.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_wait_pos_internal_junctions.setMinimum(-10000.0)
        self.sb_wait_pos_internal_junctions.setMaximum(1000.0)
        self.sb_wait_pos_internal_junctions.setProperty("value", -4.0)
        self.sb_wait_pos_internal_junctions.setObjectName("sb_wait_pos_internal_junctions")
        self.horizontalLayout_3.addWidget(self.sb_wait_pos_internal_junctions)
        self.label_12 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_3.addWidget(self.label_12)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 7, 2, 1, 1)
        self.label_overwrite_speed_limit = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_overwrite_speed_limit.setObjectName("label_overwrite_speed_limit")
        self.gridLayout_2.addWidget(self.label_overwrite_speed_limit, 5, 0, 1, 1)
        self.label_35 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_35.setObjectName("label_35")
        self.gridLayout_2.addWidget(self.label_35, 36, 0, 1, 1)
        self.sb_passenger = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_passenger.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_passenger.setProperty("value", 4.0)
        self.sb_passenger.setObjectName("doubleSpinBox_passenger")
        self.gridLayout_2.addWidget(self.sb_passenger, 33, 2, 1, 1)
        self.sb_truck = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_truck.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_truck.setProperty("value", 0.8)
        self.sb_truck.setObjectName("doubleSpinBox_truck")
        self.gridLayout_2.addWidget(self.sb_truck, 34, 2, 1, 1)
        self.sb_bus = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_bus.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_bus.setProperty("value", 0.3)
        self.sb_bus.setObjectName("doubleSpinBox_bus")
        self.gridLayout_2.addWidget(self.sb_bus, 35, 2, 1, 1)
        self.sb_bicycle = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_bicycle.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_bicycle.setProperty("value", 0.2)
        self.sb_bicycle.setObjectName("doubleSpinBox_bicycle")
        self.gridLayout_2.addWidget(self.sb_bicycle, 36, 2, 1, 1)
        self.sb_pedestrian = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.sb_pedestrian.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.sb_pedestrian.setObjectName("doubleSpinBox_pedestrian")
        self.gridLayout_2.addWidget(self.sb_pedestrian, 37, 2, 1, 1)
        
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.botton_restore_defaults = QtWidgets.QPushButton(self.frame)
        self.botton_restore_defaults.setObjectName("botton_restore_defaults")
        self.gridLayout_3.addWidget(self.botton_restore_defaults, 0, 0, 1, 1)
        self.botton_close = QtWidgets.QPushButton(self.frame)
        self.botton_close.setObjectName("botton_close")
        self.gridLayout_3.addWidget(self.botton_close, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 990, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SUMO Settings"))
        self.label_compute_orientation.setText(_translate("MainWindow", "compute_orientation"))
        self.label_unrestricted_max_speed_default.setToolTip(_translate("MainWindow", "[m/s] default max. speed for SUMO for unrestricted sped limits"))
        self.label_unrestricted_max_speed_default.setText(_translate("MainWindow", "unrestricted_max_speed_default"))
        self.label_lateral_resolution.setText(_translate("MainWindow", "lateral_resolution"))
        self.label_delta_steps.setToolTip(_translate("MainWindow", "number of sub-steps simulated in SUMO during every dt"))
        self.label_delta_steps.setText(_translate("MainWindow", "delta_steps"))
        self.label_overwrite_speed_limit.setText(_translate("MainWindow", "overwrite_speed_limit"))
        self.label.setText(_translate("MainWindow", " / 3.6  [m/s] "))
        self.label_9.setToolTip(_translate("MainWindow", "max. number of vehicles per km"))
        self.label_9.setText(_translate("MainWindow", "max_veh_per_km"))
        self.label_2.setText(_translate("MainWindow", "departure_time_ego"))
        self.label_10.setText(_translate("MainWindow", "Parameters for the SUMO settings"))
        self.label_4.setToolTip(_translate("MainWindow", "number of ego vehicles"))
        self.label_4.setText(_translate("MainWindow", "n_ego_vehicles"))
        self.label_19.setToolTip(_translate("MainWindow", "The absolute margin allowed between the planner position and ego position in SUMO"))
        self.label_19.setText(_translate("MainWindow", "protection_margin"))
        self.label_3.setText(_translate("MainWindow", "ego_veh_length"))
        self.label_43.setToolTip(_translate("MainWindow", "max. number of vehicles in route file"))
        self.label_43.setText(_translate("MainWindow", "n_vehicles_max"))
        self.label_25.setText(_translate("MainWindow", "Passenger"))
        self.label_34.setText(_translate("MainWindow", "Pedestrian"))
        self.label_29.setToolTip(_translate("MainWindow", "number of vehicle departures per second"))
        self.label_29.setText(_translate("MainWindow", "veh_per_second"))
        self.label_32.setText(_translate("MainWindow", "vehicle_length_interval"))
        self.label_13.setToolTip(_translate("MainWindow", "[m/s] default speed limit when no speed_limit is given"))
        self.label_13.setText(_translate("MainWindow", "unrestricted_speed_limit_default"))
        self.label_28.setText(_translate("MainWindow", "fringe_factor"))
        self.label_27.setText(_translate("MainWindow", "Parameters for traffic generation"))
        self.label_18.setToolTip(_translate("MainWindow", "Time window to detect the lanelet change in seconds"))
        self.label_18.setText(_translate("MainWindow", "lanelet_check_time_window"))
        self.label_33.setText(_translate("MainWindow", "Bus"))
        self.label_24.setToolTip(_translate("MainWindow", "probability distribution of different vehicle classes. Do not need to sum up to 1."))
        self.label_24.setText(_translate("MainWindow", "Parameter of vehicle classes"))
        self.label_22.setToolTip(_translate("MainWindow", "Used to limit the sync mechanism only to move xy"))
        self.label_22.setText(_translate("MainWindow", "lane_change_sync"))
        self.label_16.setToolTip(_translate("MainWindow", "[m] shifted waiting position at junction (equivalent to SUMO\'s contPos parameter)"))
        self.label_16.setText(_translate("MainWindow", "wait_pos_internal_junctions"))
        self.label_21.setToolTip(_translate("MainWindow", "Variable can be used  to force the consistency to certain number of steps"))
        self.label_21.setText(_translate("MainWindow", "consistency_window"))
        self.label_23.setToolTip(_translate("MainWindow", "tolerance for detecting start of lane change"))
        self.label_23.setText(_translate("MainWindow", "lane_change_tol"))
        self.label_7.setText(_translate("MainWindow", "ego_start_time"))
        self.label_8.setText(_translate("MainWindow", " / dt"))
        self.label_11.setText(_translate("MainWindow", " / 3.6  [m/s] "))
        self.label_30.setToolTip(_translate("MainWindow", "Interval of departure times for vehicles"))
        self.label_30.setText(_translate("MainWindow", "departure_interval_vehicles"))
        self.label_26.setText(_translate("MainWindow", "Truck"))
        self.label_41.setText(_translate("MainWindow", "vehicle_width_interval"))
        self.label_31.setText(_translate("MainWindow", "other vehicles size bound:"))
        self.label_5.setText(_translate("MainWindow", "Parameters for ego vehicle"))
        self.label_14.setText(_translate("MainWindow", " / 3.6  [m/s] "))
        self.label_17.setText(_translate("MainWindow", "Ego vehicle sync parameters"))
        self.label_20.setToolTip(_translate("MainWindow", "if desired ids of ego_vehicle known, specify here"))
        self.label_20.setText(_translate("MainWindow", "ego_ids"))
        self.label_15.setText(_translate("MainWindow", "random_seed"))
        self.label_6.setText(_translate("MainWindow", "ego_veh_width"))
        self.label_12.setText(_translate("MainWindow", " [m] "))
        self.label_35.setText(_translate("MainWindow", "Bicycle"))
        self.le_departure_interval_vehicles.setText(_translate("MainWindow", "(0, 30)"))
        self.le_ego_ids.setToolTip(_translate("MainWindow", "List[int] = []"))
        self.botton_restore_defaults.setText(_translate("MainWindow", "Restore Defaults"))
        self.botton_close.setText(_translate("MainWindow", "Appy and close"))

