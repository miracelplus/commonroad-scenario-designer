import os
import subprocess

from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.scenario.scenario import Tag
from lxml import etree
from crmapconverter.opendrive.opendriveconversion.network import Network
from crmapconverter.opendrive.opendriveparser.parser import parse_opendrive


def convert_net_to_cr(net_file:str, out_folder:str=None, verbose=False) -> str:
    """
    Converts .net file to CommonRoad xml using Netconvert and OpenDRIVE 2 Lanelet Converter.

    :param net_file: path of .net.xml file
    :param out_folder: path of output folder for CommonRoad scenario.

    :return: commonroad map file
    """
    assert isinstance(net_file,str)

    if out_folder is None:
        out_folder = os.path.dirname(net_file)

    # filenames
    scenario_name = _get_scenario_name_from_netfile(net_file)
    opendrive_file = os.path.join(out_folder, scenario_name + '.xodr')
    cr_map_file = os.path.join(out_folder, scenario_name + '.cr.xml')

    # convert to OpenDRIVE file using netconvert
    out = subprocess.check_output(['netconvert', '-s', net_file,
                                   '--opendrive-output', opendrive_file,
                                   '--junctions.scurve-stretch', '1.0'])
    if verbose:
        print('converted to OpenDrive (.xodr)')

    # convert to commonroad using opendrive2lanelet
    # import, parse and convert OpenDRIVE file
    with open(opendrive_file, "r") as fi:
        open_drive = parse_opendrive(etree.parse(fi).getroot())


    road_network = Network()
    road_network.load_opendrive(open_drive)
    scenario = road_network.export_commonroad_scenario()
    if verbose:
        print('converted to Commonroad (.cr.xml)')

    # write CommonRoad scenario to file
    commonroad_writer = CommonRoadFileWriter(scenario, planning_problem_set=None,
                                             source="Converted from SUMO net using netconvert and OpenDRIVE 2 Lanelet Converter",
                                             tags=set(Tag.simulated), author='', affiliation='')

    commonroad_writer.write_scenario_to_file(cr_map_file)

    return cr_map_file


def _get_scenario_name_from_netfile(filepath:str) -> str:
    """
    Returns the scenario name specified in the net file.

    :param filepath: the path of the net file

    """
    scenario_name:str = (os.path.splitext(os.path.basename(filepath))[0]).split('.')[0]
    return scenario_name
