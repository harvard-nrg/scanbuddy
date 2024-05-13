import sys
import logging
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import random

logger = logging.getLogger('ui')

class DashPlotter:
    _instances = list()

    def __init__(self):
        self._app = Dash('Realtime fMRI is fun')
        self._title = 'Realtime fMRI Motion'
        self.setup()

    def setup(self):
        self._app.layout = html.Div([
            html.H1(children=self._title, style={'textAlign':'center'}),
            html.Div(id='live-update-text'),
            dcc.Graph(id='live-update-graph'),
            dcc.Interval(
                id='interval-component',
                interval=2*1000, # in milliseconds
                n_intervals=0
            )
        ])

    @callback(
        Output('live-update-graph', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_graph(n):
        df = DashPlotter.df()
        return px.line(df, x='timepoint', y='roll')

    def df():
        arr = list()
        for i,instance in enumerate(DashPlotter._instances, start=1):
            volreg = instance['volreg']
            if volreg:
                arr.append([i] + volreg)
        df = pd.DataFrame(arr, columns=['timepoint', 'roll', 'pitch', 'yaw', 'dS', 'dL', 'dP'])
        return df

    def forever(self):
        self._app.run(debug=True)

    def listener(self, instances):
        DashPlotter._instances = instances
