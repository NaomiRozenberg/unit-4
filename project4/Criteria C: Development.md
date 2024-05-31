Criteria C: Development

Login System
My client required a login system for the application where different users can have their unique profile pages and post the comments. I initially decided to use cookies as a way of storing when a user is logged in. The code below shows my first attempt and I will explain in detail below:
```py
if request.method == 'POST':
   uname = request.form.get('uname')
   password = request.form.get('psw')

   #Check database for user, then compare hash of password
   if uname == "bob":
       # valid login, create a cookie
       user_id = 1
       response = make_response(redirect(url_for('get_all_food')))
       response.set_cookie('user_id',f"{user_id}")
       return response
```

This code is run when the request from the client received by the server is of type POST if ```pyrequest.method == 'POST'```. This happens when the user clicks on the login button on the index.html page. Then, I proceed to get the variables from the login form including the name and password, this is contained in the dictionary request. After checking the database with the SQL query ##’(“”(“‘“)’)... Then I set the cookie for the user with the code ```pyresponse.set_cookie('user_id',f"{user_id}")```.

However, based on my research about cookies and testing in the browser, I found out that the cookie is not a secure way of storing the user information since this is a variable stored in the browser on the client side, which can be easily changed causing identity theft if not hashed. So my solution to this issue was to change from client to server side by using sessions.  The code below shows that I could store the current user in the dictionary session, “The data that is required to be saved in the Session is stored in a temporary directory on the server.” “The data in the Session is stored on the top of cookies and signed by the server cryptographically.” [Ref 1]


py```session['current_user'] = users[username]```

In order to use the session variable I needed to define an initial secret in the variable of the Flask application, I did this in the code below and generated a random string as secure key 

py```app = Flask(__name__)
app.secret_key = "super_secret_key"```


In order to keep passwords encrypted, the most efficient way to do so is by Hashing them. “Hashing gives a more secure and adjustable method of retrieving data compared to any other “[Ref 2]. And that is why I have decided to hash the passwords, as shown below:
py```def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()```
This function hashes passwords using SHA-256 before storing them in the database, adding a layer of security. Anthor imported matter is that the password is hashed and only than stored, so that the system won't need to debug it. 


**User Registration (Signup)**
py```@app.route('/signup', methods=['GET', 'POST'])```
The route handles both GET and POST methods, which means that the user can actually uplod their information into the database. 

In addtion to that database operations checks wheather the email alreday exists it inserts new user data, and handles errors.
```py
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

```py
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
```
In the code above I have chossen to clear the session in order to log out. It is to make sure that as the session clears out so does the user. And ensures privicy to the user. 

**Picture upload**

My client had asked for users to have the abilty to upload pictures. 
First I had to make a file upload configyration
```py
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```
[Raf 3]
And afterwards I have takeld the issue of profile picture uploading. 

```py
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
Firstly, It checks the session - to make sure that user is logged in 
Secondly, It retrieves the user information in order to edit profile page
Theridly it handles the Posting of the picture file


**File Upload Handling**

The File validation Ensures a file is selected and checks that the file extension is allowed.

```py
    if 'profile_picture' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('edit_profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('edit_profile'))
```

File naming is very imported to the program as whole in order to know where does the file belong espacially for profile pictures such as in this program. 

```py
    if file and allowed_file(file.filename):
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f'profile_{user_id}.{extension}'  # Construct new filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
```
File Saving which saves the file to the designated upload directory and handles any errors that may occur during this process, is showen below

```py
try:
            file.save(file_path)
            update_user_picture(user_id, filename)
            flash('Profile picture updated successfully', 'success')
```

**The uage of Tailwind CSS in the Forum Application**
Tailwind CSS is a utility-first CSS framework. It is  customizable and helps with createung responsive and modern UI designs quickly. Here's an overview of how Tailwind CSS is used in the forum application.

In order to intgrate it,
first I had to add it into the head of each .html file. 

```html
<script src="https://cdn.tailwindcss.com"></script>
```
and than look throgh the website's documuntation [Raf 4] and add classes to diffrent divs in my html files such as in the example below. 

```html
<div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
```











References:
1. https://www.geeksforgeeks.org/how-to-use-flask-session-in-python-flask/
2. https://www.geeksforgeeks.org/importance-of-hashing/
3. https://www.geeksforgeeks.org/how-to-upload-file-in-python-flask/
4. https://tailwindcss.com/docs/installation


