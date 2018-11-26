import os
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
app = Flask(__name__)

# url = urlparse.urlparse(os.environ.get(‘PG_URL’))

url = urlparse("postgresql://alytics:alytics@localhost:5433/alytics")
pool = ThreadedConnectionPool(1, 20,
                              database=url.path[1:],
                              user=url.username,
                              password=url.password,
                              host=url.hostname,
                              port=url.port)

@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            connection.commit()
    finally:
      cursor.close()


def points_query(function_name, interval, dt):
    query = """SELECT t as x, {} as y
                FROM
                (
                    SELECT extract(epoch from ts) as t
                    FROM generate_series(now() - (%s||'days')::interval,
                                         now(), 
                                         (%s||'hours')::interval)  as ts

                ) q;"""
    query = query.format(function_name)
    with get_db_cursor() as cur:
        cur.execute(query,
                    (interval, dt))
        data = cur.fetchall()

    return data


def validate_request_data(jsn):
    function_name = jsn.get('function')
    # sql injection protection
    if function_name not in ['t+2/t', 'sin(t)']:
        return None, None, None, jsonify({'error': 'function not supported'})
    try:
        interval = int(jsn.get('interval'))
    except Exception:
        return None, None, None, jsonify({'error': 'interval not correct'})
    try:
        dt = int(jsn.get('dt'))
    except Exception:
        return None, None, None, jsonify({'error': 'dt not correct'})

    if not interval or not dt or not function_name:
        return None, None, None, jsonify({"error": "required params not set"})

    return function_name, interval, dt, None


def format_points_data(data, function_name):
    out_data = {
        'infile': {
            'title': {"text": ""},
            'series': [{
                'data': [],
                "name": function_name,
                "_colorIndex": 0,
                "_symbolIndex": 0
            }]
        }
    }
    for item in data:
        out_data['infile']['series'][0]['data'].append([
            item['x'], item['y']
        ])
    return out_data


@app.route('/points', methods=['POST'])
def get_points():
    jsn = request.json
    function_name, interval, dt, error = validate_request_data(jsn)
    if error:
        return error
    points = points_query(function_name, interval, dt)
    formatted_points = format_points_data(points, function_name)
    return jsonify(formatted_points)


if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5002, debug=True)
