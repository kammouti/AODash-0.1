from sqlalchemy import create_engine, text
import sqlalchemy
import pandas as pd
from datetime import datetime, timedelta
from flask import jsonify
import requests
import json
from dotenv import load_dotenv
import os


# load_dotenv()
# db_pwd = os.getenv("DB_PWD")



db_pwd = os.environ.get("DB_PWD")


engine = create_engine(
    f"mysql+pymysql://doadmin:{db_pwd}@dataprod-do-user-2975072-0.j.db.ondigitalocean.com:25060/dataprod")





# with engine.connect() as conn:
#     result = conn.execute(text("SELECT * FROM number_times WHERE station = 17"))
#     data1 = result.fetchone()
#     print(data1, data1[0])



# # To use pandas this is the syntax:
# with engine.connect() as conn:
#     df = pd.read_sql_query("SELECT * FROM number_times", conn)
#     print(df)


# with engine.connect() as conn:
#     # cur6 = conn.execute(text("SELECT time, sec, target FROM irmodule WHERE station = 17"))
#     # data6 = cur6.fetchone()
#     df = pd.read_sql_query("SELECT time, sec, target FROM irmodule WHERE station = 17", conn)
#     # df = pd.DataFrame(data6, columns=['time', 'sec', 'target'])
#     # target_chart = generate_time_series_chart(df)
#     print(data6)


# with engine.connect() as conn:
#     station_per = []
#     cur = conn.execute(text("SELECT station, per1 FROM number_times"))
#     data = cur.fetchall()
#     for station in data:
#         station_per.append((station[0], station[1]))
#     print(station_per)

# with engine.connect() as conn:
#     # cur = conn.execute(text("select s.station_name, sum(production_value) from production_data pd join shift_pointers spo on pd.pointer_id = spo.pointer_id join stations s on pd.station_id = s.station_id join pointer po on pd.pointer_id = po.pointer_id where month(spo.shift_start_day) = '01' and year(spo.shift_start_day) = '2025' GROUP BY s.station_name"))
#     # data = cur.fetchall()


#     df = pd.read_sql_query("select s.station_name, sum(production_value) from production_data pd join shift_pointers spo on pd.pointer_id = spo.pointer_id join stations s on pd.station_id = s.station_id join pointer po on pd.pointer_id = po.pointer_id where month(spo.shift_start_day) = '01' and year(spo.shift_start_day) = '2025' GROUP BY s.station_name", conn)
#     print(df)
 

# def load_total_producion(station_id, shift_id, pyear, pmonth, pday):
#     d_dt = datetime(pyear, pmonth, pday)
#     f_p_date = d_dt.strftime("%Y-%m-%d")
#     with engine.connect() as conn:
#             # Total production
#             cur1 = conn.execute(text(f"SELECT sum(production_value) FROM production_data WHERE station_id = {station_id} and shift_id = {shift_id} and DATE(production_date)= '{f_p_date}'"))
#             data1 = cur1.fetchone()
#             t_prod = data1[0]
#     return t_prod


# to_prod = load_total_producion(1, 2, 2025, 1, 9)

# print(to_prod)


# t_prod_by_s_sh_date = """select sum(production_value)
# from production_data pd
# join shift_pointers spo on pd.pointer_id = spo.pointer_id
# join stations s on pd.station_id = s.station_id
# join pointer po on pd.pointer_id = po.pointer_id
# where s.station_id = :station_id and spo.shift_id = :shift_id and spo.shift_start_day = :f_p_date"""

# t_prod_by_s_sh_date_cycle1 = """select sum(production_value)
# from production_data pd
# join shift_pointers spo on pd.pointer_id = spo.pointer_id
# join stations s on pd.station_id = s.station_id
# join pointer po on pd.pointer_id = po.pointer_id
# where s.station_id = :station_id and spo.shift_id = :shift_id and spo.shift_start_day = :f_p_date and pd.cycle_id=1"""




# def timeadjust_toquery(year, month, day):
#     d_dt = datetime(year, month, day)
#     adjusted_date = d_dt.strftime("%Y-%m-%d")
#     return adjusted_date
    

# def load_total_production(query, station_id, shift_id, p_year, p_month, p_day):
#     f_p_date = timeadjust_toquery(p_year, p_month, p_day)
#     with engine.connect() as conn:
#             # Total production
#             cur1 = conn.execute(text(query), {'station_id' : station_id, 'shift_id' : shift_id, 'f_p_date' : f_p_date})
#             data1 = cur1.fetchone()
#             t_prod = data1[0]
#     return t_prod



# to_prod = load_total_production(t_prod_by_s_sh_date, 5, 2, 2025, 1, 8)


# def load_total_production(**params):

#     f_p_date = timeadjust_toquery(params['p_year'], params['p_month'], params['p_day'])
#     with engine.connect() as conn:
#             # Total production
#             cur1 = conn.execute(text(params['query']), {'station_id' : params['station_id'], 'shift_id' : params['shift_id'], 'f_p_date' : f_p_date})
#             data1 = cur1.fetchone()
#             t_prod = data1[0]
#     return t_prod


# stmt = sqlalchemy.insert('pointer').values(station_id="16")
# station_to_insert = 17

# query = "INSERT INTO pointer (station_id) value (:station_id)"
# with engine.connect() as conn:
#     # result = conn.execute(stmt)
#     conn.execute(text(query), {'station_id' : station_to_insert})
#     conn.commit()




# cycles_names_query = '''
#         SELECT cycle_name FROM cycles c
#         JOIN production_line pln ON pln.production_line_id = c.production_line_id
#         where line_name = :line_name
#         '''

# with engine.connect() as conn:
#     cur = conn.execute(text(cycles_names_query), {"line_name" : "Hyundai_MKQ"})
#     # cycles_names = cur.fetchone()

#     cycles_names = [row["cycle_name"].replace('-','') for row in cur.mappings()]

#     print(cycles_names)