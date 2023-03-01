#file for ploly Dash app 

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go  
import pandas as pd
import numpy as np
import os
import json
import datetime
import time
import dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
# import dash.dependencies.Input as Input
# import dash.dependencies.Output as Output
from dash import Dash, dcc, html, Input, Output

PRODUCTIVITY_LIST = ['code-work', 'code-personal','mail','Teams','read-pdf']
app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])

app.layout = dbc.Container([
    dcc.Store(id='store', storage_type='session'),
    dcc.Store(id='store2', storage_type='session'),

    # reload button

    dbc.Row([
      
        dbc.Col(dbc.Button('Reload', id='re-button', color='primary', className='mr-1',), width=4),
        dbc.Col(dbc.Select(id='select') , width=4),
        dbc.Col(dbc.Button('Load', id='ld-button', color='primary', className='mr-1',), width=2),
        ]
    ),

    # Model with 2 graphs 
    dbc.Modal([
        dbc.ModalHeader("Stats for the day", id='modal-header'),
        dbc.ModalBody(children=[
            dcc.Graph(id='g-pie-day'),
            dcc.Graph(id='g-heat-day'),
        ]),
        dbc.ModalFooter(id='modal-footer'),
    ], id="modal", size='xl', is_open=False,
    ),

    dbc.Row( html.H2('Time spent per category pie + stacked'),),
    dbc.Row([
        dbc.Col(dcc.Graph(id='g-pie-all'), width=5),
        dbc.Col(dcc.Graph(id='g-heatmap-day'), width=5),
        ]),

    dbc.Row( html.H2('Time spent per line + bar'),),
    dbc.Row([
        dbc.Col(dcc.Graph(id='g-bar-stacked'), width=5),
        dbc.Col(dcc.Graph(id='g-line-prod'), width=5),
        ]),

    dbc.Row( html.H2('Time spent per category'),),
    dbc.Row([
        dbc.Col(dcc.Graph(id='g-heatmap-hour'), width=8),
        # dbc.Col(dcc.Graph(id='graph6'), width=5),
        ]),

    
    ],fluid=True,style={'padding-left': '150px', 'margin-left': '10px', 'backgroundColor': '#f9f9f9'})
def read_csv(df):
    df['Day'] = pd.to_datetime(df['Day'])

    # for each row read Tag col, read and remove the 'Graph' and ':' from the name
    df['Tag'] = df['Tag'].apply(lambda x: x.split(':')[1] if 'Graph' in x else x)
    df.head()

    #remove any 'unamtched' tags
    df = df[df['Tag'] != '(unmatched time)']
    # convert time from string to datetime then get number of hours


    df['Time'] = pd.to_timedelta(df['Time'])
    return df

def modify_time_per_tag_per_day(df,tag_to_modify,day_to_modify,time_to_adjust):
    """
    Modify the time used for a specific tag in a specific day
        :param df: dataframe with the data
        :param tag_to_modify: tag to modify
        :param day_to_modify: day to modify
        :param time_to_adjust: time to add or subtract
        :return: dataframe with the modified time

    Example:
            tag_to_modify = 'code-work'
            time_to_adjust = '08:00:00'
            day_to_modify = pd.to_datetime('2023-01-25')

    """
    # Find the row with the specified tag and modify the time used
    tag_row = df.loc[(df['Tag'] == tag_to_modify) & (df['Day'] == day_to_modify)]
    tag_row['Time'] = pd.to_timedelta(tag_row['Time']) + pd.to_timedelta(time_to_adjust)
    df.loc[(df['Tag'] == tag_to_modify) & (df['Day'] == day_to_modify), 'Time'] = tag_row['Time']
    # # Calculate the total time and percentage for all tags in day_to_modify
    total_time = df.loc[df['Day'] == day_to_modify]['Time'].sum()
    df.loc[df['Day'] == day_to_modify, 'Percentage'] = df.loc[df['Day'] == day_to_modify]['Time'] / total_time * 100
    return df

@app.callback(
    Output('store','data'),Output('store2','data'),Input('re-button','n_clicks'),)

def update_graph(n_clicks):
    os.system('update2.cmd')
    # read csv
    df_a = read_csv(pd.read_csv('daily.csv'))
    df = read_csv(pd.read_csv('daily_archive.csv'))
    df = pd.concat([df, df_a[df_a['Day'] == df_a['Day'].max()]])
    del df_a
    print(df.tail())
    # group by Tag and Day
    # df = df.groupby(['Tag', 'Day']).sum().reset_index()
    df['Day of the week'] = df['Day'].dt.day_name()
    df['Productivity'] = df['Tag'].apply(lambda x: 1 if x in PRODUCTIVITY_LIST else 0)
    



    df2 = pd.read_csv('minute.csv')
    df2['Minute'] = pd.to_datetime(df2['Minute'])

    # for each row read Tag col, read and remove the 'Graph' and ':' from the name
    df2['Tag'] = df2['Tag'].apply(lambda x: x.split(':')[1] if 'Graph' in x else x)

    #remove any 'unamtched' tags
    df2 = df2[df2['Tag'] != '(unmatched time)']

    # group by Tag and Day
    df2 = df2.groupby(['Tag', 'Minute']).sum().reset_index()

    df2['Hour of the day'] = df2['Minute'].dt.hour

    return df.to_json(date_format='iso' ),df2.to_json(date_format='iso')

@app.callback(
    Output('select', 'options'),
    Input('store', 'data'))
def update_options(data):
    df = pd.read_json(data)
    # read the 'Day' col as a datetime object
    df['Day'] = pd.to_datetime(df['Day'])
    # strftime as 1st of Jan 2020
    return [{'label': i.strftime("%d %B  (%A)"), 'value': i} for i in df['Day']]
    # unique 
    
@app.callback(
    Output('g-pie-all', 'figure'),
    Input('store', 'data'))
def update_graph1(data):
    df = pd.read_json(data)
    # take pie percent from the 'Percentage' col
    fig = px.pie(df, values='Percentage', names='Tag', title='Time spent on each tag')

    # names on the pie chart
    fig.update_traces(textposition='inside', textinfo='percent+label')
    # legend on bottom
    fig.update_layout(legend=dict(

        orientation="v",
        yanchor="bottom",
        y=1.02,
        x=1
    ))
    return fig
    
@app.callback(
    Output('g-heatmap-day', 'figure'),
    Input('store', 'data'))
def update_graph2(data):
    df = pd.read_json(data)
    df_ = df.groupby(['Tag', 'Day of the week']).sum().reset_index()

# pivot the table
    df_ = df_.pivot(columns='Day of the week', index='Tag', values='Percentage')
    # order the columns according to the day of the week
    df_ = df_[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]


    # plot the heatmap
    fig = go.Figure(data=go.Heatmap(
                        z=df_.values,
                            x=df_.columns,

                            y=df_.index,
                            colorscale='viridis'))
    # reorder x axis
    fig.update_layout(title='Time spent per tag per day of the week') 



    # plot
    return fig

@app.callback(
    Output('g-bar-stacked', 'figure'),
    Input('store', 'data'))
def update_graph3(data):
    df = pd.read_json(data)
    # pivot the table
    df_ = df.pivot(index='Day', columns='Tag', values='Percentage')
    # plot the bar chart
    fig = go.Figure(data=[go.Bar(name=col, x=df_.index, y=df_[col]) for col in df_.columns])

    # stacked bats
    fig.update_layout(barmode='stack')
    #add x as day
    fig.update_layout(xaxis_tickformat = '%d %B (%a)')
    # show all x ticks
    fig.update_xaxes(nticks=15)
    #add title
    fig.update_layout(title_text='Time spent on each tag on each day')
    # plot
    return fig

@app.callback(
    Output('g-line-prod', 'figure'),
    Input('store', 'data'))
def update_graph4(data):

    df = pd.read_json(data)

    # get sum of percentage for all productivity tags for each day
    df_ = df.groupby(['Day','Tag']).sum().reset_index()
    # sum of productivity tags
    df_ = df_[df_['Tag'].isin(PRODUCTIVITY_LIST)].groupby(['Day']).sum().reset_index()

    # plot the bar chart
    fig = go.Figure(data=[go.Line(name='Percentage', x=df_['Day'], y=df_['Percentage'])])
    # add x as day
    fig.update_layout(xaxis_tickformat = '%d %B (%a)')
    # show all x ticks
    fig.update_xaxes(nticks=15)
    # add title
    fig.update_layout(title_text='Productivity per day')

    # plot  
    return fig

@app.callback(
    Output('g-heatmap-hour', 'figure'),
    Input('store2', 'data'))
def update_graph5(data):
    df = pd.read_json(data)

    df_ = df.groupby(['Tag', 'Hour of the day']).count().reset_index()
    # pivot the table
    df_ = df_.pivot(index='Tag', columns='Hour of the day', values='Percentage')

    # plot the heatmap horizontally
    fig = go.Figure(data=go.Heatmap(
                            z=df_.values,
                            x=df_.columns,
                            y=df_.index,
                            colorscale='viridis'))
    #title
    fig.update_layout(title_text='Tag vs Hour of the day') 

    # plot
    return fig

@app.callback(
    Output('g-pie-day', 'figure'),
    Output('g-heat-day', 'figure'),
    Output('Modal-header', 'children'),
    Output('Modal-body', 'children'),
    Output('Modal', 'is_open'),
    Input('ld-button', 'n_clicks'),

)
def update_graph6(n_clicks):
    return fig, fig2, 'Modal Header', 'Modal Body', True

if __name__ == '__main__':
    app.run_server(debug=True)


   #Add manual add to minuaTe csv using an extra csv file that has dates + categories of extra time spent 
   #then combine the two csv files and then run the code above  