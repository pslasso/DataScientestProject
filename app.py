import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import requests
from dash.exceptions import PreventUpdate
from geopy.distance import geodesic as GD
import dash_leaflet as dl
import plotly.graph_objects as go
import dash_html_components as html


radius_km=10
docker_fastapi_url = "http://fastapi-container:80"

url_cities = f"{docker_fastapi_url}/cities"
url_city = f"{docker_fastapi_url}/city/{{city}}"
url_itinerary = f"{docker_fastapi_url}/itinerary/{{city}}/{{activity}}"

response_cities = requests.get(url_cities)
cities_data = response_cities.json()

activities = [
    "Museums", "Theaters", "Historical", "Industrial/Urban", "Beaches", "Natural",
    "Religion", "Sport", "Tourist facilities", "Foods", "Shops", "Archeology",
    "Accommodations", "Amusement"
]

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1('Welcome to the Spain Itinerary Holiday App', style={'textAlign': 'center', 'color': 'mediumturquoise'}),
        html.Div(
            [
                html.Button('Let\'s travel', id='start-button', n_clicks=0, style={'display': 'block', 'margin': 'auto'})
            ],
            style={'width': '30%', 'margin': 'auto', 'padding-top': '20px'}
        ),
        html.Div(id='city-selection', style={'display': 'none'}, children=[
            html.H3('Which city would you like to visit?', style={'textAlign': 'center', 'color': 'grey'}),
            html.Div(
                dcc.Dropdown(
                    id="input_city",
                    options=cities_data,
                    value='select your city',
                    style={'width': '50%', 'margin': 'auto'}
                ),
                style={'text-align': 'center'}
            ),
            html.Button('Next', id='city-next-button', n_clicks=0, style={'display': 'block', 'margin': 'auto'})
        ]),
        html.Div(id='activity-selection', style={'display': 'none'}, children=[
            html.H3('Which activities would you like to do?', style={'textAlign': 'center', 'color': 'grey'}),
            html.Div(
                dcc.Dropdown(
                    id="input_activity",
                    options=[{'label': activity, 'value': activity} for activity in activities],
                    value=[],
                    multi=True,
                    style={'width': '50%', 'margin': 'auto'}
                ),
                style={'text-align': 'center'}
            ),
            html.Button('Next', id='activity-next-button', n_clicks=0, style={'display': 'block', 'margin': 'auto'})
        ]),
        html.Div(id='itinerary-display', style={'display': 'none'}, children=[
            html.H3('Proposed Itinerary', style={'textAlign': 'center', 'color': 'grey'}),
            dcc.Store(id='itinerary-info'),
            html.Div(
                [
                    dl.Map(id='map', center=[0, 0], zoom=1, style={'height': '600px', 'width':'800px'}, click_lat_lng=[None, None]),
                ],
                style={'width': '100%', 'margin': 'auto', 'padding-top': '20px'}
            ),
            html.Div(id='text-info',style={'margin-top': '20px', 'text-align': 'center'}),
            html.Button('Restart', id='restart-button', n_clicks=0, style={'textAlign':'center','display': 'block', 'margin': 'auto'})
        ])
    ],
    style={'background': 'white', 'height': '100vh'}
)

@app.callback(
    [
        dash.dependencies.Output('start-button', 'style'),
        dash.dependencies.Output('city-selection', 'style'),
        dash.dependencies.Output('activity-selection', 'style'),
        dash.dependencies.Output('itinerary-display', 'style'),
        dash.dependencies.Output('input_city', 'value'),
        dash.dependencies.Output('input_activity', 'value'),
        dash.dependencies.Output('itinerary-info', 'data'),
        dash.dependencies.Output('map', 'children'),
    ],
    [
        dash.dependencies.Input('start-button', 'n_clicks'),
        dash.dependencies.Input('city-next-button', 'n_clicks'),
        dash.dependencies.Input('activity-next-button', 'n_clicks'),
        dash.dependencies.Input('restart-button', 'n_clicks')
    ],
    [
        dash.dependencies.State('input_city', 'value'),
        dash.dependencies.State('input_activity', 'value')
    ]
)
def handle_button_clicks(
    start_clicks, city_next_clicks, activity_next_clicks, restart_clicks,
    city, activities
):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'start-button':
        return (
            {'display': 'none'},
            {'display': 'block'},
            {'display': 'none'},
            {'display': 'none'},
            'select your city',
            [],
            None,
            None
        )
    elif trigger_id == 'city-next-button':
        return (
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'block'},
            {'display': 'none'},
            city,
            [],
            None,
            None
        )
    elif trigger_id == 'activity-next-button':
        response_city = requests.get(url_city.format(city=city))
        city_data = response_city.json()

        itinerary_df = pd.DataFrame()
        for activity in activities:
            response_itinerary = requests.get(url_itinerary.format(city=city, activity=activity))
            itinerary = response_itinerary.json()
            itinerary_df = pd.concat([itinerary_df, pd.DataFrame(itinerary)])

        city_coordinates = (city_data['latitude'], city_data['longitude'])

        # Filter places within a certain radius around the city
        radius_km = 10
        itinerary_df['distance'] = itinerary_df.apply(
            lambda row: GD(city_coordinates, (row['placeLatitude'], row['placeLongitude'])).km,
            axis=1
        )
        itinerary_df = itinerary_df[itinerary_df['distance'] <= radius_km]

        itinerary_df = itinerary_df.sample(n=5)
        itinerary_df = itinerary_df.rename(columns={"placeLongitude": "longitude", "placeLatitude": "latitude"})

        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(
            lat=itinerary_df['latitude'],
            lon=itinerary_df['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=17,
                opacity=0.5
            ),
            text=itinerary_df['placeName']
        ))
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(
                    lat=city_data['latitude'],
                    lon=city_data['longitude']
                ),
                pitch=0,
                zoom=13
            )
        )
        fig.update_layout(height=600, width=800)

        itinerary_info = itinerary_df.to_dict('records')

        return (
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'block'},
            city,
            activities,
            itinerary_info,
            dcc.Graph(figure=fig)
        )
    elif trigger_id == 'restart-button':
        return (
            {'display': 'block'},
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'none'},
            'select your city',
            [],
            None,
            None
        )
    else:
        raise PreventUpdate


@app.callback(
    dash.dependencies.Output('text-info', 'children'),
    dash.dependencies.Input('map', 'click_lat_lng'),
    dash.dependencies.State('map', 'children'),
    dash.dependencies.Input('itinerary-info', 'data')
)
def display_place_info(lat_lng, map_children, itinerary_info):
    if map_children is not None:
        clicked_marker = None
        min_distance = float('inf')

        itinerary_df = pd.DataFrame(itinerary_info)

        for child in map_children:
            if isinstance(child, dl.Marker):
                marker_lat_lng = child.children[0].options['position']
                distance = GD(lat_lng, marker_lat_lng).km

                if distance < min_distance:
                    min_distance = distance
                    clicked_marker = child

        text_info = html.Div([
            html.H4('Place Information'),
            html.P('No place information available.')
        ])

        if not itinerary_df.empty:
            filtered_df = itinerary_df[(itinerary_df['distance'] <= radius_km) & (itinerary_df['image'].notnull())]

            if not filtered_df.empty:
                text_info = html.Div([
                    html.H4('Place Information'),
                    *[html.Div([
                        html.Img(src=row['image'], alt=row['placeName'], style={'width': '100px', 'height': '100px'}),
                        html.P(f'Place Name: {row["placeName"]}'),
                        html.P(f'Description: {row["description"]}' if row["description"] else 'No description available.'),
                        html.P(f'Rate: {row["rate"]}')
                    ]) for _, row in filtered_df.iterrows()]
                ])

        return text_info

    raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
