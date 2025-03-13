import pandas as pd
import re
from datetime import datetime
import dash
from dash import dcc, html, dash_table
import plotly.express as px
from dash.dependencies import Input, Output
import os

DEBUG=os.environ.get('DEBUG', False)
APP_PATH=os.environ.get('APP_PATH', None)

# Load CSV from URL
ghurl = "https://github.com/fivethirtyeight/data/tree/master/trump-2-poll-issue-questions"
url = "https://raw.githubusercontent.com/rojwilco/538-data/refs/heads/master/trump-2-poll-issue-questions/trump-poll-issue-questions.csv"
df = pd.read_csv(url)

# Function to parse date ranges
def parse_date_range(date_range):
    match = re.match(r"(\w{3})\. (\d+) - (?:(\w{3})\. )?(\d+)", date_range)
    if not match:
        return pd.NaT, pd.NaT

    start_month, start_day, end_month, end_day = match.groups()
    if not end_month:
        end_month = start_month

    current_year = datetime.today().year
    start_date = datetime.strptime(f"{start_month} {start_day} {current_year}", "%b %d %Y")
    end_date = datetime.strptime(f"{end_month} {end_day} {current_year}", "%b %d %Y")

    if end_date < start_date:
        end_date = end_date.replace(year=start_date.year + 1)

    return start_date, end_date

# Apply date parsing
df[['start_date', 'end_date']] = df['dates'].apply(lambda x: pd.Series(parse_date_range(x)))

# Convert percentages to float
df['yes'] = df['yes'].astype(float)
df['no'] = df['no'].astype(float)

# Aggregate by category and end date
df_grouped = df.groupby(["category", "end_date"], as_index=False).agg({"yes": "mean", "no": "mean", "net": "mean"})

# Aggregate by all categories
df_all = df.groupby("end_date", as_index=False).agg({"yes": "mean", "no": "mean", "net": "mean"})

# Summary sorted by net percentage
df_summary = df_grouped.groupby("category", as_index=False).agg({"yes": "mean", "no": "mean", "net": "mean"}).sort_values(by="net", ascending=False)

# Get min/max Net values for scaling the gradient
min_net = df_summary["net"].min()
max_net = df_summary["net"].max()

def get_net_color(value):
    """
    Returns an RGB color based on the 'net' value.
    - Positive values are intense green.
    - Negative values are intense red.
    - Values near zero remain closer to white but still noticeable.
    """
    import numpy as np

    # Normalize value to range (-1, 1)
    normalized = np.clip(value / 100, -1, 1)

    intensity = 250  # Increase this for stronger colors (Max: 255)
    base = 255  # White background

    if normalized > 0:  # Green shades
        red = base - int(normalized * intensity)  # Reduce red more aggressively
        green = base  # Keep green at max intensity
        blue = base - int(normalized * intensity)  # Reduce blue more aggressively
    else:  # Red shades
        red = base  # Keep red at max intensity
        green = base + int(normalized * intensity)  # Reduce green more aggressively
        blue = base + int(normalized * intensity)  # Reduce blue more aggressively

    return f'rgb({red},{green},{blue})'

# Create conditional formatting rules dynamically
style_data_conditional = [
    {
        "if": {"column_id": "net", "filter_query": f"{{net}} = {row['net']}"},
        "backgroundColor": get_net_color(row["net"]),
        "color": "black"
    }
    for _, row in df_summary.iterrows()
]

# set up app path if provided (for when running behind a reverse proxy path)
if APP_PATH:
    app_path = f"/{APP_PATH}/"
else: 
    app_path = None


# debug settings
if DEBUG:
    serve_locally=True
else:
    serve_locally=False

# Initialize Dash app
app = dash.Dash(__name__, requests_pathname_prefix=app_path, serve_locally=serve_locally)

app.title = "Trump Action Approval Trends"

app.layout = app.layout = html.Div(
    style={
        'fontFamily': 'Arial, sans-serif',
        'maxWidth': '900px',
        'margin': 'auto',
        'padding': '20px',
        'backgroundColor': '#f9f9f9',
        'borderRadius': '10px',
        'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)'
    },
    children=[
        html.H1("Trump Action Approval Trends", style={'textAlign': 'center', 'color': '#333'}),        
        html.H6(
            [
                "Data Source: ",
                html.A("FiveThirtyEight", href=ghurl, target="_blank")
            ],
            style={'textAlign': 'center', 'color': '#666'},
        ),
        # Data Table with Better Styling
        html.Div(
            style={'overflowX': 'auto'},
            children=[
                dash_table.DataTable(
                    id='data-table',
                    data=df_summary.to_dict('records'),
                    columns=[
                        {"name": "Category", "id": "category"},
                        {"name": "Yes %", "id": "yes", "type": "numeric", "format": dash_table.Format.Format(precision=3)},
                        {"name": "No %", "id": "no", "type": "numeric", "format": dash_table.Format.Format(precision=3)},
                        {"name": "Net %", "id": "net", "type": "numeric", "format": dash_table.Format.Format(precision=3)}
                    ],
                    style_table={'width': '100%'},
                    style_header={
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    },
                    style_data={
                        'backgroundColor': '#fff',
                        'color': '#333',
                        'border': '1px solid #ddd'
                    },
                    style_cell={'padding': '10px', 'textAlign': 'center'},
                    style_data_conditional=style_data_conditional
                )
            ]
        ),

        html.H3("Trend Over Time", style={'textAlign': 'center', 'marginTop': '30px'}),
        html.Label("Select Category:", style={'fontSize': '16px', 'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': cat, 'value': cat} for cat in df['category'].unique()],
            value='All',
            clearable=False,
            searchable=False,
            style={'marginBottom': '20px'}
        ),
        dcc.Graph(id='trend-graph', style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'}),
        html.H3("Questions for Selected Category", style={'textAlign': 'center', 'marginTop': '30px'}),
        html.Div(
            style={'overflowX': 'auto'},
            children=[
                dash_table.DataTable(
                    id='questions-table',
                    columns=[
                        {"name": "Question", "id": "question"},
                        {"name": "Dates", "id": "dates"},
                        {"name": "Yes %", "id": "yes"},
                        {"name": "No %", "id": "no"},
                        {"name": "Net %", "id": "net"}
                    ],
                    style_table={'width': '100%'},
                    style_header={
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    },
                    style_data={
                        'backgroundColor': '#fff',
                        'color': '#333',
                        'border': '1px solid #ddd'
                    },
                    style_cell={
                        'padding': '10px',
                        'textAlign': 'center',
                        'whiteSpace': 'normal'
                    }
                )
            ]
        )
    ]
)

# Callback to update graph
@app.callback(
    Output('trend-graph', 'figure'),
    Input('category-dropdown', 'value')
)
def update_graph(selected_category):
    if selected_category == 'All':
        filtered_df = df_all
    else:
        filtered_df = df_grouped[df_grouped['category'] == selected_category]
    fig = px.line(
        filtered_df,
        x="end_date",
        y=["yes", "no"],
        title=f"Poll Trend for {selected_category}",
        labels={"end_date": "Date", "value": "Percentage"},
        markers=True
    )
    fig.update_layout(
        template="plotly_white",
        legend_title_text="Response",
        xaxis_title="Date",
        yaxis_title="Percentage (%)",
        font=dict(size=14),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

@app.callback(
    Output('questions-table', 'data'),
    Output('questions-table', 'style_data_conditional'),
    Input('category-dropdown', 'value')
)
def update_questions_table(selected_category):
    if selected_category == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['category'] == selected_category].sort_values(by='end_date', ascending=True)
    data = filtered_df.to_dict('records')
    style_data_conditional = [
        {
            "if": {"column_id": "net", "filter_query": f"{{net}} = {row['net']}"},
            "backgroundColor": get_net_color(row["net"]),
            "color": "black"
        }
        for _, row in filtered_df.iterrows()
    ]
    return data, style_data_conditional

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=DEBUG)
