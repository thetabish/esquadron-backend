from flask import Flask, render_template, request, redirect, send_from_directory, send_file
import sqlite3
from flask_cors import CORS
import json
from werkzeug.utils import secure_filename
import os

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
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

@app.route('/upload-profile-picture', methods=['POST'])
def upload_profile_picture():
    if request.method == 'POST':
        # Check if the uploaded file is present in the request
        if 'file' not in request.files:
            return 'No file uploaded'

        # Get the user ID from the request (you can modify this based on your frontend implementation)
        user_id = request.form.get('user_id')

        file = request.files['file']

        # Check if a file with a valid extension is being uploaded
        if file.filename == '':
            return 'No file selected'

        if not allowed_file(file.filename):
            return 'Invalid file type'

        # Generate a secure filename and save the file in the desired location
        filename = secure_filename(file.filename)
        file.save(os.path.join('assets', filename))

        # Save the profile picture filename and user ID in the ProfilePictures table
        conn = sqlite3.connect('NewUsers.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProfilePictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                profile_picture TEXT,
                FOREIGN KEY (user_id) REFERENCES NewUsers (id)
            )
        ''')
        cursor.execute('INSERT INTO ProfilePictures (user_id, profile_picture) VALUES (?, ?)', (user_id, filename))
        #cursor.execute('DELETE FROM ProfilePictures')
        conn.commit()
        conn.close()

        # Return a success message or redirect to another page
        return filename

    return 'Method Not Allowed'




@app.route('/profile-picture/<user_id>')
def serve_profile_picture(user_id):
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT profile_picture FROM ProfilePictures WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        filename = result[0]
        directory = os.path.abspath('assets')
        return send_from_directory(directory, filename)
    else:
        return 'Profile picture not found'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# @app.route('/profile-picture/<filename>')
# def serve_profile_picture(filename):
#     directory = os.path.abspath('assets')
#     return send_from_directory(directory, filename)

@app.route('/update-profile-picture/<filename>/<id>')
def change_profile_picture(filename, id):
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT profile_picture FROM ProfilePictures WHERE user_id = ?', (id,))
    result = cursor.fetchone()
    directory = os.path.abspath('assets')
    return send_from_directory(directory, filename)


@app.route('/search', methods=['GET'])
def search_profiles():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    query = request.args.get('query')  # Get the search query from the URL parameter

    # Perform the search operation based on the query
    cursor.execute('SELECT * FROM NewUsers WHERE user_name LIKE ?', ('%' + query + '%',))
    profiles = cursor.fetchall()

    # Convert the profiles data into a list of dictionaries
    profiles_data = []
    for profile in profiles:
        profile_data = {
            'id': profile[0],
            'email': profile[1],
            'password': profile[2],
            'date_of_birth': profile[3],
            'country': profile[4],
            'city': profile[5],
            'user_name': profile[6]
        }
        profiles_data.append(profile_data)

    # Return the profiles data as JSON response
    return json.dumps(profiles_data)

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
