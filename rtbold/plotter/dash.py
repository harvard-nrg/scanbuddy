import sys
import redis
import random
import logging
import pandas as pd
from pubsub import pub
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input, State

logger = logging.getLogger('ui')

class DashPlotter:
    def __init__(self, host='127.0.0.1', port=8080):
        self._app = Dash('Realtime fMRI is fun')
        self._host = host
        self._port = port
        self._title = 'Realtime fMRI Motion'
        self._subtitle = ''
        self._instances = dict()
        self._redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        self.init_page()
        self.init_callbacks()
        pub.subscribe(self.listener, 'plot')

    def init_page(self):
        self._app.layout = html.Div([
            html.H2(id='graph-title', children=self._title, style={'textAlign': 'center'}),
            html.H3(id='sub-title', children=self._subtitle, style={'textAlign': 'center'}),
            dcc.Graph(id='live-update-displacements'),
            dcc.Graph(id='live-update-rotations'),
            html.Div(id='warning-message', style={'display': 'none'}, children=[
                html.Div('WARNING', id='warning-text', style={'color': 'red', 'fontSize': 50, 'textAlign': 'center'}),
                html.Div(id='warning-content', style={'color': 'red', 'fontSize': 25, 'textAlign': 'center'}),
                html.Button(id='close-warning-button', n_clicks=0, children='Close')
                ]),
            dcc.Interval(
                id='interval-component',
                interval=1 * 1000
            ),
            dcc.Interval(
                id='warning-interval-component',
                interval=1 * 1000
            ),
            dcc.Store(id='warning-message-store', data={'visible': False, 'content': ''})
        ])


    def init_callbacks(self):
        self._app.callback(
            Output('live-update-displacements', 'figure'),
            Output('live-update-rotations', 'figure'),
            Output('sub-title', 'children'),
            Input('interval-component', 'n_intervals'),
        )(self.update_graphs)

        self._app.callback(
            Output('warning-message-store', 'data'),
            Input('warning-interval-component', 'n_intervals')
        )(self.check_redis_for_warnings)    

        self._app.callback(
            Output('warning-message', 'style'),
            Output('warning-content', 'children'),
            Input('warning-message-store', 'data')
        )(self.warning_display) 

        self._app.callback(
            Output('warning-message-store', 'data'),
            Input('close-warning-button', 'n_clicks'),
            State('warning-message-store', 'data')
        )(self.close_warning)


    def warning_display(self, stored_data):
        if stored_data['visible']:
            warning_style = {
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'white',
                'display': 'block',
                'zIndex': 1,
                'textAlign': 'center'
            }
            warning_content = stored_data['content']
        else:
            warning_style = {'display': 'none'}
            warning_content = '' 
        return warning_style, warning_content

    def check_redis_for_warnings(self, n):
        logger.info(f"Connecting to redis at {self._redis_client}")
        message = self._redis_client.get('scanbuddy_messages')
        logger.info(f"Message from redis: {message}")
        if message:
            return {'visible': True, 'content': message.decode('utf-8')}
        return {'visible': False, 'content': ''}

    def close_warning(self, n_clicks, stored_data):
        if n_clicks is not None and n_clicks > 0:
            return {'visible': False, 'content': ''}
        return stored_data

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
