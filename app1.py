import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from dash.exceptions import PreventUpdate
from flask_caching import Cache

# Initialize caching to store geocoding results
cache = Cache()
CACHE_TIMEOUT = 60 * 60  # 1 hour

# Load sample data
df = pd.read_csv("data/providers.csv")

# Geocoder with caching
geolocator = Nominatim(user_agent="geoaccess_tool")

@cache.memoize(timeout=CACHE_TIMEOUT)
def geocode_address(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        pass
    return None

# Create Dash app with a modern Bootstrap theme and Font Awesome for icons
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
], suppress_callback_exceptions=True)
app.title = "HMO Provider Search Tool"

# Initialize caching
cache.init_app(app.server)

# Custom CSS for additional styling
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #f0f4f8;
                font-family: 'Roboto', sans-serif;
                color: #333333;
                margin: 0;
                padding: 0;
            }
            .card-header {
                background-color: #ffffff;
                border-bottom: none;
                font-weight: 500;
                font-size: 1.1rem;
            }
            .card {
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: none;
                border-radius: 12px;
                background-color: #ffffff;
            }
            .slider-label {
                margin-bottom: 10px;
                font-weight: 500;
            }
            .map-container {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                height: 600px;
                width: 100%;
            }
            .table-container {
                background-color: #ffffff;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                margin-bottom: 30px;
            }
            .navbar {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                border-radius: 12px;
            }
            .dbc-tabs .nav-link.active {
                background-color: #0d6efd;
                color: white !important;
                border-radius: 8px 8px 0 0;
                box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
                transition: background-color 0.3s, color 0.3s, box-shadow 0.3s;
            }
            .dbc-tabs .nav-link {
                color: #0d6efd !important;
                border-radius: 8px 8px 0 0;
                margin-right: 5px;
                transition: background-color 0.3s, color 0.3s;
                background-color: #e6f0ff;
            }
            .dbc-tabs .nav-link:hover {
                background-color: #cce0ff;
                color: #0b5ed7 !important;
            }
            .sidebar {
                padding: 20px;
            }
            .btn-primary {
                background-color: #0d6efd;
                border-color: #0b5ed7;
                font-weight: 500;
            }
            .btn-secondary {
                background-color: #6c757d;
                border-color: #6c757d;
                font-weight: 500;
            }
            .btn-primary:hover {
                background-color: #0b5ed7;
                border-color: #0a58ca;
            }
            .btn-secondary:hover {
                background-color: #5a6268;
                border-color: #545b62;
            }
            /* Loading Indicators */
            .loading-indicator {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
            /* Responsive adjustments */
            @media (max-width: 767px) {
                .map-container {
                    height: 300px;
                }
                .sidebar {
                    padding: 10px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Function to create filters for Tab 1 with Enhanced Design
def create_filters_tab1():
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    html.Span([html.I(className="fa fa-filter mr-2"), "Filters"]),
                    id="collapse-tab1-button",
                    color="primary",
                    n_clicks=0,
                    style={"width": "100%", "textAlign": "left", "fontWeight": "500", "fontSize": "1rem"}
                )
            ),
            dbc.Collapse(
                dbc.CardBody([
                    dbc.Form(
                        [
                            # County Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("County"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-map-marker-alt")),
                                        dcc.Dropdown(
                                            options=[{"label": c, "value": c} for c in sorted(df["County"].unique())],
                                            id="filter-county",
                                            multi=True,
                                            placeholder="Select County",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Market Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Market"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-industry")),
                                        dcc.Dropdown(
                                            options=[{"label": m, "value": m} for m in sorted(df["Market"].unique())],
                                            id="filter-market",
                                            multi=True,
                                            placeholder="Select Market",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Specialty Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Specialty"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-user-md")),
                                        dcc.Dropdown(
                                            options=[{"label": s, "value": s} for s in sorted(df["Specialty"].unique())],
                                            id="filter-specialty",
                                            multi=True,
                                            placeholder="Select Specialty",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # City Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("City"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-city")),
                                        dcc.Dropdown(
                                            options=[{"label": c, "value": c} for c in sorted(df["City"].unique())],
                                            id="filter-city",
                                            multi=True,
                                            placeholder="Select City",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Language Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Language"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-language")),
                                        dcc.Dropdown(
                                            options=[{"label": l, "value": l} for l in sorted(df["Language"].unique())],
                                            id="filter-language",
                                            multi=True,
                                            placeholder="Select Language",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Clear All Filters Button
                            dbc.Button(
                                "Clear All Filters",
                                id="clear-filters-tab1",
                                color="secondary",
                                className="mt-3 w-100",
                                size="md"
                            ),
                        ]
                    )
                ]),
                id="collapse-tab1",
                is_open=True,
            )
        ],
        className="mb-4 sidebar"
    )

# Function to create filters for Tab 2 with Enhanced Design and "Calculate Radius" Button
def create_filters_tab2():
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    html.Span([html.I(className="fa fa-filter mr-2"), "Address & Filters"]),
                    id="collapse-tab2-button",
                    color="success",
                    n_clicks=0,
                    style={"width": "100%", "textAlign": "left", "fontWeight": "500", "fontSize": "1rem"}
                )
            ),
            dbc.Collapse(
                dbc.CardBody([
                    dbc.Form(
                        [
                            # Address
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Address"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-home")),
                                        dbc.Input(
                                            id="address1",
                                            type="text",
                                            placeholder="Street Address",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # City
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("City"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-city")),
                                        dbc.Input(
                                            id="geo-city",
                                            type="text",
                                            placeholder="City",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # State
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("State"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-flag")),
                                        dbc.Input(
                                            id="state",
                                            type="text",
                                            placeholder="State",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Zip Code
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Zip Code"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-mail-bulk")),
                                        dbc.Input(
                                            id="zip_code",
                                            type="text",
                                            placeholder="Zip Code",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Radius 1 and Radius 2
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Radius 1 (miles)"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-ruler")),
                                        dbc.Input(
                                            id="radius1",
                                            type="number",
                                            value=5,
                                            min=1,
                                            step=1,
                                            style={"flex": "1"}
                                        )
                                    ])
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Radius 2 (miles)"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-ruler")),
                                        dbc.Input(
                                            id="radius2",
                                            type="number",
                                            value=10,
                                            min=1,
                                            step=1,
                                            style={"flex": "1"}
                                        )
                                    ])
                                ], width=6),
                            ], className="mb-4"),
                            
                            html.Hr(),
                            
                            # County Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("County"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-map-marker-alt")),
                                        dcc.Dropdown(
                                            options=[{"label": c, "value": c} for c in sorted(df["County"].unique())],
                                            id="filter2-county",
                                            multi=True,
                                            placeholder="Select County",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Market Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Market"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-industry")),
                                        dcc.Dropdown(
                                            options=[{"label": m, "value": m} for m in sorted(df["Market"].unique())],
                                            id="filter2-market",
                                            multi=True,
                                            placeholder="Select Market",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Specialty Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Specialty"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-user-md")),
                                        dcc.Dropdown(
                                            options=[{"label": s, "value": s} for s in sorted(df["Specialty"].unique())],
                                            id="filter2-specialty",
                                            multi=True,
                                            placeholder="Select Specialty",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # City Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("City"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-city")),
                                        dcc.Dropdown(
                                            options=[{"label": c, "value": c} for c in sorted(df["City"].unique())],
                                            id="filter2-city",
                                            multi=True,
                                            placeholder="Select City",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Language Filter
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Language"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="fa fa-language")),
                                        dcc.Dropdown(
                                            options=[{"label": l, "value": l} for l in sorted(df["Language"].unique())],
                                            id="filter2-language",
                                            multi=True,
                                            placeholder="Select Language",
                                            style={"flex": "1"}
                                        )
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            # Calculate Radius Button
                            dbc.Button(
                                "Calculate Radius",
                                id="calculate-radius-button",
                                color="primary",
                                className="mt-3 w-100",
                                size="md"
                            ),
                            
                            # Clear All Filters Button
                            dbc.Button(
                                "Clear All Filters",
                                id="clear-filters-tab2",
                                color="secondary",
                                className="mt-3 w-100",
                                size="md",
                                style={"marginTop": "10px"}
                            ),
                        ]
                    )
                ]),
                id="collapse-tab2",
                is_open=True,
            )
        ],
        className="mb-4 sidebar"
    )

# Function to create CircleMarkers with popups and custom icons
def create_dot_markers(data, zoom, dot_size):
    """
    Create CircleMarkers with conditional coloring and dynamic sizing.
    - data: Filtered DataFrame
    - zoom: Current zoom level of the map
    - dot_size: User-controlled size multiplier from the slider
    """
    base_size = dot_size  # From slider
    radius = max(2, base_size + (zoom - 10)*0.3)
    markers = []
    for _, row in data.iterrows():
        specialty = str(row.get("Specialty", "")).strip().upper()
        color = "#dc3545" if specialty == "PCP" else "#0d6efd"
        # Popup content
        popup_content = [
            html.H5(row.get('ProviderName', 'N/A'), style={"margin-bottom": "5px"}),
            html.P(f"Provider ID: {row.get('ProviderID', 'N/A')}", style={"margin": "0"}),
            html.P(f"Vendor ID: {row.get('VendorID', 'N/A')}", style={"margin": "0"}),
            html.P(f"PCN ID: {row.get('PCNID', 'N/A')}", style={"margin": "0"}),
            html.P(f"Address: {row.get('Address', 'N/A')}", style={"margin": "0"})
        ]
        markers.append(
            dl.CircleMarker(
                center=(row['Latitude'], row['Longitude']),
                radius=radius,
                stroke=True,
                color="#343a40",
                weight=1,
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                children=[dl.Popup(popup_content)],
                interactive=True
            )
        )
    return markers

# Tab 1 layout with Enhanced Filters
tab1_layout = dbc.Container([
    dbc.Row([
        # Sidebar for Filters
        dbc.Col(
            create_filters_tab1(),
            width=3,
            id="sidebar-tab1",
            style={"position": "sticky", "top": "20px", "height": "fit-content"}
        ),
        # Main Content
        dbc.Col(
            html.Div([
                # Map Controls with Tooltips
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Map Style", className="slider-label"),
                        dcc.Dropdown(
                            id="map-style-dropdown",
                            options=[
                                {"label": "OpenStreetMap Standard", "value": "osm"},
                                {"label": "Esri World Imagery", "value": "world_imagery"},
                                {"label": "CartoDB Positron", "value": "positron"},
                                {"label": "Stamen Terrain", "value": "terrain"}
                            ],
                            value="osm",
                            clearable=False,
                            style={"width": "100%"},
                            placeholder="Select Map Style"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            dbc.Label("Dot Size", className="slider-label"),
                            dcc.Slider(
                                id="dot-size-slider1",
                                min=1,
                                max=5,
                                step=0.5,
                                value=2,
                                marks={i: str(i) for i in range(1, 6)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                updatemode='drag',
                                vertical=False,
                            ),
                        ], style={"padding": "20px 20px 0 20px"})
                    ], width=8)
                ], className="mb-4"),
                # Interactive Map
                html.Div([
                    dl.Map([
                        dl.TileLayer(id="base-tile", url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                        dl.LayerGroup(id="provider-markers"),
                    ], id="provider-map", className="map-container", center=(df['Latitude'].mean(), df['Longitude'].mean()), zoom=6)
                ], className="map-container"),
                # Loading Indicator for Map
                dcc.Loading(
                    id="loading-map-tab1",
                    type="default",
                    children=html.Div(id="map-loading-output")
                )
            ], style={"position": "relative"})
            , width=9
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Provider Data", className="mb-0")),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id="provider-table",
                            columns=[{"name": col, "id": col} for col in df.columns],
                            data=df.to_dict("records"),
                            style_table={"overflowX": "auto"},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'font-family': 'Roboto, sans-serif',
                                'font-size': '14px'
                            },
                            style_header={
                                'backgroundColor': '#0d6efd',
                                'color': 'white',
                                'fontWeight': '500',
                                'fontSize': '16px'
                            },
                            page_size=10,
                            sort_action="native",
                            filter_action='none',
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }
                            ],
                            export_format="csv",
                            export_headers="display",
                            merge_duplicate_headers=True,
                            style_as_list_view=True,
                        )
                    )
                ],
                className="table-container"
            ), width=12
        )
    ]),
    # Loading Indicator for Table
    dcc.Loading(
        id="loading-table-tab1",
        type="default",
        children=html.Div(id="table-loading-output")
    )
], fluid=True)

# Tab 2 layout with Enhanced Filters and "Calculate Radius" Button
tab2_layout = dbc.Container([
    dbc.Row([
        # Sidebar for Address Inputs and Filters
        dbc.Col(
            create_filters_tab2(),
            width=3,
            id="sidebar-tab2",
            style={"position": "sticky", "top": "20px", "height": "fit-content"}
        ),
        # Main Content
        dbc.Col(
            html.Div([
                # Map Controls with Tooltips
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Map Style", className="slider-label"),
                        dcc.Dropdown(
                            id="geoaccess-map-style-dropdown",
                            options=[
                                {"label": "OpenStreetMap Standard", "value": "osm"},
                                {"label": "Esri World Imagery", "value": "world_imagery"},
                                {"label": "CartoDB Positron", "value": "positron"},
                                {"label": "Stamen Terrain", "value": "terrain"}
                            ],
                            value="osm",
                            clearable=False,
                            style={"width": "100%"},
                            placeholder="Select Map Style"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            dbc.Label("Dot Size", className="slider-label"),
                            dcc.Slider(
                                id="dot-size-slider2",
                                min=1,
                                max=5,
                                step=0.5,
                                value=2,
                                marks={i: str(i) for i in range(1, 6)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                updatemode='drag',
                                vertical=False,
                            ),
                        ], style={"padding": "20px 20px 0 20px"})
                    ], width=8)
                ], className="mb-4"),
                # Interactive Map with Correct Layer Order
                html.Div([
                    dl.Map([
                        dl.TileLayer(id="base-tile-geoaccess", url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                        dl.LayerGroup(id="geoaccess-circles"),   # Add circles first
                        dl.LayerGroup(id="geoaccess-markers")    # Add markers after
                    ],
                    id="geoaccess-map",
                    className="map-container",
                    center=(df['Latitude'].mean(), df['Longitude'].mean()),
                    zoom=6)
                ], className="map-container"),
                # Loading Indicator for Map
                dcc.Loading(
                    id="loading-map-tab2",
                    type="default",
                    children=html.Div(id="map-loading-output-tab2")
                )
            ], style={"position": "relative"})
            , width=9
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Geo-Access Provider Data", className="mb-0")),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id="geo-provider-table",
                            columns=[{"name": col, "id": col} for col in df.columns] + [{"name": "Distance (Miles)", "id": "Distance"}],
                            data=[],
                            style_table={"overflowX": "auto"},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'font-family': 'Roboto, sans-serif',
                                'font-size': '14px'
                            },
                            style_header={
                                'backgroundColor': '#28a745',
                                'color': 'white',
                                'fontWeight': '500',
                                'fontSize': '16px'
                            },
                            page_size=10,
                            sort_action="native",
                            filter_action='none',
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }
                            ],
                            export_format="csv",
                            export_headers="display",
                            merge_duplicate_headers=True,
                            style_as_list_view=True,
                        )
                    )
                ],
                className="table-container"
            ), width=12
        )
    ]),
    # Loading Indicator for Table
    dcc.Loading(
        id="loading-table-tab2",
        type="default",
        children=html.Div(id="table-loading-output-tab2")
    )
], fluid=True)

# App layout with tabs and navbar
app.layout = dbc.Container([
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand([
                html.I(className="fa fa-hospital mr-2", style={"fontSize": "1.5rem", "color": "white"}),
                html.Span("Provider Network Search Tool", style={"fontSize": "1.5rem", "color": "white", "fontWeight": "700"})
            ], className="d-flex align-items-center"),
        ]),
        color="#0d6efd",
        dark=True,
        className="mb-4 navbar",
        style={"borderRadius": "12px"}
    ),
    dbc.Tabs(id="tabs", active_tab="tab-1", children=[
        dbc.Tab(label="Provider Search Tool", tab_id="tab-1"),
        dbc.Tab(label="Geo-Access Reporting Tool", tab_id="tab-2"),
    ], className="mb-4"),
    html.Div(id="tab-content", className="p-4")
], fluid=True)

# Callback to toggle Accordion in Tab 1
@app.callback(
    Output("collapse-tab1", "is_open"),
    Input("collapse-tab1-button", "n_clicks"),
    State("collapse-tab1", "is_open"),
)
def toggle_collapse_tab1(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback to toggle Accordion in Tab 2
@app.callback(
    Output("collapse-tab2", "is_open"),
    Input("collapse-tab2-button", "n_clicks"),
    State("collapse-tab2", "is_open"),
)
def toggle_collapse_tab2(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback to render the active tab's content
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "tab-1":
        return tab1_layout
    elif active_tab == "tab-2":
        return tab2_layout
    else:
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {active_tab} was not recognised..."),
            ]
        )

# Callback for Tab 1: Update Provider Table and Markers
@app.callback(
    [
        Output("provider-table", "data"),
        Output("provider-markers", "children"),
        Output("base-tile", "url"),
        Output("provider-map", "center"),
        Output("provider-map", "zoom")
    ],
    [
        Input("filter-county", "value"),
        Input("filter-market", "value"),
        Input("filter-specialty", "value"),
        Input("filter-city", "value"),
        Input("filter-language", "value"),
        Input("provider-map", "zoom"),
        Input("dot-size-slider1", "value"),
        Input("map-style-dropdown", "value"),
        Input("tabs", "active_tab")
    ]
)
def update_provider_tab(county, market, specialty, city, language, zoom, dot_size, selected_style, active_tab):
    if active_tab != "tab-1":
        raise PreventUpdate
    
    if zoom is None:
        zoom = 6
    filtered = df.copy()
    if county:
        filtered = filtered[filtered["County"].isin(county)]
    if market:
        filtered = filtered[filtered["Market"].isin(market)]
    if specialty:
        filtered = filtered[filtered["Specialty"].isin(specialty)]
    if city:
        filtered = filtered[filtered["City"].isin(city)]
    if language:
        filtered = filtered[filtered["Language"].isin(language)]

    markers = create_dot_markers(filtered, zoom, dot_size)

    # Update tile layer URL based on selected style
    tile_urls = {
        "osm": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "world_imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png"
    }
    tile_url = tile_urls.get(selected_style, tile_urls["osm"])

    # Adjust map center based on filtered data
    if not filtered.empty:
        mean_lat = filtered["Latitude"].mean()
        mean_lon = filtered["Longitude"].mean()
        map_center = (mean_lat, mean_lon)
        map_zoom = zoom
    else:
        map_center = (df['Latitude'].mean(), df['Longitude'].mean())
        map_zoom = 6

    return filtered.to_dict("records"), markers, tile_url, map_center, map_zoom

# Callback to clear all filters in Tab 1
@app.callback(
    [
        Output("filter-county", "value"),
        Output("filter-market", "value"),
        Output("filter-specialty", "value"),
        Output("filter-city", "value"),
        Output("filter-language", "value"),
    ],
    Input("clear-filters-tab1", "n_clicks"),
    prevent_initial_call=True
)
def clear_all_filters_tab1(n_clicks):
    return [None, None, None, None, None]

# Callback to clear all filters in Tab 2
@app.callback(
    [
        Output("address1", "value"),
        Output("geo-city", "value"),
        Output("state", "value"),
        Output("zip_code", "value"),
        Output("radius1", "value"),
        Output("radius2", "value"),
        Output("filter2-county", "value"),
        Output("filter2-market", "value"),
        Output("filter2-specialty", "value"),
        Output("filter2-city", "value"),
        Output("filter2-language", "value"),
    ],
    Input("clear-filters-tab2", "n_clicks"),
    prevent_initial_call=True
)
def clear_all_filters_tab2(n_clicks):
    return [None, None, None, None, 5, 10, None, None, None, None, None]

# Callback for Tab 2: Update Geo-Access Markers, Circles, Table, Tile URL, Center, and Zoom on Button Click or Slider Change
@app.callback(
    [
        Output("geoaccess-markers", "children"),
        Output("geoaccess-circles", "children"),
        Output("geo-provider-table", "data"),
        Output("base-tile-geoaccess", "url"),
        Output("geoaccess-map", "center"),
        Output("geoaccess-map", "zoom")
    ],
    [
        Input("calculate-radius-button", "n_clicks"),
        Input("dot-size-slider2", "value"),
        Input("geoaccess-map-style-dropdown", "value"),
        Input("tabs", "active_tab")
    ],
    [
        State("address1", "value"),
        State("geo-city", "value"),
        State("state", "value"),
        State("zip_code", "value"),
        State("radius1", "value"),
        State("radius2", "value"),
        State("filter2-county", "value"),
        State("filter2-market", "value"),
        State("filter2-specialty", "value"),
        State("filter2-city", "value"),
        State("filter2-language", "value"),
        State("geoaccess-map", "zoom")
    ],
)
def update_geo_access(n_clicks, dot_size, selected_style, active_tab, address1, geo_city, state_input, zip_code,
                      radius1, radius2, county, market, specialty, filter_city, language, zoom):
    if active_tab != "tab-2":
        raise PreventUpdate

    # Update tile layer URL based on selected style
    tile_urls = {
        "osm": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "world_imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png"
    }
    tile_url = tile_urls.get(selected_style, tile_urls["osm"])

    if zoom is None:
        zoom = 6

    # Default to all providers
    all_markers = create_dot_markers(df, zoom, dot_size)
    circles = []
    table_data = []
    map_center = (df['Latitude'].mean(), df['Longitude'].mean())
    map_zoom = zoom

    # Determine if the callback was triggered by the button or slider/map style/tab change
    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if triggered == "calculate-radius-button" and n_clicks:
        # User clicked the Calculate Radius button
        parts = [address1, geo_city, state_input, zip_code]
        full_address = ", ".join([p.strip() for p in parts if p and p.strip()])

        user_coords = None
        if full_address:
            user_coords = geocode_address(full_address)

        radii = [r for r in [radius1, radius2] if r]
        filtered = df.copy()

        # Radius filtering first
        if user_coords and radii:
            filtered = filtered[filtered.apply(
                lambda row: any(
                    geodesic(user_coords, (row["Latitude"], row["Longitude"])).miles <= r
                    for r in radii
                ),
                axis=1
            )]

            # Additional filters after radius filtering
            if county:
                filtered = filtered[filtered["County"].isin(county)]
            if market:
                filtered = filtered[filtered["Market"].isin(market)]
            if specialty:
                filtered = filtered[filtered["Specialty"].isin(specialty)]
            if filter_city:
                filtered = filtered[filtered["City"].isin(filter_city)]
            if language:
                filtered = filtered[filtered["Language"].isin(language)]

            # Compute distances
            if not filtered.empty and user_coords:
                distances = filtered.apply(
                    lambda row: round(geodesic(user_coords, (row["Latitude"], row["Longitude"])).miles, 2),
                    axis=1
                )
                filtered = filtered.copy()
                filtered["Distance"] = distances
                filtered = filtered.sort_values(by="Distance", ascending=True)
                table_data = filtered.to_dict("records")
            else:
                filtered = filtered.copy()
                filtered["Distance"] = None
                table_data = filtered.to_dict("records")

            markers = create_dot_markers(filtered, zoom, dot_size)

            # Create circles for each radius
            if user_coords and radii:
                colors = ["#dc3545", "#0d6efd"]
                for i, r in enumerate(radii):
                    circles.append(
                        dl.Circle(
                            center=user_coords,
                            radius=r * 1609.34,  # Convert miles to meters
                            color=colors[i % len(colors)],
                            fill=True,
                            fillColor=colors[i % len(colors)],
                            fillOpacity=0.2,
                            weight=2
                        )
                    )
                map_center = user_coords
                map_zoom = zoom

            return markers, circles, table_data, tile_url, map_center, map_zoom

    elif triggered in ["dot-size-slider2", "geoaccess-map-style-dropdown", "tabs"] and active_tab == "tab-2":
        # User adjusted the dot size slider, changed map style, or switched to Tab 2
        markers = create_dot_markers(df, zoom, dot_size)
        return markers, circles, df.to_dict("records"), tile_url, map_center, map_zoom

    # When the tab is switched to Tab 2, show all providers
    if triggered == "tabs" and active_tab == "tab-2":
        return all_markers, circles, df.to_dict("records"), tile_url, map_center, map_zoom

    return all_markers, circles, df.to_dict("records"), tile_url, map_center, map_zoom

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
