import iso3166
from dataclasses import dataclass


@dataclass
class CustomDefaultLaneletType:
    general_lanelet_type_activ: bool  # activates whether certain lanelet type should be added to all lanelets
    general_lanelet_type: str  # lanelet type which is added to every lanelet (if activated)
    driving_default_lanelet_type: str  # mapping of OpenDRIVE driveway lane type to a CommonRoad lanelet type
    lanelet_types_backwards_compatible: bool # if active, converts OpenDRIVE lane types only to CommonRoad lanelet
    # types compatible with commonroad-io==2022.1 (probably also even older ones)


def encode_road_section_lane_width_id(road_id, section_id, lane_id, width_id) -> str:
    """Encodes a road section lane width with an ID.

    :param road_id: ID of road.
    :type road_id: int
    :param section_id: ID of RoadSection.
    :type section_id: int
    :param lane_id: ID of Lane.
    :type lane_id: int
    :param width_id: ID of LaneWidth.
    :type width_id: int
    :return: A new ID concatenated from the input IDs.
    :rtype: str
    """
    return ".".join([str(road_id), str(section_id), str(lane_id), str(width_id)])

def encode_mark_lane_width_id(roadId, sectionId, laneId, widthId, mId) -> str:
    """Encodes a road section lane width with an ID.

    :param roadId: ID of road.
    :type roadId: int
    :param sectionId: ID of RoadSection.
    :type sectionId: int
    :param laneId: ID of Lane.
    :type laneId: int
    :param widthId: ID of LaneWidth.
    :type widthId: int
    :return: A new ID concatenated from the input IDs.
    :rtype: str
    """
    return ".".join([str(roadId), str(sectionId), str(laneId), str(widthId), str(mId)])


def get_signal_country(signal_country: str) -> str:
    """
    ISO3166 standard to find three-letter country id
    :param signal_country: String value of the country.
    :type signal_country: str
    :return: The 3-letter country ID per ISO3166.
    :rtype: str
    """
    signal_country = signal_country.upper()
    if signal_country in iso3166.countries_by_name:
        return iso3166.countries_by_name[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha2:
        return iso3166.countries_by_alpha2[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha3:
        return signal_country
    else:
        return "ZAM"
