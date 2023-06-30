from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    send_from_directory,
    send_file,
)
import sqlite3
from flask_cors import CORS
import json
from werkzeug.utils import secure_filename
import os
import base64, datetime
import bcrypt 

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "posts")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Connect to the SQLite database
conn = sqlite3.connect("NewUsers.db")
cursor = conn.cursor()


conn.commit()
# Create a table to store user data
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS NewUsers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        date_of_birth TEXT,
        country TEXT,
        city TEXT,
        user_name TEXT,
        question TEXT,
        answer TEXT
    )
    """
)

conn.commit()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Bio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        relationship_status TEXT,
        lives_in TEXT,
        works_at TEXT,
        education TEXT,
        gender TEXT,  -- Add the 'gender' field
        marital_status TEXT,  -- Add the 'marital_status' field
        interested_in_dating TEXT,  -- Add the 'interested_in_dating' field
        sexual_orientation TEXT,  -- Add the 'sexual_orientation' field
        FOREIGN KEY (user_id) REFERENCES NewUsers (id)
    )
"""
)
conn.commit()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        blocked_user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES NewUsers (id),
        FOREIGN KEY (blocked_user_id) REFERENCES NewUsers (id)
    )
"""
)
conn.commit()
conn.close()


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}


@app.route("/block-user", methods=["POST"])
def block_user():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "POST":
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        user_id = data.get("user_id")
        blocked_user_id = data.get("blocked_user_id")

        if not user_id or not blocked_user_id:
            return json.dumps({"message": "Please provide user_id and blocked_user_id"})

        # Check if the blocking relationship already exists
        cursor.execute(
            "SELECT * FROM Blocks WHERE user_id = ? AND blocked_user_id = ?",
            (user_id, blocked_user_id),
        )
        block_relationship = cursor.fetchone()

        if block_relationship:
            # Block relationship already exists, return an appropriate response
            return json.dumps({"message": "Block relationship already exists"})
        else:
            # Add the block relationship to the Blocks table
            cursor.execute(
                "INSERT INTO Blocks (user_id, blocked_user_id) VALUES (?, ?)",
                (user_id, blocked_user_id),
            )
            conn.commit()
            return json.dumps({"message": "User blocked successfully"})

    return "Method Not Allowed"


@app.route("/unblock-user", methods=["POST"])
def unblock_user():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "POST":
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        user_id = data.get("user_id")
        blocked_user_id = data.get("blocked_user_id")

        if not user_id or not blocked_user_id:
            return json.dumps({"message": "Please provide user_id and blocked_user_id"})

        # Check if the blocking relationship exists
        cursor.execute(
            "SELECT * FROM Blocks WHERE user_id = ? AND blocked_user_id = ?",
            (user_id, blocked_user_id),
        )
        block_relationship = cursor.fetchone()

        if block_relationship:
            # Unblock the user by deleting the block relationship
            cursor.execute(
                "DELETE FROM Blocks WHERE user_id = ? AND blocked_user_id = ?",
                (user_id, blocked_user_id),
            )
            conn.commit()
            return json.dumps({"message": "User unblocked successfully"})
        else:
            # Block relationship does not exist
            return json.dumps({"message": "Block relationship does not exist"})

    return "Method Not Allowed"

@app.route('/get-blocked-by-users', methods=['POST'])
def get_blocked_by_usersforusers():
    conn = sqlite3.connect('NewUsers.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        payload = request.data.decode('utf-8')
        data = json.loads(payload)
        user_id = data.get('user_id')

        if not user_id:
            return json.dumps({'error': 'Please provide a valid user_id'})

        # Get the blocked users for the given user_id from the Blocks table
        cursor.execute('''
            SELECT NewUsers.id, NewUsers.user_name
            FROM Blocks
            INNER JOIN NewUsers ON Blocks.user_id = NewUsers.id
            WHERE Blocks.blocked_user_id = ?
        ''', (user_id,))
        blocked_users = cursor.fetchall()

        # Convert the blocked users data into a list of dictionaries
        blocked_users_data = []
        for user in blocked_users:
            user_data = {
                'id': user[0],
                'user_name': user[1]
            }
            blocked_users_data.append(user_data)

        # Return the blocked users data as JSON response
        return json.dumps(blocked_users_data)

    return json.dumps({'error': 'Method Not Allowed'})


@app.route('/get-blocked-users', methods=['POST'])
def get_blocked_usersforusers():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "POST":
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        user_id = data.get("user_id")

        if not user_id:
            return json.dumps({"error": "Please provide a valid user_id"})

        # Get the blocked users for the given user_id from the Blocks table
        cursor.execute(
            """
            SELECT NewUsers.id, NewUsers.user_name
            FROM Blocks
            INNER JOIN NewUsers ON Blocks.blocked_user_id = NewUsers.id
            WHERE Blocks.user_id = ?
        """,
            (user_id,),
        )
        blocked_users = cursor.fetchall()

        # Convert the blocked users data into a list of dictionaries
        blocked_users_data = []
        for user in blocked_users:
            user_data = {"id": user[0], "user_name": user[1]}
            blocked_users_data.append(user_data)

        # Return the blocked users data as JSON response
        return json.dumps(blocked_users_data)

    return json.dumps({"error": "Method Not Allowed"})


@app.route("/blocked-users", methods=["GET"])
def get_blocked_users():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    # SQL statement to create BlockedUsers table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS BlockedUsers (
            user_id INT NOT NULL,
            PRIMARY KEY (user_id)
        )
    """
    )

    cursor.execute("SELECT * FROM BlockedUsers")

    blocked_users = cursor.fetchall()
    blocked_users_list = []
    blocked_users_list = [user[0] for user in blocked_users]

    conn.close()

    return jsonify({"blocked_users": blocked_users_list})


@app.route("/update-blocked-users", methods=["POST"])
def update_blocked_users():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    # SQL statement to create BlockedUsers table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS BlockedUsers (
            user_id INT NOT NULL,
            PRIMARY KEY (user_id)
        )
    """
    )
    payload = request.get_json()
    user_id = payload.get("user_id")
    block = payload.get("block")

    if block:
        # Insert user_id into BlockedUsers table
        cursor.execute(
            "INSERT OR IGNORE INTO BlockedUsers (user_id) VALUES (?)", (user_id,)
        )
    else:
        # Remove user_id from BlockedUsers table
        cursor.execute("DELETE FROM BlockedUsers WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return {"status": "success"}


@app.route("/get-user-posts/<int:user_id>", methods=["GET"])
def get_user_posts(user_id):
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT Posts.user_id, NewUsers.user_name, Posts.image_path, Posts.text
        FROM Posts
        INNER JOIN NewUsers ON Posts.user_id = NewUsers.id
        WHERE Posts.user_id = ?
        ORDER BY Posts.timestamp DESC
    """,
        (user_id,),
    )

    posts = cursor.fetchall()
    post_data = []

    for post in posts:
        user_id, user_name, image_path, text = post

        # Load the image file as bytes
        image_data = None
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

        image_base64 = (
            base64.b64encode(image_data).decode("utf-8") if image_data else None
        )

        post_data.append(
            {
                "user_id": user_id,
                "user_name": user_name,
                "image_base64": image_base64,
                "text": text,
            }
        )

    conn.close()

    return jsonify({"posts": post_data})


@app.route("/get-posts/<int:user_id>", methods=["GET"])
def get_posts(user_id):
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    cursor.execute(
    """
    SELECT Posts.user_id, NewUsers.user_name, Posts.image_path, Posts.text
    FROM Posts
    INNER JOIN NewUsers ON Posts.user_id = NewUsers.id
    WHERE Posts.user_id = ?
        OR Posts.user_id IN (
            SELECT friend_id
            FROM Friends
            WHERE user_id = ?
        )
    ORDER BY Posts.timestamp DESC
    """,
    (user_id, user_id),
)

    posts = cursor.fetchall()
    post_data = []

    for post in posts:
        user_id, user_name, image_path, text = post

        # Load the image file as bytes
        image_data = None
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

        image_base64 = (
            base64.b64encode(image_data).decode("utf-8") if image_data else None
        )

        post_data.append(
            {
                "user_id": user_id,
                "user_name": user_name,
                "image_base64": image_base64,
                "text": text,
            }
        )

    conn.close()

    return jsonify({"posts": post_data})


@app.route("/posts", methods=["POST"])
def create_post():
    # Assuming you have already established a connection and obtained the cursor

    # Execute a SELECT query to retrieve records from the Posts table

    user_id = request.form.get("userId")
    image = request.files.get("image")
    text = request.form.get("text")

    print(f"User ID: {user_id}")
    print(f"Text: {text}")

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)
        print("Image received and saved")

    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            image_path TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Added timestamp column
            FOREIGN KEY (user_id) REFERENCES NewUsers (id)
        )
    """
    )

    cursor.execute(
        "INSERT INTO Posts (user_id, text, image_path) VALUES (?, ?, ?)",
        (user_id, text, image_path if image else None),
    )

    conn.commit()

    return jsonify({"message": "Post created successfully"})


@app.route("/update-admin-data", methods=["POST"])
def update_admin_data():
    data = request.json

    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    # Rest of the code remains the same...
    user_id = data["user_id"]
    lives_in = data["lives_in"]
    relationship_status = data["relationship_status"]
    works_at = data["works_at"]
    user_name = data["user_name"]
    email = data["email"]
    date_of_birth = data["date_of_birth"]
    country = data["country"]
    city = data["city"]

    # Check if the user_id exists in the Bio table
    bio_query = "SELECT * FROM Bio WHERE user_id = ?"
    cursor.execute(bio_query, (user_id,))
    row = cursor.fetchone()

    if row:
        # Update Bio.db
        bio_db_query = "UPDATE Bio SET lives_in = ?, relationship_status = ?, works_at = ? WHERE user_id = ?"
        bio_db_params = (lives_in, relationship_status, works_at, user_id)
    else:
        # Insert into Bio.db
        bio_db_query = "INSERT INTO Bio (user_id, lives_in, relationship_status, works_at) VALUES (?, ?, ?, ?)"
        bio_db_params = (user_id, lives_in, relationship_status, works_at)

    # Update NewUsers.db
    new_users_db_query = "UPDATE NewUsers SET user_name = ?, email = ?, date_of_birth = ?, country = ?, city = ? WHERE id = ?"
    new_users_db_params = (user_name, email, date_of_birth, country, city, user_id)

    try:
        # Execute queries in NewUsers.db
        cursor.execute(new_users_db_query, new_users_db_params)
        # Execute queries in Bio.db
        cursor.execute(bio_db_query, bio_db_params)
        conn.commit()

        # Return success response
        return {"status": "success", "message": "User data updated successfully"}
    except Exception as e:
        # Return error response
        return {"status": "error", "message": str(e)}


@app.route("/get-user-name/<int:viewedProfileId>", methods=["GET"])
def get_user(viewedProfileId):
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    # Retrieve data for the specified viewedProfileId
    cursor.execute("SELECT * FROM NewUsers WHERE id = ?", (viewedProfileId,))
    user = cursor.fetchone()

    if user is not None:
        user_id = user[0]
        user_name = user[6]

        # Create a dictionary to store the user data
        user_data = {"user_id": user_id, "user_name": user_name}

        # Return the user data as JSON response
        return jsonify(user_data)
    else:
        # Return an error message if the user is not found
        return jsonify({"error": "User not found"})


@app.route("/get-all-users", methods=["GET"])
def get_all_users():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    # Retrieve data from NewUsers table
    cursor.execute("SELECT * FROM NewUsers")
    users = cursor.fetchall()

    # List to store the combined user data
    combined_data = []

    # Iterate over each user
    for user in users:
        user_id = user[0]
        email = user[1]
        password = user[2]
        date_of_birth = user[3]
        country = user[4]
        city = user[5]
        user_name = user[6]

        # Retrieve data from Bio table for the current user
        cursor.execute("SELECT * FROM Bio WHERE user_id = ?", (user_id,))
        bio_data = cursor.fetchone()
        relationship_status = bio_data[2] if bio_data else ""
        lives_in = bio_data[3] if bio_data else ""
        works_at = bio_data[4] if bio_data else ""

        # Retrieve data from ProfilePictures table for the current user
        cursor.execute(
            "SELECT profile_picture FROM ProfilePictures WHERE user_id = ?", (user_id,)
        )
        profile_picture_row = cursor.fetchone()
        profile_picture = (
            profile_picture_row[0] if profile_picture_row is not None else ""
        )

        # Create a dictionary to store the combined user data
        user_data = {
            "user_id": user_id,
            "email": email,
            "password": password,
            "date_of_birth": date_of_birth,
            "country": country,
            "city": city,
            "user_name": user_name,
            "relationship_status": relationship_status,
            "lives_in": lives_in,
            "works_at": works_at,
            "profile_picture": profile_picture,
        }

        # Add the user data to the combined data list
        combined_data.append(user_data)

    # Return the combined data as JSON response
    return jsonify(combined_data)


@app.route("/bio", methods=["POST"])
def update_bio():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    payload = request.data.decode("utf-8")  # Decode the bytes to a string
    data = json.loads(payload)
    user_id = data.get("id")
    rel = data.get("rel")
    loc = data.get("loc")
    work = data.get("work")
    edu = data.get("edu")
    gender = data.get("gender")
    marital_status = data.get("maritalStatus")
    interested_in_dating = data.get("interestedInDating")
    sexual_orientation = data.get("sexualOrientation")

    # Check if the user bio already exists
    cursor.execute("SELECT * FROM Bio WHERE user_id = ?", (user_id,))
    existing_bio = cursor.fetchone()

    if existing_bio:
        # Update the existing user bio
        cursor.execute(
            "UPDATE Bio SET relationship_status = ?, lives_in = ?, works_at = ?, education = ?, gender = ?, marital_status = ?, interested_in_dating = ?, sexual_orientation = ? WHERE user_id = ?",
            (rel, loc, work, edu, gender, marital_status, interested_in_dating, sexual_orientation, user_id),
        )
        conn.commit()
        return "User bio updated successfully"
    else:
        # Insert a new user bio
        cursor.execute(
            "INSERT INTO Bio (user_id, relationship_status, lives_in, works_at, education, gender, marital_status, interested_in_dating, sexual_orientation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, rel, loc, work, edu, gender, marital_status, interested_in_dating, sexual_orientation),
        )
        conn.commit()
        return "User bio added successfully"


@app.route("/bio", methods=["GET"])
def get_bio():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    # Get the user_id from the request
    user_id = request.args.get("user_id")

    # Check if the user_id exists
    if not user_id:
        return "Please provide a valid user_id"

    # Fetch the bio data for the given user_id
    cursor.execute("SELECT * FROM Bio WHERE user_id = ?", (user_id,))
    bio_data = cursor.fetchone()

    if bio_data:
        # Convert the bio data into a dictionary
        bio = {
            "user_id": bio_data[1],
            "relationship_status": bio_data[2],
            "lives_in": bio_data[3],
            "works_at": bio_data[4],
            "education": bio_data[5],
            "gender": bio_data[6],
            "marital_status": bio_data[7],
            "interested_in_dating": bio_data[8],
            "sexual_orientation": bio_data[9],
        }
        return jsonify(bio)
    else:
        return json.dumps({"message": "not found"})

@app.route("/add-friend", methods=["POST"])
def add_friend():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    if request.method == "POST":
        # Get the form data from the request
        payload = request.data.decode("utf-8")  # Decode the bytes to a string
        data = json.loads(payload)
        user_id = data.get("user_id")
        friend_id = data.get("friend_id")

        # Check if both user_id and friend_id exist
        if not user_id or not friend_id:
            return "Please provide user_id and friend_id"

        # Create a new table to store the friends data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                friend_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES NewUsers (id),
                FOREIGN KEY (friend_id) REFERENCES NewUsers (id)
            )
        """
        )
        # Check if the friendship already exists
        cursor.execute(
            "SELECT * FROM Friends WHERE user_id = ? AND friend_id = ?",
            (user_id, friend_id),
        )
        friendship = cursor.fetchone()

        if friendship:
            # Friendship already exists
            return "Friendship already exists"
        else:
            # Add the friendship to the Friends table
            cursor.execute(
                "INSERT INTO Friends (user_id, friend_id) VALUES (?, ?)",
                (user_id, friend_id),
            )
            conn.commit()
            return "Friend added successfully"

    return "Method Not Allowed"


@app.route("/get-followers", methods=["POST"])
def get_followers():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Get the user_id from the request
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        user_id = data.get("user_id")

        # Check if the user_id exists
        if not user_id:
            return json.dump({"error": "Please provide a valid user_id"})

        # Get the friends of the user from the Friends table
        cursor.execute(
            """
            SELECT NewUsers.id, NewUsers.user_name
            FROM Friends
            INNER JOIN NewUsers ON Friends.user_id = NewUsers.id
            WHERE Friends.friend_id = ?
        """,
            (user_id,),
        )
        friends = cursor.fetchall()

        # Convert the friends data into a list of dictionaries
        friends_data = []
        for friend in friends:
            friend_data = {"id": friend[0], "user_name": friend[1]}
            friends_data.append(friend_data)

        # Return the friends data as JSON response
        return friends_data

    return json.dump({"error": "Method Not Allowed"})


@app.route("/get-friends", methods=["POST"])
def get_friends():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Get the user_id from the request
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        user_id = data.get("user_id")

        # Check if the user_id exists
        if not user_id:
            return json.dump({"error": "Please provide a valid user_id"})

        # Get the friends of the user from the Friends table
        cursor.execute(
            """
            SELECT NewUsers.id, NewUsers.user_name
            FROM Friends
            INNER JOIN NewUsers ON Friends.friend_id = NewUsers.id
            WHERE Friends.user_id = ?
        """,
            (user_id,),
        )
        friends = cursor.fetchall()

        # Convert the friends data into a list of dictionaries
        friends_data = []
        for friend in friends:
            friend_data = {"id": friend[0], "user_name": friend[1]}
            friends_data.append(friend_data)

        # Return the friends data as JSON response
        return friends_data

    return json.dump({"error": "Method Not Allowed"})


@app.route("/upload-profile-picture", methods=["POST"])
def upload_profile_picture():
    if request.method == "POST":
        # Check if the uploaded file is present in the request
        if "file" not in request.files:
            return "No file uploaded"

        # Get the user ID from the request (you can modify this based on your frontend implementation)
        user_id = request.form.get("user_id")

        file = request.files["file"]

        # Check if a file with a valid extension is being uploaded
        if file.filename == "":
            return "No file selected"

        if not allowed_file(file.filename):
            return "Invalid file type"

        # Generate a secure filename and save the file in the desired location
        filename = secure_filename(file.filename)
        file.save(os.path.join("assets", filename))

        # Check if the user already has a profile picture
        conn = sqlite3.connect("NewUsers.db")
        cursor = conn.cursor()

        # Create the ProfilePictures table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ProfilePictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                profile_picture TEXT,
                FOREIGN KEY (user_id) REFERENCES NewUsers (id)
            )
        """
        )

        cursor.execute("SELECT * FROM ProfilePictures WHERE user_id = ?", (user_id,))
        existing_picture = cursor.fetchone()

        if existing_picture:
            # User already has a profile picture, update the existing record
            cursor.execute(
                "UPDATE ProfilePictures SET profile_picture = ? WHERE user_id = ?",
                (filename, user_id),
            )
        else:
            # User doesn't have a profile picture, insert a new record
            cursor.execute(
                "INSERT INTO ProfilePictures (user_id, profile_picture) VALUES (?, ?)",
                (user_id, filename),
            )

        conn.commit()
        conn.close()

        # Return a success message or redirect to another page
        return filename

    return "Method Not Allowed"


@app.route("/profile-picture/<user_id>")
def serve_profile_picture(user_id):
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT profile_picture FROM ProfilePictures WHERE user_id = ?", (user_id,)
    )
    result = cursor.fetchone()

    if result:
        filename = result[0]
        directory = os.path.abspath("assets")
        return send_from_directory(directory, filename)
    else:
        return "Profile picture not found"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# @app.route('/profile-picture/<filename>')
# def serve_profile_picture(filename):
#     directory = os.path.abspath('assets')
#     return send_from_directory(directory, filename)


@app.route("/update-profile-picture/<filename>/<id>")
def change_profile_picture(filename, id):
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT profile_picture FROM ProfilePictures WHERE user_id = ?", (id,)
    )
    result = cursor.fetchone()
    directory = os.path.abspath("assets")
    return send_from_directory(directory, filename)


@app.route("/search", methods=["GET"])
def search_profiles():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    query = request.args.get("query")  # Get the search query from the URL parameter
    if query == "":
        return []
    # Perform the search operation based on the query
    cursor.execute(
        "SELECT * FROM NewUsers WHERE user_name LIKE ?", ("%" + query + "%",)
    )
    profiles = cursor.fetchall()

    # Convert the profiles data into a list of dictionaries
    profiles_data = []
    for profile in profiles:
        profile_data = {
            "id": profile[0],
            "email": profile[1],
            "password": profile[2],
            "date_of_birth": profile[3],
            "country": profile[4],
            "city": profile[5],
            "user_name": profile[6],
        }
        profiles_data.append(profile_data)

    # Return the profiles data as JSON response
    return json.dumps(profiles_data)


@app.route("/suggest", methods=["GET"])
def get_user_names():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()

    if request.method == "GET":
        cursor.execute("SELECT user_name FROM NewUsers")
        user_names = [row[0] for row in cursor.fetchall()]
        return json.dumps(user_names)

    return "Method Not Allowed"


@app.route("/check-email", methods=["POST"])
def check_email():
    if request.method == "POST":
        # Get the email from the request
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        email = data.get("email")

        # Create a new database connection and cursor
        conn = sqlite3.connect("NewUsers.db")
        cursor = conn.cursor()

        # Check if the email exists in the database
        cursor.execute("SELECT EXISTS(SELECT 1 FROM NewUsers WHERE email = ?)", (email,))
        exists = cursor.fetchone()[0] == 1

        if exists:
            # Get the security question for the user
            cursor.execute("SELECT question FROM NewUsers WHERE email = ?", (email,))
            question = cursor.fetchone()[0]

            # Close the database connection and cursor
            cursor.close()
            conn.close()

            # Return the response with the question
            return jsonify({"exists": exists, "question": question})
        else:
            # Close the database connection and cursor
            cursor.close()
            conn.close()

            return jsonify({"exists": exists})

    return "Method Not Allowed"

@app.route("/validate-answer", methods=["POST"])
def validate_answer():
    if request.method == "POST":
        # Get the answer and email from the request
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        answer = data.get("answer")
        email = data.get("email")

        # Create a new database connection and cursor
        conn = sqlite3.connect("NewUsers.db")
        cursor = conn.cursor()

        # Check if the email exists in the database
        cursor.execute("SELECT EXISTS(SELECT 1 FROM NewUsers WHERE email = ?)", (email,))
        exists = cursor.fetchone()[0] == 1

        if exists:
            # Get the actual answer from the database for comparison
            cursor.execute("SELECT answer FROM NewUsers WHERE email = ?", (email,))
            actual_answer = cursor.fetchone()[0]

            # Compare the provided answer with the actual answer
            if answer == actual_answer:
                # Close the database connection and cursor
                cursor.close()
                conn.close()
                print("valid answer")
                return jsonify({"valid": True})
        
        # Close the database connection and cursor
        cursor.close()
        conn.close()

    return jsonify({"valid": False})

@app.route("/update-password", methods=["POST"])
def update_password():
    if request.method == "POST":
        # Get the email and new password from the request
        payload = request.data.decode("utf-8")
        data = json.loads(payload)
        email = data.get("email")
        new_password = data.get("password")

        # Create a new database connection and cursor
        conn = sqlite3.connect("NewUsers.db")
        cursor = conn.cursor()

        # Update the password for the user
        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

        # Save the user data to the database
        cursor.execute("UPDATE NewUsers SET password = ? WHERE email = ?", (hashed_password.decode("utf-8"), email))
        conn.commit()

        # Close the database connection and cursor
        cursor.close()
        conn.close()

        # Return a success response
        return jsonify({"success": True})

    return "Method Not Allowed"

@app.route("/signin", methods=["POST"])
def signin():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    if request.method == "POST":
        # Get the form data from the request
        payload = request.data.decode("utf-8")  # Decode the bytes to a string
        data = json.loads(payload)
        email = data.get("email")
        password = data.get("password")

        cursor.execute("SELECT * FROM NewUsers WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            # User exists, verify the password
            stored_password = user[2]  # Get the stored hashed password from the database

            if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                # Password is correct
                user_data = {
                    "id": user[0],
                    "email": user[1],
                    "password": user[2],
                    "date_of_birth": user[3],
                    "country": user[4],
                    "city": user[5],
                    "user_name": user[6],
                }
                print(user_data)
                return json.dumps(user_data)
            else:
                # Incorrect password
                return jsonify({"message": "Invalid email or password"})


    return "Method Not Allowed"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    conn = sqlite3.connect("NewUsers.db")
    cursor = conn.cursor()
    if request.method == "POST":
        # Get the form data from the request
        payload = request.data.decode("utf-8")  # Decode the bytes to a string
        data = json.loads(payload)
        email = data.get("email")
        password = data.get("password")
        date_of_birth = data.get("dateOfBirth")
        country = data.get("country")
        city = data.get("city")
        user_name = data.get("userName")
        question = data.get("question")
        answer = data.get("answer")

        # Perform validation (add your validation logic here)
        if (
            not email
            or not password
            or not date_of_birth
            or not country
            or not city
            or not user_name
            or not question
            or not answer
        ):
            return "Please fill in all the required fields"

         # Hash the password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Save the user data to the database
        cursor.execute(
            "INSERT INTO NewUsers (email, password, date_of_birth, country, city, user_name, question, answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (email, hashed_password.decode("utf-8"), date_of_birth, country, city, user_name, question, answer),

        )
        conn.commit()
        if cursor.lastrowid:
            cursor.execute("SELECT * FROM NewUsers")
            rows = cursor.fetchall()
            print("Data inserted successfully. User ID:", cursor.lastrowid)
            # Data inserted successfully
            user_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM NewUsers WHERE email = ? AND password = ?",
                (email, hashed_password.decode("utf-8")),
            )
            user = cursor.fetchone()
            user_data = {
                "id": user[0],
                "email": user[1],
                "password": user[2],
                "date_of_birth": user[3],
                "country": user[4],
                "city": user[5],
                "user_name": user[6],
                "question": user[7],
                "answer": user[8],
            }
            print(user_data)
            return json.dumps(user_data)
        else:
            print("Failed to insert data into the database.")

    # Render the signup page template for GET requests
    return render_template("signup.html")



if __name__ == "__main__":
    app.run(debug=True)
