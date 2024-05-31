Criteria C: Development

Login System
My client required a login system for the application where different users can have their unique profile pages and post the comments. I initially decided to use cookies as a way of storing when a user is logged in. The code below shows my first attempt and I will explain in detail below:
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
This code is run when the request from the client received by the server is of type POST if request.method == 'POST'. This happens when the user clicks on the login button on the index.html page. Then, I proceed to get the variables from the login form including the name and password, this is contained in the dictionary request. After checking the database with the SQL query ##’(“”(“‘“)’)... Then I set the cookie for the user with the code response.set_cookie('user_id',f"{user_id}"), note that the cookie is like a dictionary with key and values both strings. I used a f-string to convert the id which is an integer to a string.

However, based on my research about cookies and testing in the browser, I found out that the cookie is not a secure way of storing the user information since this is a variable stored in the browser on the client side, which can be easily changed causing identity theft if not hashed. So my solution to this issue was to change from client to server side by using sessions.  The code below shows that I could store the current user in the dictionary session, “The data that is required to be saved in the Session is stored in a temporary directory on the server.” “The data in the Session is stored on the top of cookies and signed by the server cryptographically.” [Ref 1]


py'''session['current_user'] = users[username]'''

In order to use the session variable I needed to define an initial secret in the variable of the Flask application, I did this in the code below and generated a random string as secure key 

app = Flask(__name__)
app.secret_key = "super_secret_key"


In order to keep passwords encrypted, the most efficient way to do so is by Hashing them. “Hashing gives a more secure and adjustable method of retrieving data compared to any other “[ref 2]. And that is why I have decided to hash the passwords 
