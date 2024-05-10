import logging
from dash import Dash, html, dcc, callback, Output, Input

logger = logging.getLogger('ui')

class DashPlotter:
    def __init__(self):
        self._app = Dash('RT Fun')
        self.setup()

    def setup(self):
        self._app.layout = html.Div([
            html.H1(children='Title of Dash App', style={'textAlign':'center'}),
            dcc.Graph(id='graph-content')
        ]) 
    
    def forever(self):
        self._app.run(debug=True)

    def listener(self, instances):
        pass
