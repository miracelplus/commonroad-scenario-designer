import copy
from typing import List, Tuple

from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.border import (
    Border,
)
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane import (
    ParametricLane,
    ParametricLaneBorderGroup,
)
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.plane_group import (
    ParametricLaneGroup,
)
from crdesigner.map_conversion.opendrive.opendrive_conversion.utils import (
    encode_mark_lane_width_id,
    encode_road_section_lane_width_id,
)
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import (
    Lane,
    LaneSection,
    LaneWidth,
)
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import (
    PlanView,
)


class OpenDriveConverter:
    """Class for static methods to convert lane_sections to parametric_lanes."""

    @staticmethod
    def create_reference_border(plan_view: PlanView, lane_offsets: List[float]) -> Border:
        """Create the most inner border from a PlanView.
        This border is used as a reference for other
        borders which rely on the PlanView.

        :param plan_view: PlanView object from OpenDrive which specifies the geometry
            of the reference path.
        :param lane_offsets: Object which contains information about width offset of reference
            path the plain_view path.
         :return: The reference border on which all other borders in this lane section are based upon.
        """

        reference_border = Border()

        # Set reference to plan view
        reference_border.reference = plan_view

        # Lane offsets will be coeffs
        # this has to be done if the reference path has the laneoffset attribute
        # and thus is different to the geometry described in the plan_view
        # openDRIVE lets multiple laneOffsets start at the same position
        # but only the last one counts -> delete all previous ones
        if any(lane_offsets):
            for lane_offset in lane_offsets:
                if lane_offset.start_pos in reference_border.width_coefficient_offsets:
                    # offset is already there, delete previous entries
                    idx = reference_border.width_coefficient_offsets.index(lane_offset.start_pos)
                    del reference_border.width_coefficient_offsets[idx]
                    del reference_border.width_coefficients[idx]
                reference_border.width_coefficient_offsets.append(lane_offset.start_pos)
                reference_border.width_coefficients.append(lane_offset.polynomial_coefficients)
        else:
            reference_border.width_coefficient_offsets.append(0.0)
            reference_border.width_coefficients.append([0.0])

        return reference_border

    @staticmethod
    def lane_section_to_parametric_lanes(
        lane_section: LaneSection, reference_border: Border
    ) -> List[ParametricLaneGroup]:
        """Convert a whole lane section into a list of ParametricLane objects.

        :param lane_section: LaneSection from which to create the list of ParametricLane Objects
        :param reference_border: The reference border of the lane section, created from create_reference_border()
        :return: The converted ParametricLane objects.
        """

        plane_groups = []

        for side in ["right", "left"]:
            # lanes loaded by opendriveparser are aleady sorted by id
            # coeff_factor decides if border is left or right of the reference line
            lanes = lane_section.rightLanes if side == "right" else lane_section.leftLanes
            coeff_factor = -1.0 if side == "right" else 1.0

            # Most inner border gets added first
            lane_borders = [reference_border]

            # copy reference border, but set refOffset to start of lane_section

            for lane in lanes:
                (
                    inner_neighbour_id,
                    outer_neighbour_id,
                    inner_neighbour_same_dir,
                ) = OpenDriveConverter.determine_neighbours(lane)

                # Create outer lane border
                # outer_parametric_lane_border =

                lane_borders.append(OpenDriveConverter._create_outer_lane_border(lane_borders, lane, coeff_factor))

                # check the center line to save the inner linemarkings of the lanes around the center line
                inner_linemarking = None
                # lanes around the center line have an id of 1 and -1.
                if lane.id == 1 or lane.id == -1:
                    for parent_lane_section in lane.parentRoad.lanes.lane_sections:
                        # check for the center line
                        if len(parent_lane_section.centerLanes) > 0:
                            # check if the center lane has a road mark
                            if len(parent_lane_section.centerLanes[0].road_mark) > 0:
                                # assign the road mark to the inner linemarking
                                inner_linemarking = copy.deepcopy(parent_lane_section.centerLanes[0].road_mark[0])
                                # check if the road mark type is made up of 2 different markings,
                                # assume right hand drive
                                if parent_lane_section.centerLanes[0].road_mark[0].type == "solid broken":
                                    if lane.id == 1:
                                        inner_linemarking.type = "solid"
                                    if lane.id == -1:
                                        inner_linemarking.type = "broken"
                                if parent_lane_section.centerLanes[0].road_mark[0].type == "broken solid":
                                    if lane.id == 1:
                                        inner_linemarking.type = "broken"
                                    if lane.id == -1:
                                        inner_linemarking.type = "solid"

                plane_group = ParametricLaneGroup(
                    id_=encode_road_section_lane_width_id(lane_section.parentRoad.id, lane_section.idx, lane.id, -1),
                    inner_neighbour=inner_neighbour_id,
                    inner_neighbour_same_direction=inner_neighbour_same_dir,
                    outer_neighbour=outer_neighbour_id,
                    inner_linemarking=inner_linemarking,
                )

                # Create new lane for each width segment
                for width in lane.widths:
                    # check if road mark was changed and set corresponding road mark
                    mark_idx = -1
                    for mark in lane.road_mark:
                        if width.start_offset > mark.SOffset:
                            mark_idx += 1
                    # create new lane
                    parametric_lane = OpenDriveConverter.create_parametric_lane(
                        lane_borders, width, lane, side, mark_idx
                    )
                    parametric_lane.reverse = bool(lane.id > 0)
                    plane_group.append(parametric_lane)

                # if lane borders are specified by offsets instead of widths
                # for borders in lane.borders:

                if plane_group.length > 0:
                    plane_groups.append(plane_group)
        return plane_groups

    @staticmethod
    def create_parametric_lane(
        lane_borders: List[Border], width: LaneWidth, lane: Lane, side: str, mark_idx: int
    ) -> ParametricLane:
        """Create a parametric lane for a certain width section.

        :param lane_borders: Array with already created lane borders.
        :param width: Width section with offset and coefficient information.
        :param lane: Lane in which new parametric lane is created.
        :param side: Which side of the lane section where the parametric lane is created.
        :param mark_idx: Index of line marking belonging to lane.
        :return: A ParametricLane object with specified borders and a unique id.
        """
        if len(lane.road_mark) > 0:
            marking = lane.road_mark[mark_idx]
        else:
            marking = None

        border_group = ParametricLaneBorderGroup(
            inner_border=lane_borders[-2],
            outer_border=lane_borders[-1],
            inner_border_offset=width.start_offset + lane_borders[-1].ref_offset,
            outer_border_offset=width.start_offset,
        )
        parametric_lane = ParametricLane(
            id_=encode_mark_lane_width_id(
                lane.lane_section.parentRoad.id,
                lane.lane_section.idx,
                lane.id,
                width.idx,
                mark_idx,
            ),
            type_=lane.type,
            length=width.length,
            border_group=border_group,
            speed=lane.speed,
            line_marking=marking,
            side=side,
            access=lane.access,
        )
        return parametric_lane

    @staticmethod
    def _create_outer_lane_border(lane_borders: List[Border], lane: Lane, coeff_factor: int) -> Border:
        """Create an outer lane border of a lane.
        InnerBorder is already saved in lane_borders, as it is
        the outer border of the inner neighbour of the lane.

        :param lane_borders: Previous calculated lane borders of more inner lanes.
        :param lane: Lane for which outer border shall be created.
        :param coeff_factor: Factor of -1 or 1, depending on which side of the reference path the lane is.
            Right side is -1.
        :return: The created outer lane border.
        """

        # Create outer lane border
        # Offset from reference border is already included in first inner border
        # (lane_border[0])
        # reference_border starts at beginning of road, prev: lane section
        border = Border()
        if len(lane_borders) == 1:
            border.ref_offset = lane.lane_section.sPos

        # last created border
        if lane.has_border_record:
            border.reference = lane_borders[0]
        else:
            border.reference = lane_borders[-1]

        for width in lane.widths:
            border.width_coefficient_offsets.append(width.start_offset)
            border.width_coefficients.append([x * coeff_factor for x in width.polynomial_coefficients])
        return border

    @staticmethod
    def determine_neighbours(lane: Lane) -> Tuple[str, str, bool]:
        """Determines neighbors of a lane.

        :param lane: Lane to find neighbors to.
        :return: IDs of the inner and outer neighbor, and whether the inner neighbor has the same direction.
        """
        if abs(lane.id) > 1:
            if lane.id > 0:
                inner_lane_id = lane.id - 1
                outer_lane_id = lane.id + 1
            else:
                inner_lane_id = lane.id + 1
                outer_lane_id = lane.id - 1

            inner_neighbour_same_dir = True

        else:
            # Skip lane id 0

            if lane.id == 1:
                inner_lane_id = -1
                outer_lane_id = 2
            else:
                inner_lane_id = 1
                outer_lane_id = -2
            inner_neighbour_same_dir = False

        inner_neighbour_id = encode_road_section_lane_width_id(
            lane.lane_section.parentRoad.id, lane.lane_section.idx, inner_lane_id, -1
        )

        outer_neighbour_id = encode_road_section_lane_width_id(
            lane.lane_section.parentRoad.id, lane.lane_section.idx, outer_lane_id, -1
        )

        return inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir
