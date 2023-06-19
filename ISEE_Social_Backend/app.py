from flask import Flask,jsonify, render_template, request, redirect, send_from_directory, send_file
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

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Bio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        relationship_status TEXT,
        lives_in TEXT,
        works_at TEXT,
        FOREIGN KEY (user_id) REFERENCES NewUsers (id)
    )
''')
conn.commit()

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

@app.route('/bio', methods=['POST'])
def update_bio():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    payload = request.data.decode('utf-8')  # Decode the bytes to a string
    data = json.loads(payload)
    user_id = data.get('id')
    rel = data.get('rel')
    loc = data.get('loc')
    work = data.get('work')
    
    # Check if the user bio already exists
    cursor.execute('SELECT * FROM Bio WHERE user_id = ?', (user_id,))
    existing_bio = cursor.fetchone()
    
    if existing_bio:
        # Update the existing user bio
        cursor.execute('UPDATE Bio SET relationship_status = ?, lives_in = ?, works_at = ? WHERE user_id = ?', (rel, loc, work, user_id))
        conn.commit()
        return "User bio updated successfully"
    else:
        # Insert a new user bio
        cursor.execute('INSERT INTO Bio (user_id, relationship_status, lives_in, works_at) VALUES (?, ?, ?, ?)', (user_id, rel, loc, work))
        conn.commit()
        return "User bio added successfully"

@app.route('/bio', methods=['GET'])
def get_bio():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()

    # Get the user_id from the request
    user_id = request.args.get('user_id')

    # Check if the user_id exists
    if not user_id:
        return "Please provide a valid user_id"

    # Fetch the bio data for the given user_id
    cursor.execute('SELECT * FROM Bio WHERE user_id = ?', (user_id,))
    bio_data = cursor.fetchone()

    if bio_data:
        # Convert the bio data into a dictionary
        bio = {
            'user_id': bio_data[1],
            'relationship_status': bio_data[2],
            'lives_in': bio_data[3],
            'works_at': bio_data[4]
        }
        return jsonify(bio)
    else:
        return "Bio data not found"
    

@app.route('/add-friend', methods=['POST'])
def add_friend():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # Get the form data from the request
        payload = request.data.decode('utf-8')  # Decode the bytes to a string
        data = json.loads(payload)
        user_id = data.get('user_id')
        friend_id = data.get('friend_id')

        # Check if both user_id and friend_id exist
        if not user_id or not friend_id:
            return "Please provide user_id and friend_id"

        # Create a new table to store the friends data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                friend_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES NewUsers (id),
                FOREIGN KEY (friend_id) REFERENCES NewUsers (id)
            )
        ''')
        # Check if the friendship already exists
        cursor.execute('SELECT * FROM Friends WHERE user_id = ? AND friend_id = ?', (user_id, friend_id))
        friendship = cursor.fetchone()

        if friendship:
            # Friendship already exists
            return "Friendship already exists"
        else:
            # Add the friendship to the Friends table
            cursor.execute('INSERT INTO Friends (user_id, friend_id) VALUES (?, ?)', (user_id, friend_id))
            conn.commit()
            return "Friend added successfully"

    return "Method Not Allowed"


@app.route('/get-friends', methods=['POST'])
def get_friends():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Get the user_id from the request
        payload = request.data.decode('utf-8')
        data = json.loads(payload)
        user_id = data.get('user_id')

        # Check if the user_id exists
        if not user_id:
            return json.dump({'error': 'Please provide a valid user_id'})

        # Get the friends of the user from the Friends table
        cursor.execute('''
            SELECT NewUsers.id, NewUsers.user_name
            FROM Friends
            INNER JOIN NewUsers ON Friends.friend_id = NewUsers.id
            WHERE Friends.user_id = ?
        ''', (user_id,))
        friends = cursor.fetchall()

        # Convert the friends data into a list of dictionaries
        friends_data = []
        for friend in friends:
            friend_data = {
                'id': friend[0],
                'user_name': friend[1]
            }
            friends_data.append(friend_data)

        # Return the friends data as JSON response
        return (friends_data)

    return json.dump({'error': 'Method Not Allowed'})

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
    app.run(debug=True)
