import os
from copy import deepcopy
from typing import Dict, List, Iterable, Set
from xml.dom import minidom
from xml.etree import ElementTree as et

import numpy as np
from commonroad.geometry.shape import Polygon
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.lanelet import LaneletNetwork
from crmapconverter.sumo_map.sumolib_net import Crossing
from shapely.geometry import LineString
from shapely.ops import unary_union
from crmapconverter.sumo_map.sumolib_net.edge import Edge
from matplotlib.pyplot import plot as plt

from .config import EGO_ID_START, SumoConfig


def get_scenario_name_from_crfile(filepath: str) -> str:
    """
    Returns the scenario name specified in the cr file.

    :param filepath: the path of the cr file

    """
    scenario_name: str = (os.path.splitext(
        os.path.basename(filepath))[0]).split('.')[0]
    return scenario_name


def get_scenario_name_from_netfile(filepath: str) -> str:
    """
    Returns the scenario name specified in the net file.

    :param filepath: the path of the net file

    """
    scenario_name: str = (os.path.splitext(
        os.path.basename(filepath))[0]).split('.')[0]
    return scenario_name


def get_boundary_from_netfile(filepath: str) -> list:
    """
    Get the boundary of the netfile.
    :param filepath:
    :return: boundary as a list containing min_x, max_x, min_y, max_y coordinates
    """
    tree = et.parse(filepath)
    root = tree.getroot()
    location = root.find("location")
    boundary_list = location.attrib['origBoundary']  # origBoundary
    min_x, min_y, max_x, max_y = boundary_list.split(',')
    boundary = [float(min_x), float(max_x), float(min_y), float(max_y)]
    return boundary


def get_total_lane_length_from_netfile(filepath: str) -> float:
    """
    Compute the total length of all lanes in the net file.
    :param filepath:
    :return: float value of the total lane length
    """
    tree = et.parse(filepath)
    root = tree.getroot()
    total_lane_length = 0
    for lane in root.iter('lane'):
        total_lane_length += float(lane.get('length'))
    return total_lane_length


def add_params_in_rou_file(
    rou_file: str,
    driving_params: dict = SumoConfig.driving_params) -> None:
    """
    Add parameters for the vType setting in the route file generated by SUMO. Parameters are sampled from uniform distribution.
    :param rou_file: the route file to be modified
    :param driving_params: dictionary with driving parameter as keys and interval of sampling as values
    :return:
    """
    tree = et.parse(rou_file)
    root = tree.getroot()
    vType = root.find("vType")
    if vType is not None:
        for key, value_interval in driving_params.items():
            random_value = np.random.uniform(value_interval.start,
                                             value_interval.end, 1)[0]
            vType.set(key, str("{0:.2f}".format(random_value)))
    tree.write(rou_file)


def write_ego_ids_to_rou_file(rou_file: str, ego_ids: List[int]) -> None:
    """
    Writes ids of ego vehicles to the route file.

    :param rou_file: the route file
    :param ego_ids: a list of ego vehicle ids

    """
    tree = et.parse(rou_file)
    vehicles = tree.findall('vehicle')
    ego_str = {}
    for ego_id in ego_ids:
        ego_str.update({str(ego_id): EGO_ID_START + str(ego_id)})

    for veh in vehicles:
        if veh.attrib['id'] in ego_str:
            veh.attrib['id'] = ego_str[veh.attrib['id']]

    for elem in tree.iter():
        if (elem.text):
            elem.text = elem.text.strip()
        if (elem.tail):
            elem.tail = elem.tail.strip()
    rough_string = et.tostring(tree.getroot(), encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    text = reparsed.toprettyxml(indent="\t", newl="\n")
    file = open(rou_file, "w")
    file.write(text)


def compute_max_curvature_from_polyline(polyline: np.ndarray) -> float:
    """
    Computes the curvature of a given polyline
    :param polyline: The polyline for the curvature computation
    :return: The pseudo maximum curvature of the polyline
    """
    assert isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(
        polyline[:, 0]
    ) >= 2, 'Polyline malformed for curvature computation p={}'.format(
        polyline)
    x_d = np.gradient(polyline[:, 0])
    x_dd = np.gradient(x_d)
    y_d = np.gradient(polyline[:, 1])
    y_dd = np.gradient(y_d)

    # compute curvature
    curvature = (x_d * y_dd - x_dd * y_d) / ((x_d ** 2 + y_d ** 2) ** (3. / 2.))

    # compute maximum curvature
    abs_curvature = [abs(ele) for ele in curvature]  # absolute value
    max_curvature = max(abs_curvature)

    # compute pseudo maximum -- mean of the two largest curvatures --> relax the constraint
    abs_curvature.remove(max_curvature)
    second_max_curvature = max(abs_curvature)
    max_curvature = (max_curvature + second_max_curvature) / 2

    return max_curvature


def _erode_lanelets(lanelet_network: LaneletNetwork,
                    radius: float = 0.4) -> LaneletNetwork:
    """Erode shape of lanelet by given radius."""
    lanelets_ero = []
    crop_meters = 0.3
    min_factor = 0.1
    for lanelet in lanelet_network.lanelets:
        lanelet_ero = deepcopy(lanelet)

        # shorten lanelet by radius
        if len(lanelet_ero._center_vertices) > 4:
            i_max = int(
                (np.floor(len(lanelet_ero._center_vertices) - 1) / 2)) - 1

            i_crop_0 = np.argmax(lanelet_ero.distance >= crop_meters)
            i_crop_1 = len(lanelet_ero.distance) - np.argmax(
                lanelet_ero.distance >= lanelet_ero.distance[-1] - crop_meters)
            i_crop_0 = min(i_crop_0, i_max)
            i_crop_1 = min(i_crop_1, i_max)

            lanelet_ero._left_vertices = lanelet_ero._left_vertices[
                                         i_crop_0:-i_crop_1]
            lanelet_ero._center_vertices = lanelet_ero._center_vertices[
                                           i_crop_0:-i_crop_1]
            lanelet_ero._right_vertices = lanelet_ero._right_vertices[
                                          i_crop_0:-i_crop_1]
        else:
            factor_0 = min(1, crop_meters / lanelet_ero.distance[1])
            lanelet_ero._left_vertices[0] = factor_0 * lanelet_ero._left_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._left_vertices[1]
            lanelet_ero._right_vertices[0] = factor_0 * lanelet_ero._right_vertices[0] \
                                             + (1 - factor_0) * lanelet_ero._right_vertices[1]
            lanelet_ero._center_vertices[0] = factor_0 * lanelet_ero._center_vertices[0] \
                                              + (1 - factor_0) * lanelet_ero._center_vertices[1]

            factor_0 = min(
                1, crop_meters /
                   (lanelet_ero.distance[-1] - lanelet_ero.distance[-2]))
            lanelet_ero._left_vertices[-1] = factor_0 * lanelet_ero._left_vertices[-2] \
                                             + (1 - factor_0) * lanelet_ero._left_vertices[-1]
            lanelet_ero._right_vertices[-1] = factor_0 * lanelet_ero._right_vertices[-2] \
                                              + (1 - factor_0) * lanelet_ero._right_vertices[-1]
            lanelet_ero._center_vertices[-1] = factor_0 * lanelet_ero._center_vertices[-2] \
                                               + (1 - factor_0) * lanelet_ero._center_vertices[-1]

        # compute eroded vector from center
        perp_vecs = (lanelet_ero.left_vertices -
                     lanelet_ero.right_vertices) * 0.5
        length = np.linalg.norm(perp_vecs, axis=1)
        factors = np.divide(radius, length)  # 0.5 * np.ones_like(length))
        factors = np.reshape(factors, newshape=[-1, 1])
        factors = 1 - np.maximum(
            factors,
            np.ones_like(factors) *
            min_factor)  # ensure minimum width of eroded lanelet
        perp_vec_ero = np.multiply(perp_vecs, factors)

        # recompute vertices
        lanelet_ero._left_vertices = lanelet_ero.center_vertices + perp_vec_ero
        lanelet_ero._right_vertices = lanelet_ero.center_vertices - perp_vec_ero
        if lanelet_ero._polygon is not None:
            lanelet_ero._polygon = Polygon(
                np.concatenate((lanelet_ero.right_vertices,
                                np.flip(lanelet_ero.left_vertices, 0))))
        lanelets_ero.append(lanelet_ero)

    return LaneletNetwork.create_from_lanelet_list(lanelets_ero)


def _find_intersecting_edges(
    edges_dict: Dict[int, List[int]],
    lanelet_network: LaneletNetwork) -> List[List[int]]:
    """

    :param lanelet_network:
    :return:
    """
    eroded_lanelet_network = _erode_lanelets(lanelet_network)

    # visualize eroded lanelets
    # plt.figure(figsize=(25, 25))
    # draw_object(eroded_lanelet_network.lanelets)
    # plt.axis('equal')
    # plt.autoscale()
    # plt.show()

    polygons_dict = {}
    edge_shapes_dict = {}
    for edge_id, lanelet_ids in edges_dict.items():
        edge_shape = []
        for lanelet_id in (lanelet_ids[0], lanelet_ids[-1]):
            if lanelet_id not in polygons_dict:
                polygon = eroded_lanelet_network.find_lanelet_by_id(
                    lanelet_id).convert_to_polygon()

                polygons_dict[lanelet_id] = polygon.shapely_object

                edge_shape.append(polygons_dict[lanelet_id])

        edge_shapes_dict[edge_id] = edge_shape

    intersecting_edges = []
    for edge_id, shape_list in edge_shapes_dict.items():
        for edge_id_other, shape_list_other in edge_shapes_dict.items():
            if edge_id == edge_id_other: continue
            edges_intersect = False
            for shape_0 in shape_list:
                if edges_intersect: break
                for shape_1 in shape_list_other:
                    # shapely
                    if shape_0.intersection(shape_1).area > 0.0:
                        edges_intersect = True
                        intersecting_edges.append([edge_id, edge_id_other])
                        break

    return intersecting_edges


def remove_unreferenced_traffic_lights(
    lanelet_network: LaneletNetwork) -> LaneletNetwork:
    referenced_traffic_lights = set()
    for lanelet in lanelet_network.lanelets:
        referenced_traffic_lights |= lanelet.traffic_lights

    lanelet_network._traffic_lights = {
        traffic_light.traffic_light_id: traffic_light
        for traffic_light in lanelet_network.traffic_lights
        if traffic_light.traffic_light_id in referenced_traffic_lights
    }
    return lanelet_network


def max_lanelet_network_id(lanelet_network: LaneletNetwork) -> int:
    max_lanelet = np.max([l.lanelet_id for l in lanelet_network.lanelets
                          ]) if lanelet_network.lanelets else 0
    max_intersection = np.max([
        i.intersection_id for i in lanelet_network.intersections
    ]) if lanelet_network.intersections else 0
    max_traffic_light = np.max([
        t.traffic_light_id for t in lanelet_network.traffic_lights
    ]) if lanelet_network.traffic_lights else 0
    max_traffic_sign = np.max([
        t.traffic_sign_id for t in lanelet_network.traffic_signs
    ]) if lanelet_network.traffic_signs else 0
    return np.max(
        [max_lanelet, max_intersection, max_traffic_light, max_traffic_sign])


def vector_angle(v1: np.array, v2: np.array) -> float:
    """Computes the angle between two vectors, in radians

    Args:
        v1 (np.array): [description]
        v2 (np.array): [description]

    Returns:
        float: [description]
    """
    v1 /= np.linalg.norm(v1)
    v2 /= np.linalg.norm(v2)
    return np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))


def min_cluster(items, condition, comp):
    """clusters the items according to the comparator() of size minimally condition()

    Args:
        items ([type]): [description]
        condition ([type]): [description]
        comp ([type]): [description]

    Returns:
        [type]: List of clusters
    """
    clusters = [{items.pop()}]
    while items:
        item = items.pop()
        min_idx = 0
        min_val = float("inf")
        for idx, cluster in enumerate(clusters):
            current = np.min([comp(item, e) for e in cluster])
            if current < min_val:
                min_idx = idx
                min_val = current
        if condition(min_val):
            clusters[min_idx].add(item)
        else:
            clusters.append({item})
    return clusters


def merge_crossings(crossings: List[Crossing]) -> List[Crossing]:
    """Merges crossings whose share the same point in their
    shape at either the beginning or end.

    Args:
        crossings (List[Crossing]): list of crossings to merge

    Returns:
        List[Crossing]: merged crossings
    """
    old = set(crossings)
    new = old

    def eq(a, b):
        return all(np.isclose(a, b))

    do = True
    while do or len(new) < len(old):
        do = False
        old = new
        for current in old:
            match = next(
                (other for other in old
                 if (eq(current.shape[-1], other.shape[0]) or eq(
                    other.shape[-1], current.shape[0])) and other != current),
                None)
            if not match: continue

            if eq(current.shape[-1], match.shape[0]):
                match.shape = np.concatenate((current.shape[:-1], match.shape),
                                             axis=0)
            elif eq(match.shape[-1], current.shape[0]):
                match.shape = np.concatenate((match.shape[:-1], current.shape),
                                             axis=0)
            new = old - {current}
            break
    return list(new)


def intersect_lanelets_line(lanelets: Iterable[Lanelet],
                            line: np.ndarray,
                            push_back_factor=0.25,
                            visualize=False) -> np.ndarray:
    """
    Intersects a list of lanelets with a line specified by a numpy array.
    Optionally the ends of the intersection can be pushed back along the
    direction of the intersection.
    :param lanelets: List of Lanelets
    :type lanelets:
    :param line: line as numpy array
    :type line:
    :param push_back_factor: units to push back the ends of the intersection
    :type push_back_factor:
    :return: intersection
    :rtype:
    """
    # intersect line with convex hull of lanelets
    convex_hull = unary_union([
        lanelet.convert_to_polygon().shapely_object for lanelet in lanelets
    ]).convex_hull
    shapely_line = LineString(line)
    intersect = convex_hull.intersection(shapely_line)
    res = np.array(intersect)

    # push back the line end points to give waiting space in crossing
    line_direction = res[-1] - res[0]
    line_direction /= np.linalg.norm(line_direction)
    assert push_back_factor >= 0, "push_back_factor has to be >= 0"
    res[0] -= line_direction * push_back_factor
    res[-1] += line_direction * push_back_factor

    if visualize:
        plt.figure(figsize=(25, 25))
        plt.axis('equal')
        plt.plot(*convex_hull.exterior.xy)
        plt.plot(*shapely_line.xy)
        plt.plot(*res.xy)
        plt.autoscale()
        plt.show()
    return res


def edge_centroid(e: Edge) -> np.ndarray:
    """Computes the centroid of an edge based on the vertices of it's lanes"""
    pts = np.array([v for lane in e.getLanes() for v in lane._shape])
    return np.sum(pts, axis=0) / pts.shape[0]
