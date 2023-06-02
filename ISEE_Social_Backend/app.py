from flask import Flask, render_template, request, redirect
import sqlite3
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Connect to the SQLite database
conn = sqlite3.connect('NewUsers.db')
cursor = conn.cursor()

# Create a table to store user data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS NewUsers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        date_of_birth TEXT,
        country TEXT,
        city TEXT,
        user_name TEXT
    )
''')
conn.commit()

@app.route('/suggest', methods=['GET'])
def get_user_names():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT user_name FROM NewUsers')
        user_names = [row[0] for row in cursor.fetchall()]
        return json.dumps(user_names)
    
    return "Method Not Allowed"

@app.route('/signin', methods=['POST'])
def signin():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # Get the form data from the request
        payload = request.data.decode('utf-8')  # Decode the bytes to a string
        data = json.loads(payload)
        email = data.get('email')
        password = data.get('password')
        
        # Check if the user exists in the database
        cursor.execute('SELECT * FROM NewUsers WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        
        if user:
            # User exists, return "ok"
            user_data = {
                'id': user[0],
                'email': user[1],
                'password': user[2],
                'date_of_birth': user[3],
                'country': user[4],
                'city': user[5],
                'user_name': user[6]
            }
            print(user_data)
            return json.dumps(user_data)
        else:
            # User does not exist or incorrect credentials
            return "Invalid email or password"
    
    return "Method Not Allowed"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # Get the form data from the request
        payload = request.data.decode('utf-8')  # Decode the bytes to a string
        data = json.loads(payload) 
        email = data.get('email')
        password = data.get('password')
        date_of_birth = data.get('dateOfBirth')
        country = data.get('country')
        city = data.get('city')
        user_name = data.get('userName')
        
        # Perform validation (add your validation logic here)
        if not email or not password or not date_of_birth or not country or not city or not user_name:
            return "Please fill in all the required fields"
        
        # Save the user data to the database
        cursor.execute('INSERT INTO NewUsers (email, password, date_of_birth, country, city, user_name) VALUES (?, ?, ?, ?, ?, ?)', (email, password, date_of_birth, country, city, user_name))
        conn.commit()
        if cursor.lastrowid:
            cursor.execute('SELECT * FROM NewUsers')
            rows = cursor.fetchall()
            print("Data inserted successfully. User ID:", cursor.lastrowid)
             # Data inserted successfully
            user_id = cursor.lastrowid
            cursor.execute('SELECT * FROM NewUsers WHERE email = ? AND password = ?', (email, password))
            user = cursor.fetchone()
            user_data = {
                'id': user[0],
                'email': user[1],
                'password': user[2],
                'date_of_birth': user[3],
                'country': user[4],
                'city': user[5],
                'user_name': user[6]
            }
            print(user_data)
            return json.dumps(user_data)

            # Redirect to a success page or login page
            # In this case, return the user_id as a JSON response
            return json.dumps({'user_id': user_id})
        else:
            print("Failed to insert data into the database.")
    
    # Render the signup page template for GET requests
    return render_template('signup.html')

if __name__ == '__main__':
    app.run()
