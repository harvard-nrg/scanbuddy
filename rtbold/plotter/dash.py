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
            dcc.Graph(id='live-update-displacements'),
            dcc.Graph(id='live-update-rotations'),
            dcc.Interval(
                id='interval-component',
                interval=1*1000
            )
        ])

    def init_callbacks(self):
        self._app.callback(
            Output('live-update-displacements', 'figure'),
            Output('live-update-rotations', 'figure'),
            Input('interval-component', 'n_intervals'),
        )(self.update_graphs)

    def update_graphs(self, n):
        df = self.todataframe()
        disps = self.displacements(df)
        rots = self.rotations(df)
        return disps,rots

    def displacements(self, df):
        fig = px.line(df, x='N', y=['superior', 'left', 'posterior'])
        fig.update_layout(
            title='Displacements',
            yaxis_title='mm',
            legend={
                'title': ''
            }
        )
        return fig

    def rotations(self, df):
        fig = px.line(df, x='N', y=['roll', 'pitch', 'yaw'])
        fig.update_layout(
            title='Rotations',
            yaxis_title='degrees (ccw)',
            legend={
                'title': ''
            }
        )
        return fig

    def todataframe(self):
        arr = list()
        for i,instance in enumerate(self._instances, start=1):
            if not instance:
                continue
            volreg = instance['volreg']
            if volreg:
                arr.append([i] + volreg)
        df = pd.DataFrame(arr, columns=['N', 'roll', 'pitch', 'yaw', 'superior', 'left', 'posterior'])
        return df

    def forever(self):
        self._app.run(debug=True)

    def listener(self, instances):
        self._instances = instances
