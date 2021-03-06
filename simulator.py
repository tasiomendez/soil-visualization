import os
import networkx as nx
from soil.simulation import SoilSimulation


class Simulator():
    """ Simulator for running simulations. Using SOIL."""

    def __init__(self, dump=False, dir_path='output'):
        self.name = 'soil'
        self.dump = dump
        self.dir_path = dir_path

    def run(self, config):
        name = config['name']
        print('Using config(s): {name}'.format(name=name))

        sim = SoilSimulation(**config)
        sim.dir_path = os.path.join(self.dir_path, name)
        sim.dump = self.dump

        print('Dumping results to {} : {}'.format(sim.dir_path, sim.dump))
        
        simulation_results = sim.run_simulation()

        # G = simulation_results[0].history_to_graph()
        # for node in G.nodes():
        #     if 'pos' in G.node[node]:
        #         G.node[node]['viz'] = {"position": {"x": G.node[node]['pos'][0], "y": G.node[node]['pos'][1], "z": 0.0}}
        #         del (G.node[node]['pos'])
        # nx.write_gexf(G, 'test.gexf', version='1.2draft')

        return simulation_results

    def reset(self):
        pass
