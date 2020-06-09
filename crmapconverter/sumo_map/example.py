import os
import numpy as np

from .cr2sumo import CR2SumoMapConverter
from .scenario_wrapper import ScenarioWrapper
from .config import SumoConfig
from commonroad.common.file_reader import CommonRoadFileReader

from .sumo_interface.sumo2cr.interface.sumo_simulation import SumoSimulation

files_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'test_files'))
scenario_name = "merging_lanelets_utm"
input_file = os.path.join(files_folder, scenario_name + '.xml')
net_path = os.path.join(files_folder, scenario_name + ".net.xml")

scenario, planning_problem = CommonRoadFileReader(input_file).open()

# translate scenario to center
centroid = np.mean(np.concatenate(
    [l.center_vertices for l in scenario.lanelet_network.lanelets]),
                   axis=0)
scenario.translate_rotate(-centroid, 0)
planning_problem.translate_rotate(-centroid, 0)

config = SumoConfig()
# convert net to .net.xml
converter = CR2SumoMapConverter(scenario.lanelet_network, config)
converter.convert_net()
converter.write_net(net_path)

# create Scenario Wrapper
# generate additional files
scenario_wrapper = ScenarioWrapper.init_from_net_file(net_path, input_file)

# run Simulation
simulation = SumoSimulation()
simulation.initialize(config, scenario_wrapper)

for t in range(config.simulation_steps):
    simulation.simulate_step()

simulation.stop()

# save resulting scenario
print(simulation.commonroad_scenarios_all_time_steps())
