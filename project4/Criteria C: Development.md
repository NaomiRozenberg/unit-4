
---

**Criteria C: Development**

**Login System**

My client required a login system for the application, allowing different users to have unique profile pages and post comments. I initially decided to use cookies to store the login state of a user. The code below shows my first attempt, followed by a detailed explanation:

```python
if request.method == 'POST':
   uname = request.form.get('uname')
   password = request.form.get('psw')

   # Check database for user, then compare hash of password
   if uname == "bob":
       # Valid login, create a cookie
       user_id = 1
       response = make_response(redirect(url_for('get_all_food')))
       response.set_cookie('user_id', f"{user_id}")
       return response
```

This code runs when the request method is POST, triggered by the user clicking the login button on the index.html page. It retrieves the username and password from the login form and checks the database for a matching user. If the login is valid, it sets a cookie to store the user ID.

However, through research and browser testing, I found that cookies are not a secure way to store user information, as they can be easily altered, leading to identity theft. To address this issue, I switched to using sessions, which store data on the server side. The code below demonstrates this approach:

```python
session['current_user'] = users[username]
```

To use the session variable, I defined a secret key in the Flask application:

```python
app = Flask(__name__)
app.secret_key = "super_secret_key"
```

To ensure passwords are securely stored, I implemented hashing using SHA-256:

```python
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
```

This function hashes passwords before storing them in the database, enhancing security.

**User Registration (Signup)**

The signup route handles both GET and POST methods, allowing users to register by entering their information into the database:

```python
@app.route('/signup', methods=['GET', 'POST'])
```

Database operations check if the email already exists, and if not, insert the new user data:

```python
username = request.form['username']
password = request.form['password']
email = request.form['email']
hashed_password = hash_password(password)
db = DatabaseBridge('database.db')
existing_user = db.search(f"SELECT * FROM users WHERE email='{email}'", False)
if existing_user:
    db.close()
    return "Error: email already exists"
```

**Log Out**

To log out, I clear the session to ensure the user is logged out and their privacy is maintained:

```python
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
```

**Picture Upload**

My client requested the ability for users to upload pictures. First, I configured file upload settings:

```python
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

Then, I tackled profile picture uploading:

```python
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        user_info = db.search(f"SELECT * FROM users WHERE id={user_id}", False)
        db.close()
        if request.method == 'POST':
            if 'profile_picture' in request.files:
                upload_picture()  # Handle file upload
            return redirect(url_for('profile'))
        return render_template('edit_profile.html', user_info=user_info, user_id=user_id)
    else:
        return redirect(url_for('login'))
```

This route ensures the user is logged in, retrieves user information, and handles the posting of picture files.

**File Upload Handling**

File validation ensures a file is selected and the file extension is allowed:

```python
if 'profile_picture' not in request.files:
    flash('No file part', 'error')
    return redirect(url_for('edit_profile'))

file = request.files['profile_picture']

if file.filename == '':
    flash('No selected file', 'error')
    return redirect(url_for('edit_profile'))
```

File naming is crucial for organizing profile pictures:

```python
if file and allowed_file(file.filename):
    extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f'profile_{user_id}.{extension}'  # Construct new filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
```

File saving saves the file to the designated upload directory and handles any errors:

```python
try:
    file.save(file_path)
    update_user_picture(user_id, filename)
    flash('Profile picture updated successfully', 'success')
```

**Using Tailwind CSS in the Forum Application**

Tailwind CSS is a utility-first CSS framework that helps create responsive and modern UI designs quickly. To integrate it, I added the following to the head of each .html file:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

I then referred to the documentation and added classes to various divs in my HTML files:

```html
<div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
```

---

**References:**

1. [GeeksforGeeks: How to use Flask Session in Python Flask](https://www.geeksforgeeks.org/how-to-use-flask-session-in-python-flask/)
2. [GeeksforGeeks: Importance of Hashing](https://www.geeksforgeeks.org/importance-of-hashing/)
3. [GeeksforGeeks: How to Upload File in Python Flask](https://www.geeksforgeeks.org/how-to-upload-file-in-python-flask/)
4. [Tailwind CSS Documentation](https://tailwindcss.com/docs/installation)

---



