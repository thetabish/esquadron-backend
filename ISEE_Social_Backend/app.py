from flask import Flask, render_template, request, redirect
import sqlite3
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Connect to the SQLite database
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create a table to store user data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        date_of_birth TEXT,
        country TEXT,
        city TEXT
    )
''')
conn.commit()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    conn = sqlite3.connect('users.db')
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
        
        # Perform validation (add your validation logic here)
        if not email or not password or not date_of_birth or not country or not city:
            return "Please fill in all the required fields"
        
        # Save the user data to the database
        cursor.execute('INSERT INTO users (email, password, date_of_birth, country, city) VALUES (?, ?, ?, ?, ?)', (email, password, date_of_birth, country, city))
        conn.commit()
        if cursor.lastrowid:
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            print("Data inserted successfully. User ID:", cursor.lastrowid)
        else:
            print("Failed to insert data into the database.")
        
        # Redirect to a success page or login page
        return "ok"
    
    # Render the signup page template for GET requests
    return render_template('signup.html')

if __name__ == '__main__':
    app.run()
