from pso_engine import run_pso
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask import Response
from functools import wraps


def check_auth(username, password):
    # Change these to your own secure credentials!
    return username == 'admin' and password == 'password123'

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


app = Flask(__name__)
app.secret_key = 'super_secret_routing_key_replace_in_production'

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'routing_system_db'


# ── FIX: Custom JSON encoder so datetime/date objects don't crash jsonify ──
class CustomJSONProvider(app.json_provider_class):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_name=session.get('user_name'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already registered. Please log in.', 'error')
                    return redirect(url_for('register'))

                sql = "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(sql, (name, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_attempt = request.form['password']

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password_hash'], password_attempt):
                    session['user_id'] = user['id']
                    session['user_name'] = user['name']
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password.', 'error')
        finally:
            conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/landmarks', methods=['GET'])
def get_landmarks():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, landmark_name, lat, lng FROM landmarks ORDER BY landmark_name ASC")
            landmarks = cursor.fetchall()
            return jsonify(landmarks)
    finally:
        conn.close()


def get_all_transit_legs():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT t.*,
                       s.landmark_name as start_name, s.lat as start_lat, s.lng as start_lng,
                       e.landmark_name as end_name, e.lat as end_lat, e.lng as end_lng
                FROM transit_legs t
                JOIN landmarks s ON t.start_node_id = s.id
                JOIN landmarks e ON t.end_node_id = e.id
            """
            cursor.execute(sql)
            original_legs = cursor.fetchall()

            bidirectional_legs = []
            for leg in original_legs:
                bidirectional_legs.append(leg)

                reverse_leg = leg.copy()
                reverse_leg['start_node_id'] = leg['end_node_id']
                reverse_leg['end_node_id']   = leg['start_node_id']
                reverse_leg['start_name']    = leg['end_name']
                reverse_leg['end_name']      = leg['start_name']
                reverse_leg['start_lat']     = leg['end_lat']
                reverse_leg['start_lng']     = leg['end_lng']
                reverse_leg['end_lat']       = leg['start_lat']
                reverse_leg['end_lng']       = leg['start_lng']
                bidirectional_legs.append(reverse_leg)

            return bidirectional_legs
    finally:
        conn.close()


def find_all_paths(legs, current_node, target_node, current_path, all_paths, visited):
    if current_node == target_node:
        all_paths.append(list(current_path))
        return

    visited.add(current_node)

    for leg in legs:
        if leg['start_node_id'] == current_node and leg['end_node_id'] not in visited:
            current_path.append(leg)
            find_all_paths(legs, leg['end_node_id'], target_node, current_path, all_paths, visited)
            current_path.pop()

    visited.remove(current_node)


@app.route('/api/optimize', methods=['POST'])
def optimize_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    start_id = int(data['origin'])
    end_id   = int(data['destination'])
    mode     = data['mode']

    all_legs = get_all_transit_legs()
    possible_routes = []

    find_all_paths(all_legs, start_id, end_id, [], possible_routes, set())

    if not possible_routes:
        return jsonify({'error': 'No valid routes found between these landmarks.'}), 404

    optimal_solution = run_pso(possible_routes, mode)
    return jsonify(optimal_solution)


@app.route('/api/save_route', methods=['POST'])
def save_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data    = request.json
    user_id = session['user_id']
    origin_id = data['origin']
    dest_id   = data['destination']
    mode      = data['mode']

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM saved_routes
                WHERE user_id = %s AND origin_id = %s AND destination_id = %s AND optimization_mode = %s
            """, (user_id, origin_id, dest_id, mode))

            if cursor.fetchone():
                return jsonify({'message': 'Route already saved!'}), 200

            cursor.execute("""
                INSERT INTO saved_routes (user_id, origin_id, destination_id, optimization_mode)
                VALUES (%s, %s, %s, %s)
            """, (user_id, origin_id, dest_id, mode))
            conn.commit()
            return jsonify({'message': 'Route saved successfully!'}), 201
    except Exception as e:
        # ── FIX: log the real error so you can see it in your terminal ──
        print(f"ERROR in save_route: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()



@app.route('/api/saved_routes', methods=['GET'])
def get_saved_routes():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT sr.id,
                       sr.origin_id,
                       sr.destination_id,
                       sr.optimization_mode,
                       CAST(sr.saved_at AS CHAR) as saved_at,
                       o.landmark_name as origin_name,
                       d.landmark_name as destination_name
                FROM saved_routes sr
                JOIN landmarks o ON sr.origin_id = o.id
                JOIN landmarks d ON sr.destination_id = d.id
                WHERE sr.user_id = %s
                ORDER BY sr.saved_at DESC
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return jsonify(rows)
    except Exception as e:
        print(f"ERROR in get_saved_routes: {e}")
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500
    finally:
        conn.close()






# ==========================================
# ADMIN DASHBOARD ROUTES
# ==========================================

@app.route('/admin')
@requires_auth
def admin_dashboard():
    # In a real app, you'd check if session['user_id'] is an admin here!
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch landmarks so we can populate the dropdowns for adding routes
            cursor.execute("SELECT id, landmark_name FROM landmarks ORDER BY landmark_name ASC")
            landmarks = cursor.fetchall()
    finally:
        conn.close()
    
    return render_template('admin.html', landmarks=landmarks)

@app.route('/admin/add_landmark', methods=['POST'])
@requires_auth
def add_landmark():
    name = request.form.get('landmark_name')
    lat = request.form.get('lat')
    lng = request.form.get('lng')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Add the new location with coordinates
            cursor.execute(
                "INSERT INTO landmarks (landmark_name, lat, lng) VALUES (%s, %s, %s)",
                (name, lat, lng)
            )
        conn.commit()
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/add_leg', methods=['POST'])
@requires_auth
def add_leg():
    start_node = request.form.get('start_node')
    end_node = request.form.get('end_node')
    mode = request.form.get('mode')
    cost = request.form.get('cost')
    time = request.form.get('time')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Add the new connection between two existing nodes
            cursor.execute(
                "INSERT INTO transit_legs (start_node_id, end_node_id, transport_mode, cost, travel_time) VALUES (%s, %s, %s, %s, %s)",
                (start_node, end_node, mode, cost, time)
            )
        conn.commit()
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))









if __name__ == '__main__':
    app.run(debug=True)