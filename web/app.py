import os
from base64 import b64encode
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from flask import Flask, request, jsonify, redirect
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from psycopg2 import Binary
from contextlib import contextmanager
from flask import render_template
import urllib
from uuid import uuid4
from celery import Celery
app = Flask(__name__)

pg_url = urlparse(os.environ.get('PG_URL'))
highcharts_url =  os.environ.get('HIGHCHARTS_URL')
points_generator_url = os.environ.get('POINTS_GENERATOR_URL')

app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND')

pool = ThreadedConnectionPool(1, 20,
                              database=pg_url.path[1:],
                              user=pg_url.username,
                              password=pg_url.password,
                              host=pg_url.hostname,
                              port=pg_url.port)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


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


def validate_request_data(form_data):
    function_name = form_data.get('function')
    # sql injection protection
    if function_name not in ['t+2/t', 'sin(t)']:
        return None, None, None, 'function not supported'
    try:
        interval = int(form_data.get('interval'))
    except ValueError:
        return None, None, None, 'interval not correct'
    try:
        dt = int(form_data.get('dt'))
    except ValueError:
        return None, None, None, 'dt not correct'

    if not interval or not dt or not function_name:
        return None, None, None, "required params not set"

    return function_name, interval, dt, None


def get_points_data(function_name, interval, dt):
    jsn = {
        "function": function_name,
        "interval": interval,
        "dt": dt}
    params = json.dumps(jsn).encode('utf8')
    req = urllib.request.Request(points_generator_url,
                                 data=params,
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return response.read()


def get_image_data(points):
    req = urllib.request.Request(highcharts_url,
                                 data=points,
                                 headers={'content-type': 'application/json'})
    try:
        response = urllib.request.urlopen(req)
        return response.read()
    except HTTPError as e:
        return e
    except URLError as e:
        return e


def update_graph(function_name, interval, dt, item_id):
    with get_db_cursor(commit=True) as cur:
        points = get_points_data(function_name, interval, dt)
        graph = get_image_data(points)
        if isinstance(graph, bytes):
            cur.execute("UPDATE graphs SET graph = %s, ts = now() WHERE id = %s",
                        (Binary(graph), item_id))
        else:
            cur.execute("UPDATE graphs SET error = %s, ts = now() WHERE id = %s",
                        (graph, item_id))


def update_function(function_name, interval, dt):
    with get_db_cursor(commit=True) as cur:
        item_id = str(uuid4())
        cur.execute("INSERT INTO graphs (id, func, time_interval, dt)\
                     VALUES (%s, %s, %s, %s)",
                    (item_id, function_name, interval, dt))
    return item_id


@celery.task
def update_func_data(item):
    with app.app_context():
        update_graph(item['func'],
                     item['time_interval'],
                     item['dt'],
                     item['id'])


@app.route('/', methods=['GET'])
def index():
    with get_db_cursor(commit=True) as cur:
        cur.execute("SELECT * FROM graphs")
        data = cur.fetchall()
    for i in range(len(data)):
        item = data[i]
        if item['graph']:
            item['graph'] = b64encode(item['graph']).decode('utf-8')
        else:
            item['graph'] = ''
    return render_template('index.html', table_data=data)


@app.route('/add', methods=['GET', 'POST'])
def add_function():
    if request.method == 'GET':
        return render_template('add.html', error='')
    if request.method == 'POST':
        form_data = request.form
        function_name, interval, dt, error = validate_request_data(form_data)
        if error:
            return render_template('add.html', error=error)

        item_id = update_function(function_name, interval, dt)
        update_graph(function_name, interval, dt, item_id)

        return redirect("/", code=302)


@app.route('/update', methods=['POST'])
def update_graphs():
    ids = tuple(request.form.getlist('id'))
    print(ids)
    if len(ids) == 0:
        return redirect("/", code=302)
    with get_db_cursor(commit=True) as cur:
        cur.execute("SELECT id, func, time_interval, dt FROM graphs WHERE id IN %s",
                    (ids,))
        data = cur.fetchall()

    for item in data:
        update_func_data.delay(item)

    return redirect("/", code=302)


if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5001, debug=True)

