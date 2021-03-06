import io
import logging
import networkx as nx
import os
import threading
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import tornado.gen
import yaml
import webbrowser
from contextlib import contextmanager
from time import sleep
from xml.etree.ElementTree import tostring

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PageHandler(tornado.web.RequestHandler):
    """ Handler for the HTML template which holds the visualization. """

    def get(self):
        self.render('index.html', port=self.application.port,
                    name=self.application.name)


class SocketHandler(tornado.websocket.WebSocketHandler):
    """ Handler for websocket. """

    def open(self):
        if self.application.verbose:
            logger.info('Socket opened!')

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        """ Receiving a message from the websocket, parse, and act accordingly. """

        msg = tornado.escape.json_decode(message)

        if msg['type'] == 'config_file':

            if self.application.verbose:
                print(msg['data'])

            self.config = list(yaml.load_all(msg['data']))

            if len(self.config) > 1:
                error = 'Please, provide only one configuration.'
                if self.application.verbose:
                    logger.error(error)
                self.write_message({'type': 'error',
                    'error': error})
                return
            else:
                self.config = self.config[0]
                self.send_log('INFO.' + self.application.simulator.name, 'Using config: {name}'.format(name=self.config['name']))

            if 'visualization_params' in self.config:
                self.write_message({'type': 'visualization_params',
                    'data': self.config['visualization_params']})
            self.name = self.config['name']
            self.run_simulation()

            settings = []
            for key in self.config['environment_params']: 
                if type(self.config['environment_params'][key]) == float or type(self.config['environment_params'][key]) == int:
                    if self.config['environment_params'][key] <= 1:
                        setting_type = 'number'
                    else:
                        setting_type = 'great_number'
                elif type(self.config['environment_params'][key]) == bool:
                    setting_type = 'boolean'
                else:
                    setting_type = 'undefined'

                settings.append({
                    'label': key,
                    'type': setting_type,
                    'value': self.config['environment_params'][key]
                })

            self.write_message({'type': 'settings',
                'data': settings})

        elif msg['type'] == 'get_trial':
            if self.application.verbose:
                logger.info('Trial {} requested!'.format(msg['data']))
            self.send_log('INFO.' + __name__, 'Trial {} requested!'.format(msg['data']))
            self.write_message({'type': 'get_trial',
                'data': self.get_trial( int(msg['data']) ) })

        elif msg['type'] == 'run_simulation':
            if self.application.verbose:
                logger.info('Running new simulation for {name}'.format(name=self.config['name']))
            self.send_log('INFO.' + self.application.simulator.name, 'Running new simulation for {name}'.format(name=self.config['name']))
            self.config['environment_params'] = msg['data']
            self.run_simulation()

        elif msg['type'] == 'download_gexf':
            G = self.simulation[ int(msg['data']) ].history_to_graph()
            for node in G.nodes():
                if 'pos' in G.node[node]:
                    G.node[node]['viz'] = {"position": {"x": G.node[node]['pos'][0], "y": G.node[node]['pos'][1], "z": 0.0}}
                    del (G.node[node]['pos'])
            writer = nx.readwrite.gexf.GEXFWriter(version='1.2draft')
            writer.add_graph(G)
            self.write_message({'type': 'download_gexf',
                'filename': self.config['name'] + '_trial_' + str(msg['data']),
                'data': tostring(writer.xml).decode(writer.encoding) })

        elif msg['type'] == 'download_json':
            G = self.simulation[ int(msg['data']) ].history_to_graph()
            for node in G.nodes():
                if 'pos' in G.node[node]:
                    G.node[node]['viz'] = {"position": {"x": G.node[node]['pos'][0], "y": G.node[node]['pos'][1], "z": 0.0}}
                    del (G.node[node]['pos'])
            self.write_message({'type': 'download_json',
                'filename': self.config['name'] + '_trial_' + str(msg['data']),
                'data': nx.node_link_data(G) })

        else:
            if self.application.verbose:
                logger.info('Unexpected message!')

    def update_logging(self):
        try:
            if (not self.log_capture_string.closed and self.log_capture_string.getvalue()):
                for i in range(len(self.log_capture_string.getvalue().split('\n')) - 1):
                    self.send_log('INFO.' + self.application.simulator.name, self.log_capture_string.getvalue().split('\n')[i])
                self.log_capture_string.truncate(0)
                self.log_capture_string.seek(0)
        finally:
            if self.capture_logging:
                thread = threading.Timer(0.01, self.update_logging)
                thread.start()

    def on_close(self):
        if self.application.verbose:
            logger.info('Socket closed!')

    def send_log(self, logger, logging):
        self.write_message({'type': 'log',
            'logger': logger,
            'logging': logging })

    def run_simulation(self):
        # Run simulation and capture logs
        if 'visualization_params' in self.config:
            del self.config['visualization_params']
        with self.logging(self.application.simulator.name):
            try:
                self.simulation = self.application.simulator.run(self.config)
                trials = []
                for i in range(self.config['num_trials']):
                    trials.append('{}_trial_{}'.format(self.name, i))
                self.write_message({'type': 'trials',
                    'data': trials })
            except:
                error = 'Something went wrong. Please, try again.'
                self.write_message({'type': 'error',
                    'error': error})
                self.send_log('ERROR.' + self.application.simulator.name, error)

    def get_trial(self, trial):
        G = self.simulation[trial].history_to_graph()
        return nx.node_link_data(G)

    @contextmanager
    def logging(self, logger):
        self.capture_logging = True
        self.logger_application = logging.getLogger(logger)
        self.log_capture_string = io.StringIO()
        ch = logging.StreamHandler(self.log_capture_string)
        self.logger_application.addHandler(ch)
        self.update_logging()
        yield self.capture_logging

        sleep(0.2)
        self.log_capture_string.close()
        self.logger_application.removeHandler(ch)
        self.capture_logging = False
        return self.capture_logging
    

class ModularServer(tornado.web.Application):
    """ Main visualization application. """

    port = 8001
    page_handler = (r'/', PageHandler)
    socket_handler = (r'/ws', SocketHandler)
    static_handler = (r'/(.*)', tornado.web.StaticFileHandler,
                      {'path': 'templates'})
    local_handler = (r'/local/(.*)', tornado.web.StaticFileHandler,
                     {'path': ''})

    handlers = [page_handler, socket_handler, static_handler, local_handler]
    settings = {'debug': True,
                'template_path': os.path.dirname(__file__) + '/templates'}

    def __init__(self, simulator, name='SOIL', verbose=True, *args, **kwargs):
        
        self.verbose = verbose
        self.name = name
        self.simulator = simulator

        # Initializing the application itself:
        super().__init__(self.handlers, **self.settings)

    def launch(self, port=None):
        """ Run the app. """
        
        if port is not None:
            self.port = port
        url = 'http://127.0.0.1:{PORT}'.format(PORT=self.port)
        print('Interface starting at {url}'.format(url=url))
        self.listen(self.port)
        # webbrowser.open(url)
        tornado.ioloop.IOLoop.instance().start()
