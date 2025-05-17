
from flask import Flask, render_template, redirect, request, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                exit_price REAL,
                result REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("database.db") as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return redirect('/login')
            except sqlite3.IntegrityError:
                return "Usuário já existe."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect('/dashboard')
            else:
                return "Login inválido"
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        asset = request.form['asset']
        direction = request.form['direction']
        entry = float(request.form['entry_price'])
        exit_price = float(request.form['exit_price'])
        result = exit_price - entry if direction == 'buy' else entry - exit_price

        with sqlite3.connect("database.db") as conn:
            conn.execute('''
                INSERT INTO trades (user_id, date, asset, direction, entry_price, exit_price, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  asset, direction, entry, exit_price, result))
            conn.commit()

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT date, asset, direction, entry_price, exit_price, result FROM trades WHERE user_id=?", (session['user_id'],))
        trades = c.fetchall()

    return render_template('dashboard.html', trades=trades, username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
