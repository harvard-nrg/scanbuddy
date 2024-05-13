import sys
import logging
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import random

logger = logging.getLogger('ui')

class DashPlotter:
    def __init__(self):
        self._app = Dash('Realtime fMRI is fun')
        self._title = 'Realtime fMRI Motion'
        self._instances = list()
        self.init_page()
        self.init_callbacks()

    def init_page(self):
        self._app.layout = html.Div([
            html.H2(children=self._title, style={'textAlign':'center'}),
            html.Div(id='live-update-text'),
            dcc.Graph(id='live-update-rotations'),
            dcc.Graph(id='live-update-displacements'),
            dcc.Interval(
                id='interval-component',
                interval=1*1000,
                n_intervals=0
            )
        ])

    def init_callbacks(self):
        self._app.callback(
            Output('live-update-rotations', 'figure'),
            Input('interval-component', 'n_intervals'),
        )(self.update_rotations)

        self._app.callback(
            Output('live-update-displacements', 'figure'),
            Input('interval-component', 'n_intervals'),
        )(self.update_displacements)

    def update_displacements(self, n):
        df = self.df()
        fig = px.line(df, x='N', y=['superior', 'left', 'posterior'])
        fig.update_layout(
            yaxis_title='mm',
            legend={
                'title': ''
            },
            title={
                'text': 'Displacements'
            }
        )
        return fig

    def update_rotations(self, n):
        df = self.df()
        line = px.line(df, x='N', y=['roll', 'pitch', 'yaw'])
        line.update_layout(
            yaxis_title='degrees (ccw)',
            legend={
                'title': ''
            },
            title={
                'text': 'Rotations'
            }
        )
        return line 

    def df(self):
        arr = list()
        for i,instance in enumerate(self._instances, start=1):
            volreg = instance['volreg']
            if volreg:
                arr.append([i] + volreg)
        df = pd.DataFrame(arr, columns=['N', 'roll', 'pitch', 'yaw', 'superior', 'left', 'posterior'])
        return df

    def forever(self):
        self._app.run(debug=True)

    def listener(self, instances):
        self._instances = instances
