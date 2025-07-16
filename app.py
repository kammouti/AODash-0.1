from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
# from database import engine, load_total_production
from database import engine
from sqlalchemy import text
import plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import os
import serial
from collections import defaultdict
import json
import random
import plotly.io as pio


DAY_WORK_TIME = 480
BREAK_TIME = 20
BREAK_TIME_NUMBER = 2

GRAPHS_FONT = 'Calibri'

SHIFT_SCHEDULE = {
    "Night": (22, 6),  # 10:00 PM - 06:00 AM (spans midnight)
    "Morning": (6, 14),  # 06:00 AM - 02:00 PM
    "Afternoon": (14, 22)  # 02:00 PM - 10:00 PM
}

app = Flask(__name__)

# load the secret key for the session use/ need to move .env file to get ignore
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
db_pwd = os.getenv("DB_PWD")


# # life time of a session
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)

# to delete session after closing the browser
app.config['SESSION_PERMANENT'] = False





def get_current_shift():
    """Returns the current shift based on time"""
    current_hour = datetime.now().hour  # Get the current hour (0-23)

    for shift, (start, end) in SHIFT_SCHEDULE.items():
        if start < end:  # Regular shift (same day)
            if start <= current_hour < end:
                return shift
        else:  # Night shift (spans midnight)
            if current_hour >= start or current_hour < end:
                return shift

        # if start <= current_hour < end or (start < end and current_hour >= start or current_hour < end):  # Regular shift (same day)
        #     return shift

    return None

def generate_gauge_chart(data):
    if 0<= data <55:
        gauge_color="#E1B8A8"
    elif 55 <= data <85:
        gauge_color="#C19E67"
    elif data >= 85:
        gauge_color="#84B484"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=data,
        number={'suffix': "%", 'valueformat': '.0f'},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={'axis': {'range': [None, 100]},
            'bar': {'color': gauge_color},
            'steps' : [
                 {'range': [0, 85], 'color': "#F3F1F3"},
                 {'range': [85, 100], 'color': "#F3F1F3"}],
            'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 1, 'value': 85}}

    ))
    fig.update_layout(margin=dict(t=30, b=30, l=30, r=30),
            font=dict(
            family=GRAPHS_FONT,
            color="#455364",
            size=14
        )
        )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='300px')

    return chart_html

def generate_pie_chart(dura, rem):
    labels = ['Actual (min)', 'Remaining (min)']
    values = [dura, rem]
    colors = ['67AFE1', 'F3F1F3']
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='value', marker=dict(colors=colors, line=dict(color='#000000', width=1)))])
    fig.update_layout(margin=dict(t=30, b=30, l=30, r=30),
            font=dict(
            family=GRAPHS_FONT,
            color="#455364",
            size=14
        )
        )
    fig.update_traces(textfont_size=20)
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='300px',)

    return chart_html

def generate_cycles_chart(list_total_cycle, cycles_names):
    labels = cycles_names
    colors=[]
    values = list_total_cycle
    random_color = ['#67AFE1', '#C19E67', '#99ABA5', '#313E3C', '#879CBC', '#83624F', '#455364', '#F3F1F3', '#E1B8A8', '#F341F3', '#A1B8A8', '#F341F3', '#A1B8A8', '#84E484']
    # Define a list of colors for the bars
    # i=1
    # for _ in list_total_cycle:
    #     colors.append(random.choice(random_color))
    #     labels.append(f"Cycle{i}")
    #     i+=1

    for i in range(1, len(list_total_cycle)):
        colors.append(random_color[i])
        # labels.append(f"Cycle{i}")

    fig = go.Figure(data=[go.Bar(x=labels, y=values, text=values, textposition='auto', marker_color=colors)])
    fig.update_layout(
        bargap=0.1,
        # title='Distribution cycles / Time(s)'  # Add the title here
    )
    fig.update_layout(margin=dict(t=30, b=30, l=30, r=30),
            font=dict(
            family=GRAPHS_FONT,
            color="#455364",
            size=14
        )
        )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='300px')

    return chart_html

def pointer_marker(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['production_time'], y=df['time_diff'], mode='markers', name='Cycle Time'))
    fig.add_trace(go.Scatter(x=df['production_time'], y=df['target'], mode='lines', name='Target'))
    fig.update_layout(
        title='Time Distribution',
        xaxis_title='Time',
        yaxis_title='Cycle Time (s)',
        legend_title='Legend',
        yaxis_type="log",
        yaxis_tickvals=[10, 100, 1000, 10000],
        yaxis_ticktext=["10", "100", "1,000", "10,000"],
        xaxis = dict(
        tickmode = 'array',
        tickvals = [time for time in df['production_time']],
        ticktext = [time.split(' ')[4] for time in df['production_time']]),
        font=dict(
            family=GRAPHS_FONT,
            color="#455364",
            size=12
        )
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def working_target_time(target_working_time, working_time):
    labels = ['Target (s)', 'Actual (s)']
    values = [target_working_time, working_time]

    # Define the retro LCD color palette
    lcd_colors = ['#C19E67', '#84B484']

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation='h',
        text=values,
        textposition='auto',
        marker=dict(
            color=lcd_colors
        )
    )])

    fig.update_layout(
        height=400,
        margin=dict(t=50, b=50, l=50, r=50),
        xaxis_title=f"The operator working time should be at least {target_working_time}(s)",
        yaxis_title="",
        bargap=0.1,
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        font=dict(
            family=GRAPHS_FONT,
            color="#455364",
            size=16
        )
    )

    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def generate_time_series_chart2(df2):
    fig = go.Figure()

    # Line 1: When 'shift' = 1 in blue
    fig.add_trace(
        go.Scatter(x=df2[df2['shift'] == 1]['day'], y=df2[df2['shift'] == 1]['total'], mode='lines', name='Shift 1',
                   line=dict(color='blue')))

    # Line 2: When 'shift' = 2 in green
    fig.add_trace(
        go.Scatter(x=df2[df2['shift'] == 2]['day'], y=df2[df2['shift'] == 2]['total'], mode='lines', name='Shift 2',
                   line=dict(color='orange')))

    # Line 3: When 'shift' = 3 in yellow
    fig.add_trace(
        go.Scatter(x=df2[df2['shift'] == 3]['day'], y=df2[df2['shift'] == 3]['total'], mode='lines', name='Shift 3',
                   line=dict(color='black')))

    fig.update_layout(
        title='S06 weekly report of production',
        xaxis_title='Date',
        yaxis_title='Production (pcs)',
        legend_title='Shifts',
        yaxis_type="log",
        yaxis_tickvals=[500, 1000, 2000, 4000, 8000, 16000],
        yaxis_ticktext=["500", "1000", "2,000", "4,000", "8,000", "16,000"]
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def generate_time_series_chart3(df3):
    fig = go.Figure()

    # Line 1: When 'shift' = 1 in blue
    fig.add_trace(go.Scatter(x=df3[df3['shift'] == 1]['day'], y=df3[df3['shift'] == 1]['per1'] * 100, mode='lines',
                             name='Shift 1', line=dict(color='blue')))

    # Line 2: When 'shift' = 2 in green
    fig.add_trace(go.Scatter(x=df3[df3['shift'] == 2]['day'], y=df3[df3['shift'] == 2]['per1'] * 100, mode='lines',
                             name='Shift 2', line=dict(color='orange')))

    # Line 3: When 'shift' = 3 in yellow
    fig.add_trace(go.Scatter(x=df3[df3['shift'] == 3]['day'], y=df3[df3['shift'] == 3]['per1'] * 100, mode='lines',
                             name='Shift 3', line=dict(color='black')))

    fig.update_layout(
        title='S06 weekly report of performance',
        xaxis_title='Date',
        yaxis_title='Performance (%)',
        legend_title='Shifts',
        yaxis_type="linear",
        yaxis_tickformat='.0f'
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def generate_time_series_chart4(df4):
    fig = go.Figure()

    # Line 1: When 'shift' = 1 in blue
    fig.add_trace(
        go.Scatter(x=df4[df4['shift'] == 1]['day'], y=df4[df4['shift'] == 1]['cycle1'], mode='lines', name='Shift 1',
                   line=dict(color='blue')))

    # Line 2: When 'shift' = 2 in green
    fig.add_trace(
        go.Scatter(x=df4[df4['shift'] == 2]['day'], y=df4[df4['shift'] == 2]['cycle1'], mode='lines', name='Shift 2',
                   line=dict(color='orange')))

    # Line 3: When 'shift' = 3 in yellow
    fig.add_trace(
        go.Scatter(x=df4[df4['shift'] == 3]['day'], y=df4[df4['shift'] == 3]['cycle1'], mode='lines', name='Shift 3',
                   line=dict(color='black')))

    fig.update_layout(
        title='S06 weekly report of production in OK CT',
        xaxis_title='Date',
        yaxis_title='Production in OK CT (pcs)',
        legend_title='Shifts',
        yaxis_type="log",
        yaxis_tickvals=[500, 1000, 2000, 4000, 8000, 16000],
        yaxis_ticktext=["500", "1000", "2,000", "4,000", "8,000", "16,000"]
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def generate_time_series_chart5(df5):
    fig = go.Figure()

    # Line 1: When 'shift' = 1 in blue
    fig.add_trace(go.Scatter(x=df5[df5['shift'] == 1]['day'], y=df5[df5['shift'] == 1]['average_act'], mode='lines',
                             name='Shift 1', line=dict(color='blue')))

    # Line 2: When 'shift' = 2 in green
    fig.add_trace(go.Scatter(x=df5[df5['shift'] == 2]['day'], y=df5[df5['shift'] == 2]['average_act'], mode='lines',
                             name='Shift 2', line=dict(color='orange')))

    # Line 3: When 'shift' = 3 in yellow
    fig.add_trace(go.Scatter(x=df5[df5['shift'] == 3]['day'], y=df5[df5['shift'] == 3]['average_act'], mode='lines',
                             name='Shift 3', line=dict(color='black')))

    fig.update_layout(
        title='S06 weekly report of average',
        xaxis_title='Date',
        yaxis_title='Average (s)',
        legend_title='Shifts',
        yaxis_type="log",
        yaxis_tickvals=[500, 1000, 2000, 4000, 8000, 16000],
        yaxis_ticktext=["500", "1000", "2,000", "4,000", "8,000", "16,000"]
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def generate_time_series_chart6(df6):
    fig = go.Figure()

    # Line 1: When 'shift' = 1 in blue
    fig.add_trace(
        go.Scatter(x=df6[df6['shift'] == 1]['day'], y=df6[df6['shift'] == 1]['dura'], mode='lines', name='Shift 1',
                   line=dict(color='blue')))

    # Line 2: When 'shift' = 2 in green
    fig.add_trace(
        go.Scatter(x=df6[df6['shift'] == 2]['day'], y=df6[df6['shift'] == 2]['dura'], mode='lines', name='Shift 2',
                   line=dict(color='orange')))

    # Line 3: When 'shift' = 3 in yellow
    fig.add_trace(
        go.Scatter(x=df6[df6['shift'] == 3]['day'], y=df6[df6['shift'] == 3]['dura'], mode='lines', name='Shift 3',
                   line=dict(color='black')))

    fig.update_layout(
        title='S06 weekly report of production duration',
        xaxis_title='Date',
        yaxis_title='Production Duration (min)',
        legend_title='Shifts',
        yaxis_type="log",
        yaxis_tickvals=[500, 1000, 2000, 4000, 8000, 16000],
        yaxis_ticktext=["500", "1000", "2,000", "4,000", "8,000", "16,000"]
    )
    chart_html = fig.to_html(full_html=False, default_width='100%', default_height='400px')
    return chart_html

def lines_data_calculation(j_data):
    t_prod = sum(int(pointer["production_value"]) for pointer in j_data)
    # total production of station by shift on cycle1
    t_prod_cycle1 = sum(int(pointer["production_value"]) for pointer in j_data if "Cycle1-" in pointer["cycle_name"])
    # performance of the station by shift 
    if t_prod == 0:
        per = 0
    else:
        per = round((t_prod_cycle1 / t_prod)*100)
    return t_prod, per
# data calculation
def data_calculation(j_data):
    
    line_name = j_data[0]['line_name']
    station_name = j_data[0]['station_name']

    t_prod = sum(int(pointer["production_value"]) for pointer in j_data)

    # total production of station by shift on cycle1
    t_prod_cycle1 = sum(int(pointer["production_value"]) for pointer in j_data if "Cycle1-" in pointer["cycle_name"])

    # performance of the station by shift 
    if t_prod == 0:
        per = 0
    else:
        per = round((t_prod_cycle1 / t_prod)*100)
    perf_chart = generate_gauge_chart(per)

    # work duration in minutes
    dur = round(sum(float(pointer["time_diff"]) for pointer in j_data)/60)
    rem = DAY_WORK_TIME - dur - (BREAK_TIME * BREAK_TIME_NUMBER)
    dur_chart = generate_pie_chart(dur, rem)

    # Total production by each cycle
    cycles_names_query = '''
        SELECT cycle_name FROM cycles c
        JOIN production_line pln ON pln.production_line_id = c.production_line_id
        where line_name = :line_name
        '''
    t_cycle_prod=[]
    with engine.connect() as conn:
        cur = conn.execute(text(cycles_names_query), {"line_name" : line_name})

        cycles_names = [row["cycle_name"].replace(f'{line_name}_','') for row in cur.mappings()]
        cycles_names.remove('First_Entry')
    
    for cycle in cycles_names:
        t_cycle_prod.append(sum(int(pointer["production_value"]) for pointer in j_data if cycle in pointer["cycle_name"]))

    cycles_chart = generate_cycles_chart(t_cycle_prod,cycles_names)


    # target graph
    pointer_time = []
    for pointer in j_data:
        pointer_time.append({'production_time':pointer['production_time'],'time_diff':pointer['time_diff'],'target':4.5})

    df = pd.DataFrame.from_dict(pointer_time)
    target_chart = pointer_marker(df)

    TARGET = 4.5
    working_time = dur/t_prod
    target_working_time= TARGET

    avr_chart = working_target_time(target_working_time,working_time)

    return t_prod, per, perf_chart, dur_chart, cycles_chart, target_chart, avr_chart


# @app.route("/")
# def index():
#     return render_template('index.html')

# @app.route("/api/get_data", methods=["GET"])
# def get_data():
    selected_date = request.args.get("date")  # Get the date parameter
    shift_name = request.args.get("shift_name")  # Get the shift ID
    station_name = request.args.get("station_name")  # Get the station ID

    # Validate parameters
    if not selected_date:
        return jsonify({"error": "No date provided"}), 400
    if not shift_name:
        return jsonify({"error": "No shift Name provided"}), 400
    if not station_name:
        return jsonify({"error": "No station Name provided"}), 400

    # SQL query to fetch data
    query = """select s.station_name,pln.line_name, sh.shift_name, pd.production_time, spo.shift_end_day, pd.production_value, pd.time_diff, c.cycle_name, COALESCE(op.operator_name, 'Not Assigned') AS operator_name
from production_data pd
join shift_pointers spo on pd.pointer_id = spo.pointer_id
join stations s on pd.station_id = s.station_id
join pointer po on pd.pointer_id = po.pointer_id
join shifts sh on pd.shift_id = sh.shift_id
join cycles c on pd.cycle_id = c.cycle_id
join production_line pln on pd.production_line_id = pln.production_line_id
left join operators op on pd.operator_id = op.operator_id
where s.station_name = :station_name and sh.shift_name = :shift_name and spo.shift_end_day = :selected_date
"""

    with engine.connect() as conn:
        # Total production
        cur = conn.execute(text(query), {'station_name' : station_name, 'shift_name' : shift_name, 'selected_date' : selected_date})
        # cur = conn.execute(query, (station_id, shift_id, selected_date))
        # data = cur.fetchall()
        data = [dict(row) for row in cur.mappings()]
        # for row in cur.mappings():
        #     data.append(dict(row))

# Return the fetched data as JSON
    return jsonify(data)

# make a time shift station select to set data
@app.route("/setdata", methods=["GET", "POST"])
def setdata():
    if request.method == "POST":
        selected_date = request.form["selected_date"]
        selected_station = request.form["selected_station"]
        selected_shift = request.form["selected_shift"]
        
        session["date"] = selected_date
        session["station"] = selected_station
        session["shift"] = selected_shift

        # # specify that the sessions should be permanent 
        # session.permanent = True

        return redirect(url_for("dash", date=selected_date, station=selected_station, shift=selected_shift))
 
    return render_template('dash.html')


# # DASH with dash API
# @app.route("/dash", methods=["GET", "POST"])
# def dash():
    current_info={
    "current_date" : datetime.now().date(),
    "current_year" : datetime.now().year,
    "current_month" : datetime.now().month,
    "current_day" : datetime.now().day,
    "current_time" : datetime.now().time(),
    "current_hour" : datetime.now().time().hour,
    "current_shift" : get_current_shift()
    }

    selected_date = request.args.get("date", session.get("date", None))
    selected_shift = request.args.get("shift", session.get("shift", None))
    selected_station = request.args.get("station", session.get("station", None))

    session["date"] = selected_date
    session["shift"] = selected_shift
    session["station"] = selected_station

    url = "http://127.0.0.1:5000/api/get_data"
    params = {
        "date": selected_date,
        "shift_name": selected_shift,
        "station_name": selected_station
    }
    response = requests.get(url, params=params)
    pointers = response.json()
    if response.status_code == 200:
        data = data_calculation(pointers)
    else:
        data = (0, 0, 0)  # Handle error gracefully
    
    # get the info of the station:
    # info_dict = pointers.__dict__
    station_name = session.get("station", None)
    # line_name = pointers[0]['line_name']
    # operator_name = pointers[0]['operator_name']
    shift_name = session.get("shift", None)
    
    
    # to set the checked shift in radio select of shifts
    shift_in_session = {"M": 'Morning'== selected_shift, "A": 'Afternoon' == selected_shift, "N": 'Night' == selected_shift}
    station_in_session = False


    return render_template('dash.html',
                           t_prod=data[0],
                           per= data[1],
                           perf_chart=data[2],
                           shift_in_session=shift_in_session,
                           station_in_session=station_in_session,
                           station_name = station_name,
                        #    line_name = line_name,
                        #    operator_name = operator_name,
                           shift_name = shift_name,
                           current_year = current_info['current_year']
                           )


def processed_data(needed_data):
    current_info={
    "current_date" : date.today(),
    "current_year" : date.today().year,
    "current_month" : date.today().month,
    "current_day" : date.today().day,
    "current_time" : datetime.now().time(),
    "current_hour" : datetime.now().time().hour,
    "current_shift" : get_current_shift()
    }

    selected_shift = request.args.get("shift", session.get('shift', current_info.get('current_shift')))
    if current_info['current_shift'] == "Night":
        selected_date = request.args.get("date", session.get('date', current_info.get('current_date') + timedelta(1)))
    else:
        selected_date = request.args.get("date", session.get('date', current_info.get('current_date')))
    selected_station = request.args.get("station", session.get("station", None))

    session["date"] = selected_date
    session["shift"] = selected_shift
    session["station"] = selected_station

    url = "http://127.0.0.1:5000/api/get_lines_data"
    params = {
        "date": selected_date,
        "shift_name": selected_shift,
    }
    response = requests.get(url, params=params)
    
    
    # pointers_list = json.loads(pointers)

    if response.status_code == 200:
        pointers = response.json()
        # Initialize a nested dictionary structure
        lines_pointers = defaultdict(lambda: defaultdict(list))
        for station_pointers in pointers:
            line_name = station_pointers["line_name"]
            station_name = station_pointers["station_name"]
            filtered_station_pointers = {k: v for k, v in station_pointers.items()}
            lines_pointers[line_name][station_name].append(filtered_station_pointers)
        
        # To get a good format of dictionary
        pointers_byline_bystation = json.loads(json.dumps(lines_pointers))

        data_calcul = defaultdict(lambda: defaultdict(list))
        
        for station_pointers in pointers:
            line_name = station_pointers["line_name"]
            station_name = station_pointers["station_name"]
            data_calcul[line_name][station_name] = lines_data_calculation(pointers_byline_bystation[line_name][station_name])
        final_data_calcul = json.loads(json.dumps(data_calcul))

        # Sort stations by performance for each line
        for lineKey, stations in final_data_calcul.items():
            final_data_calcul[lineKey] = dict(
                sorted(stations.items(), key=lambda item: item[1][1], reverse=False)
            )

    
    else:
        final_data_calcul = {"NO_LINE":{"NO_STATION":(0, 0, 0, 0, 0,0,0)}}
    
    # to set the checked shift in radio select of shifts
    shift_in_session = {"M": 'Morning'== selected_shift, "A": 'Afternoon' == selected_shift, "N": 'Night' == selected_shift}
    shift_name = session.get("shift", None)
    

    
    if needed_data == "lines":
        station_in_session = False
        return {
            "data": final_data_calcul,
            "shift_in_session": shift_in_session,
            "station_in_session":station_in_session,
            "selected_date": selected_date,
            "shift_name" :  shift_name,
            "current_year" :  current_info['current_year']
        }
    else:
        try:
            for line in final_data_calcul:
                for station in final_data_calcul[line]:
                    if station == selected_station:
                        selected_line = line
            station_data = data_calculation(pointers_byline_bystation[selected_line][selected_station])

        except UnboundLocalError:
            selected_line = "None"
            selected_station = session.get("station", None)
            station_data = (0, 0, 0, 0, 0, 0, 0)
            
        return {
            "data": final_data_calcul,
            "t_prod": station_data[0],
            "per": station_data[1],
            "perf_chart": station_data[2],
            "dur_chart": station_data[3],
            "cycles_chart": station_data[4],
            "target_chart": station_data[5],
            "avr_chart": station_data[6],
            "shift_in_session": shift_in_session,
            "selected_station" : selected_station,
            "line_name" : selected_line,
            "selected_date": selected_date,
        # #    "operator_name" :  operator_name,
            "shift_name" : shift_name,
            "current_year" : current_info['current_year']
        }
    

@app.route("/", methods=["GET", "POST"])
def dash():
    calculated_data = processed_data(needed_data="station")
    return render_template('dash.html', calculated_data=calculated_data)

@app.route('/lines', methods=["GET", "POST"])
def lines():
    calculated_data = processed_data(needed_data="lines")
    return render_template('lines.html', calculated_data=calculated_data)



@app.route('/get-processed-data/<needed_data>', methods=['GET'])
def get_processed_data(needed_data):
    calculated_data = processed_data(needed_data=needed_data) 
    return jsonify(calculated_data)


@app.route("/set_line_data", methods=["GET", "POST"])
def set_line_data():
    if request.method == "POST":
        # session.pop("date")
        selected_date = request.form["selected_date"] # Get the date from the form
        selected_shift = request.form["selected_shift"]
        
        session["date"] = selected_date
        session["shift"] = selected_shift
        

        # # specify that the sessions should be permanent 
        # session.permanent = True

        return redirect(url_for("lines", date=selected_date, shift=selected_shift))
    return render_template('lines.html')


@app.route("/api/get_lines_data", methods=["GET"])
def get_lines_data():
    selected_date = request.args.get("date", session.get('date'))  # Get the date parameter
    shift_name = request.args.get("shift_name", session.get('shift'))  # Get the shift ID

    # SQL query to fetch data
    query = """select s.station_name,pln.line_name, sh.shift_name, pd.production_time, pd.production_date, spo.shift_end_day, pd.production_value, pd.time_diff, c.cycle_name, COALESCE(op.operator_name, 'Not Assigned') AS operator_name
from production_data pd
join shift_pointers spo on pd.pointer_id = spo.pointer_id
join stations s on pd.station_id = s.station_id
join pointer po on pd.pointer_id = po.pointer_id
join shifts sh on pd.shift_id = sh.shift_id
join cycles c on pd.cycle_id = c.cycle_id
join production_line pln on pd.production_line_id = pln.production_line_id
left join operators op on pd.operator_id = op.operator_id
where sh.shift_name = :shift_name and spo.shift_end_day = :selected_date
"""
    with engine.connect() as conn:
        # Total production
        cur = conn.execute(text(query), {'shift_name' : shift_name, 'selected_date' : selected_date})
        # cur = conn.execute(query, (station_id, shift_id, selected_date))
        # data = cur.fetchall()
        data = [dict(row) for row in cur.mappings()]
        # for row in cur.mappings():
        #     data.append(dict(row))

# Return the fetched data as JSON
    return jsonify(data)






@app.route('/pointerinsert', methods=["GET", "POST"])
def pointerinsert():
    # Parse the JSON payload
    try:
        if request.method == "GET":
            # Handle GET request (cURL, Browser, API request)
            station_id = request.args.get('station_id')
            counter = request.args.get('counter')
        elif request.method == "POST":
            # Handle JSON payload from Arduino or other clients
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid or missing JSON data'}), 400
            station_id = data.get('station_id')
            counter = data.get('counter')
        # Ensure station_id and counter are provided
        if not station_id or counter is None:
            return jsonify({'error': 'Missing station_id or counter'}), 400
        
        # Insert into the database
        query = "INSERT INTO pointer (station_id, pointer_counter) VALUES (:station_id, :pointer_counter)"
        with engine.connect() as conn:  # Use engine.begin() to manage transactions
            conn.execute(text(query), {'station_id': station_id, 'pointer_counter': counter})
            conn.commit()

        return jsonify({'message': 'Data inserted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8000, debug=True)