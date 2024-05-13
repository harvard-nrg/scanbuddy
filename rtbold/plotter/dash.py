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
            html.H2(children=self._title, style={'textAlign':'center'}),
            html.Div(id='live-update-text'),
            dcc.Graph(id='live-update-translations'),
            dcc.Graph(id='live-update-rotations'),
            dcc.Interval(
                id='interval-component',
                interval=2*1000, # in milliseconds
                n_intervals=0
            )
        ])

    @callback(
        Output('live-update-translations', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_graph(n):
        df = DashPlotter.df()
        line = px.line(df, x='N', y=['superior', 'left', 'posterior'])
        line.update_layout(
            title='Displacements',
            yaxis_title='mm',
            legend={
                'title': ''
            }
        )
        return line 

    @callback(
        Output('live-update-rotations', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_graph(n):
        df = DashPlotter.df()
        line = px.line(df, x='N', y=['roll', 'pitch', 'yaw'])
        line.update_layout(
            title='Rotations',
            yaxis_title='degrees (ccw)',
            legend={
                'title': ''
            }
        )
        return line 

    def df():
        arr = list()
        for i,instance in enumerate(DashPlotter._instances, start=1):
            volreg = instance['volreg']
            if volreg:
                arr.append([i] + volreg)
        df = pd.DataFrame(arr, columns=['N', 'roll', 'pitch', 'yaw', 'superior', 'left', 'posterior'])
        return df

    def forever(self):
        self._app.run(debug=True)

    def listener(self, instances):
        DashPlotter._instances = instances
