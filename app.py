from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import sqlite3
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import date

app = Flask(__name__)
app.secret_key = 'ev_logistics_secret'

ADMIN_PASSWORD = '123@abc'

# Real EV numbers (edit as needed)
EV_IDS = [
    "KA25EV001",
    "KA25EV002",
    "KA25EV003"
]


def init_db():
    conn = sqlite3.connect('deliveries.db')
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS assignments 
           (date TEXT, vehicle TEXT, orders TEXT)'''
    )
    conn.commit()
    conn.close()


def cluster_deliveries_from_csv(csv_file, n_clusters=None):
    """
    csv_file: Flask FileStorage object from upload form.
    CSV columns: name, lat, lon
    Returns dict: { 'KA25EV001': {'orders': [...]}, ... }
    """
    # Read CSV directly from uploaded file
    df = pd.read_csv(csv_file)

    # Validate columns
    required_cols = {'name', 'lat', 'lon'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    # Remove rows without coordinates
    df = df.dropna(subset=['lat', 'lon'])

    # Convert coordinates to float
    df['lat'] = df['lat'].astype(float)
    df['lon'] = df['lon'].astype(float)

    coords = df[['lat', 'lon']].to_numpy()

    # Decide cluster count: min(#EVs, #unique points)
    if n_clusters is None:
        n_clusters = min(len(EV_IDS), len(np.unique(coords, axis=0)))

    # Scale for better clustering
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)

    # K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords_scaled)

    # Build assignments per EV
    assignments = {}
    for cluster_id in range(n_clusters):
        vehicle_id = EV_IDS[cluster_id]  # real EV number
        cluster_orders = df[labels == cluster_id].to_dict(orient='records')
        assignments[vehicle_id] = {"orders": cluster_orders}

    return assignments


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('upload'))
        flash('Invalid password')
    return render_template('login.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        csv_file = request.files.get('csv_file')
        if csv_file and csv_file.filename:
            today = date.today().isoformat()

            try:
                assignments = cluster_deliveries_from_csv(csv_file)
            except Exception as e:
                # Simple error message back to page
                flash(f'Error processing CSV: {e}')
                return render_template('upload.html')

            # Save to SQLite
            conn = sqlite3.connect('deliveries.db')
            c = conn.cursor()
            for vehicle, orders in assignments.items():
                c.execute(
                    "INSERT INTO assignments VALUES (?, ?, ?)",
                    (today, vehicle, str(orders))
                )
            conn.commit()
            conn.close()

            # Keep in session for display
            session['assignments'] = assignments
            return redirect(url_for('assignments'))

        flash('Please upload a CSV file.')
    return render_template('upload.html')


@app.route('/assignments')
def assignments():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    assignments = session.get('assignments', {})
    return render_template('assignments.html', assignments=assignments)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
