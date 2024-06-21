import sys
import logging
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import random
from pubsub import pub

logger = logging.getLogger('ui')

class DashPlotter:
    def __init__(self, host='127.0.0.1', port=8080):
        self._app = Dash('Realtime fMRI is fun')
        self._host = host
        self._port = port
        self._title = 'Realtime fMRI Motion'
        self._subtitle = ''
        self._instances = dict()
        self.init_page()
        self.init_callbacks()
        pub.subscribe(self.listener, 'plot')

    def init_page(self):
        self._app.layout = html.Div([
            html.H2(id='graph-title', children=self._title, style={'textAlign':'center'}),
            html.H3(id='sub-title', children=self._subtitle, style={'textAlign':'center'}),
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
            Output('sub-title', 'children'),
            Input('interval-component', 'n_intervals'),
        )(self.update_graphs)

    def update_graphs(self, n):
        df = self.todataframe()
        disps = self.displacements(df)
        rots = self.rotations(df)
        title = self.get_subtitle()
        return disps,rots,title

    def get_subtitle(self):
        title = self._subtitle
        return title

    def displacements(self, df):
        fig = px.line(df, x='N', y=['x', 'y', 'z'])
        fig.update_layout(
            title={
                'text': 'Translations',
                'x': 0.5
            },
            yaxis_title='mm',
            legend={
                'title': ''
            }
        )
        return fig

    def rotations(self, df):
        fig = px.line(df, x='N', y=['roll', 'pitch', 'yaw'])
        fig.update_layout(
            title={
                'text': 'Rotations',
                'x': 0.5
            },
            yaxis_title='degrees (ccw)',
            legend={
                'title': ''
            }
        )
        return fig

    def todataframe(self):
        arr = list()
        for i,instance in enumerate(self._instances.values(), start=1):
            volreg = instance['volreg']
            if volreg:
                arr.append([i] + volreg)
        df = pd.DataFrame(arr, columns=['N', 'roll', 'pitch', 'yaw', 'x', 'y', 'z'])
        return df

    def forever(self):
        self._app.run(
            host=self._host,
            port=self._port
        )

    def listener(self, instances, subtitle_string):
        self._instances = instances
        self._subtitle = subtitle_string
