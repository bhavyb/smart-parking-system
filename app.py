from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'parking.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = 'dev_secret_key'  # change in production

@app.route('/')
def index():
    conn = get_db_connection()
    slots = conn.execute('SELECT * FROM slots ORDER BY slot_id').fetchall()
    conn.close()
    return render_template('index.html', slots=slots)

@app.route('/slots')
def slots_view():
    conn = get_db_connection()
    slots = conn.execute('SELECT * FROM slots ORDER BY slot_id').fetchall()
    conn.close()
    return render_template('available_slots.html', slots=slots)

@app.route('/book', methods=['GET','POST'])
def book_slot():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        vehicle_no = request.form.get('vehicle_no','').strip()
        phone = request.form.get('phone','').strip()
        slot_no = int(request.form.get('slot_no'))
        if not name or not vehicle_no:
            flash('Please fill required fields','danger')
            return redirect(url_for('book_slot'))
        # insert booking and mark slot occupied
        conn.execute('INSERT INTO bookings (name,vehicle_no,phone,slot_no,booking_time) VALUES (?,?,?,?,?)',
                     (name,vehicle_no,phone,slot_no, datetime.now().isoformat()))
        conn.execute('UPDATE slots SET is_available=0 WHERE slot_id=?',(slot_no,))
        conn.commit()
        conn.close()
        return render_template('booking_success.html', name=name, slot_no=slot_no, vehicle_no=vehicle_no)
    else:
        slots = conn.execute('SELECT * FROM slots WHERE is_available=1 ORDER BY slot_id').fetchall()
        conn.close()
        return render_template('book_slot.html', slots=slots)

@app.route('/admin', methods=['GET','POST'])
def admin_login():
    # simple placeholder admin login (username: admin, password: admin)
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        if u=='admin' and p=='admin':
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials','danger')
            return redirect(url_for('admin_login'))
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    bookings = conn.execute('SELECT * FROM bookings ORDER BY booking_time DESC').fetchall()
    slots = conn.execute('SELECT * FROM slots ORDER BY slot_id').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', bookings=bookings, slots=slots)

@app.route('/admin/free/<int:slot_id>', methods=['POST'])
def free_slot(slot_id):
    conn = get_db_connection()
    conn.execute('UPDATE slots SET is_available=1 WHERE slot_id=?',(slot_id,))
    # optional: delete bookings for freed slot
    conn.commit()
    conn.close()
    flash(f'Slot {slot_id} marked available','success')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
