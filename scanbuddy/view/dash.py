import os
import sys
import dash
import redis
import random
import secrets
import logging
import pandas as pd
from pubsub import pub
import plotly.express as px
import dash_auth
from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

ERROR_ART = """
██╗    ██╗ █████╗ ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
██║    ██║██╔══██╗██╔══██╗████╗  ██║██║████╗  ██║██╔════╝ 
██║ █╗ ██║███████║██████╔╝██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══██║██╔══██╗██║╚██╗██║██║██║╚██╗██║██║   ██║
╚███╔███╔╝██║  ██║██║  ██║██║ ╚████║██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""
DEFAULT_MESSAGE = 'Hello, World!'

class View:
    def __init__(self, host='127.0.0.1', port=8080, config=None, debug=False):
        self._config = config
        self._host = self._config.find_one('$.app.host', default=host)
        self._port = self._config.find_one('$.app.port', default=port)
        self._debug = self._config.find_one('$.app.debug', default=debug)
        self._title = self._config.find_one('$.app.title', default='Realtime fMRI Motion')
        self._subtitle = 'Ready'
        self._num_warnings = 0
        self._instances = dict()
        self._redis_client = redis.StrictRedis(
            host=self._config.find_one('$.broker.host', default='127.0.0.1'),
            port=self._config.find_one('$.broker.port', default=6379),
            db=0
        )
        self.init_app()
        self.init_page()
        self.init_callbacks()
        pub.subscribe(self.listener, 'plot')

    def init_app(self):
        self._app = Dash(
            self._title,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP
            ]
        )
        username = self._config.find_one('$.app.auth.user')
        passphrase = self._get_passphrase()
        auth = {
            username: passphrase
        }
        session_secret_key = self._session_secret()
        dash_auth.BasicAuth(
            self._app,
            auth,
            secret_key=session_secret_key
        )

    def _session_secret(self):
        envar = self._config.find_one('$.app.session_secret.env')
        if not envar:
            raise AuthError('you must specify a session secret key environment variable')
        if envar not in os.environ:
            raise AuthError(f'environment variable "{envar}" is not defined')
        value = os.environ[envar]
        if not value.strip():
            raise AuthError('value stored in environment variable "{envar}" cannot be empty')
        return value

    def _get_passphrase(self):
        envar = self._config.find_one('$.app.auth.pass.env')
        if not envar:
            raise AuthError('you must specify an authentication passphrase environment variable')
        if envar not in os.environ:
            raise AuthError(f'environment variable "{envar}" is not defined')
        value = os.environ[envar]
        if not value.strip():
            raise AuthError(f'value stored in environment variable "{envar}" cannot be empty')
        return value

    def init_page(self):
        notifications_button = dbc.NavItem(
            dbc.Button([
                'Notifications',
                dbc.Badge(
                    id='notification-badge',
                    color='light',
                    text_color='primary',
                    className='ms-1'
                )],
                id='notifications-button',
                color='primary'
            )
        )   

        branding = dbc.NavbarBrand(
            self._title,
            class_name='ms-2'
        )   

        subtitle = dbc.NavItem(
            self._subtitle,
            id='sub-title',
            style={
                'color': '#e2ded0'
            }
        )   

        navbar = dbc.Navbar(
            dbc.Container([
                dbc.Row(
                    dbc.Col(branding),
                ),
                dbc.Row(
                    dbc.Col(subtitle, class_name='g-0 ms-auto flex-nowrap mt-3 mt-md-0')
                ),
                dbc.Row(
                    dbc.Col(notifications_button, class_name='ms-2'),
                )
            ]),
            color="dark",
            dark=True
        )   

        displacements_graph = dcc.Graph(
            id='live-update-displacements',
            style={
                'height': '47vh'
            }
        )   

        rotations_graph = dcc.Graph(
            id='live-update-rotations',
            style={
                'height': '47vh'
            }
        )   

        metrics_card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H5("Motion Metrics", className="card-title", style={"borderBottom": "1px solid black", "marginBottom": "0px", "textAlign": "center", "padding": "10px"}),
                        dbc.Row([
                            dbc.Col("Number of Movements > .5 mm", width={"size": 8, "order": 1}, style={"borderRight": "1px solid black", "borderBottom": "1px solid black", "textAlign": "center", "padding": "10px"}),
                            dbc.Col(id='movements-05mm', children="0", width={"size": 4, "order": 2}, style={"borderBottom": "1px solid black", "textAlign": "center", "padding": "10px"})
                        ], style={"margin": "0px"}),
                        dbc.Row([
                            dbc.Col("Number of Movements > 1 mm", width={"size": 8, "order": 1}, style={"borderRight": "1px solid black", "textAlign": "center", "padding": "10px"}),
                            dbc.Col(id='movements-1mm', children="0", width={"size": 4, "order": 2}, style={"textAlign": "center", "padding": "10px"})
                        ], style={"margin": "0px"})
                    ],
                    style={"border": "1px solid black", "padding": "0"})
            ],
            style={"width": "24rem", "border": "1px solid black", "backgroundColor": "#ffe4e1"},
            className="m-2"
        )

        self._app.layout = html.Div([
            navbar,
            dbc.Row(
                [
                    dbc.Col(metrics_card, width=2, style={"marginTop": "50px"}),
                    dbc.Col(
                        [
                            displacements_graph,
                            rotations_graph,
                        ],
                        width=10
                    ),
                ],
                className="g-0"
            ),
            html.Dialog(
                id='bsod-dialog',
                children=[
                    html.Pre(
                        ERROR_ART,
                        id='bsod-title',
                        style={
                            'color': 'red',
                            'verticalAlign': 'center',
                            'fontFamily': 'courier, monospace',
                            'fontSize': '1vw',
                        }
                    ),
                    html.Pre(
                        DEFAULT_MESSAGE,
                        id='bsod-content',
                        style={
                            'color': 'red',
                            'fontFamily': 'courier, monospace',
                            'fontSize': '1.3vw',
                            'textAlign': 'left',
                            'whiteSpace': 'pre-wrap',
                            'padding': '5vh 5vw 5vh 5vw',
                        }
                    ),
                    html.Button(
                        'DISMISS',
                        id='bsod-dismiss-button',
                        style={
                            'color': 'black',
                            'borderColor': 'grey',
                            'borderWidth': '1vh',
                            'backgroundColor': '',
                            'padding': '1vh 1vw 1vh 1vw',
                            'fontFamily': 'courier, monospace',
                            'fontSize': '1.5vw'
                        }
                    )
                ],
                style={
                    'backgroundColor': 'black',
                    'position': 'absolute',
                    'top': 0,
                    'height': '100vh',
                    'width': '100vw',
                    'padding': 0,
                    'margin': 0,
                    'textAlign': 'center',
                }
            ),
            dcc.Interval(
                id='plot-interval-component',
                interval=1 * 1000
            ),
            dcc.Interval(
                id='message-interval-component',
                interval=1 * 1000
            )
        ])


    def init_callbacks(self):
        self._app.callback(
            Output('live-update-displacements', 'figure'),
            Output('live-update-rotations', 'figure'),
            Output('sub-title', 'children'),
            Input('plot-interval-component', 'n_intervals'),
        )(self.update_graphs)

        self._app.callback(
            Output('bsod-dialog', 'open', allow_duplicate=True),
            Output('bsod-content', 'children', allow_duplicate=True),
            Output('notification-badge', 'children'),
            Input('message-interval-component', 'n_intervals'),
            prevent_initial_call=True
        )(self.check_messages)

        self._app.callback(
            Output('bsod-dialog', 'open', allow_duplicate=True),
            Output('bsod-content', 'children', allow_duplicate=True),
            Input('bsod-dismiss-button', 'n_clicks'),
            prevent_initial_call=True
        )(self.close_bsod)

        self._app.callback(
            Output('movements-05mm', 'children'),
            Output('movements-1mm', 'children'),
            Input('plot-interval-component', 'n_intervals'),
        )(self.update_metrics)

    def check_messages(self, n_intervals):
        try:
            message = self._redis_client.get('scanbuddy_messages')
            if message:
                self._num_warnings += 1
                self._redis_client.delete('scanbuddy_messages')
                return True, message.decode(), self._num_warnings
        except redis.exceptions.ConnectionError as e:
            logger.warning(f'unable to get messages from message broker, service unavailable')

        return dash.no_update,dash.no_update,dash.no_update

    def close_bsod(self, n_clicks):
        return False, 'Hello, World!'

    def update_graphs(self, n):
        df = self.todataframe()
        disps = self.displacements(df)
        rots = self.rotations(df)
        title = self.get_subtitle()
        return disps,rots,title

    def update_metrics(self, n):
        df = self.todataframe()
        movements_05mm = (df[['x', 'y', 'z']].abs() > 0.5).any(axis=1).sum() + (df[['x', 'y', 'z']].abs() < -0.5).any(axis=1).sum()
        movements_1mm = (df[['x', 'y', 'z']].abs() > 1.0).any(axis=1).sum() + (df[['x', 'y', 'z']].abs() < -1.0).any(axis=1).sum()
        return str(movements_05mm), str(movements_1mm)

    def get_subtitle(self):
        return self._subtitle

    def displacements(self, df):
        fig = px.line(df, x='N', y=['x', 'y', 'z'])
        fig.update_layout(
            title={
                'text': f'Translations',
                'x': 0.5
            },
            yaxis_title='mm',
            legend={
                'title': ''
            },
            shapes=[
                {  # 1 mm line
                    'type': 'line',
                    'xref': 'paper',
                    'x0': 0,
                    'x1': 1,
                    'y0': 1,
                    'y1': 1,
                    'line': {
                        'color': 'black',
                        'width': 2,
                        'dash': 'solid',
                    },
                },
                {  # -1 mm line
                    'type': 'line',
                    'xref': 'paper',
                    'x0': 0,
                    'x1': 1,
                    'y0': -1,
                    'y1': -1,
                    'line': {
                        'color': 'black',
                        'width': 2,
                        'dash': 'solid',
                    },
                },
            ]
        )
        return fig

    def rotations(self, df):
        fig = px.line(df, x='N', y=['roll', 'pitch', 'yaw'])
        fig.update_layout(
            title={
                'text': f'Rotations',
                'x': 0.5
            },
            yaxis_title='degrees (ccw)',
            legend={
                'title': ''
            },
            shapes=[
                {  # 1 degree line
                    'type': 'line',
                    'xref': 'paper',
                    'x0': 0,
                    'x1': 1,
                    'y0': .5,
                    'y1': .5,
                    'line': {
                        'color': 'black',
                        'width': 2,
                        'dash': 'solid',
                    },
                },
                {  # -1 degree line
                    'type': 'line',
                    'xref': 'paper',
                    'x0': 0,
                    'x1': 1,
                    'y0': -.5,
                    'y1': -.5,
                    'line': {
                        'color': 'black',
                        'width': 2,
                        'dash': 'solid',
                    },
                },
            ]
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
            port=self._port,
            debug=self._debug
        )

    def listener(self, instances, subtitle_string):
        self._instances = instances
        self._subtitle = subtitle_string

class AuthError(Exception):
    pass
