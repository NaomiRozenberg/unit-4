import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from tools import DatabaseBridge
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password = hash_password(password)
        db = DatabaseBridge('database.db')
        existing_user = db.search(f"SELECT * FROM users WHERE email='{email}'", False)
        if existing_user:
            db.close()
            return "Error: email already exists"
        try:
            db.run_query(f'''INSERT INTO users (username, email, password) VALUES 
            ('{username}', '{email}', '{hashed_password}');''')
        except Exception as e:
            db.close()
            return f"An error occurred: {e}"
        db.close()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        db = DatabaseBridge('database.db')
        user = db.search(f"SELECT * FROM users WHERE email='{email}'", False)
        if user:
            if user[3] == hash_password(password):
                session['user_id'] = user[0]
                db.close()
                return redirect('/forums')
            else:
                error_message = "Incorrect password. Please try again."
                db.close()
                return render_template('login.html', error_message=error_message)
        else:
            error_message = "User not found. Please sign up."
            db.close()
            return render_template('login.html', error_message=error_message)
    return render_template('login.html')

@app.route('/forums')
def main_page():
    db = DatabaseBridge('database.db')
    query = """
    SELECT discussion_forums.id, discussion_forums.title, ib_groups.name, 
           (SELECT COUNT(*) FROM forum_follows WHERE followed_forum_id = discussion_forums.id) AS follower_count
    FROM discussion_forums 
    JOIN ib_groups ON discussion_forums.group_id = ib_groups.id
    """
    forums = db.search(query, True)
    db.close()
    return render_template('main_page.html', forums=forums)

@app.route('/follow_forum/<int:forum_id>', methods=['POST'])
def follow_forum(forum_id):
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        existing_follow = db.search(f"SELECT * FROM forum_follows WHERE user_id={user_id} AND followed_forum_id={forum_id}", False)
        if not existing_follow:
            db.run_query(f"INSERT INTO forum_follows (user_id, followed_forum_id) VALUES ({user_id}, {forum_id})")
        db.close()
    return redirect(request.referrer)

@app.route('/unfollow_forum/<int:forum_id>', methods=['POST'])
def unfollow_forum(forum_id):
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        try:
            db.run_query(f"DELETE FROM forum_follows WHERE user_id={user_id} AND followed_forum_id={forum_id}")
        except Exception as e:
            print(f"Error unfollowing forum: {e}")
        db.close()
    return redirect(request.referrer)


@app.route('/forums/<int:forum_id>', methods=['GET'])
def see_forum(forum_id):
    db = DatabaseBridge('database.db')

    # Get the user_id from the session
    user_id = session.get('user_id', None)

    posts_query = f"""
    SELECT posts.id, posts.post_title, posts.post_text, posts.post_date, posts.user_name, COUNT(likes.id) AS like_count,
           (SELECT COUNT(*) FROM likes WHERE post_id = posts.id AND user_id = {user_id}) AS user_liked
    FROM posts
    LEFT JOIN likes ON posts.id = likes.post_id
    WHERE posts.forum_id = {forum_id}
    GROUP BY posts.id, posts.post_title, posts.post_text, posts.post_date, posts.user_name
    """
    posts = db.search(posts_query, True)

    follow_count_query = f"SELECT COUNT(*) FROM forum_follows WHERE followed_forum_id = {forum_id}"
    follow_count = db.search(follow_count_query, False)[0]

    followers_query = f"""
    SELECT users.username
    FROM forum_follows
    JOIN users ON forum_follows.user_id = users.id
    WHERE forum_follows.followed_forum_id = {forum_id}
    """
    followers = db.search(followers_query, True)

    db.close()
    return render_template('forum.html', posts=posts, forum_id=forum_id, follow_count=follow_count, followers=followers)


@app.route('/forums/<int:forum_id>/<int:post_id>', methods=['GET'])
def see_post(forum_id, post_id):
    db = DatabaseBridge('database.db')
    post_query = f"SELECT * FROM posts WHERE id={post_id}"
    post = db.search(post_query, False)
    like_count_query = f"SELECT COUNT(*) FROM likes WHERE post_id={post_id}"
    like_count = str(db.search(like_count_query, False)).replace('(', '').replace(')', '').replace(',', '')
    comments_query = f"SELECT comments.id, comments.comment_text, comments.comment_date, users.username FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id={post_id}"
    comments = db.search(comments_query, True)
    db.close()
    if post and like_count:
        return render_template('post.html', post=post, like_count=like_count, forum_id=forum_id, comments=comments)
    else:
        return "Post not found", 404

@app.route('/like_post/<int:forum_id>/<int:post_id>', methods=['POST'])
def like_post(forum_id, post_id):
    db = DatabaseBridge('database.db')
    if 'user_id' in session:
        user_id = session['user_id']
        existing_like = db.search(f"SELECT * FROM likes WHERE post_id={post_id} AND user_id={user_id}", False)
        if existing_like:
            try:
                db.run_query(f"DELETE FROM likes WHERE post_id={post_id} AND user_id={user_id}")
            except Exception as e:
                print(f"Error removing like: {e}")
        else:
            try:
                db.run_query(f"INSERT INTO likes (post_id, user_id) VALUES ({post_id}, {user_id})")
            except Exception as e:
                print(f"Error inserting like: {e}")
    else:
        print("User ID not found in session")
    db.close()
    referrer_url = request.referrer
    if referrer_url:
        return redirect(referrer_url)
    else:
        return redirect(url_for('see_forum', forum_id=forum_id))

@app.route('/add_comment/<int:forum_id>/<int:post_id>', methods=['POST'])
def add_comment(forum_id, post_id):
    if 'user_id' in session:
        user_id = session['user_id']
        comment_text = request.form['comment']
        db = DatabaseBridge('database.db')
        try:
            db.run_query(f"INSERT INTO comments (post_id, user_id, comment_text) VALUES ({post_id}, {user_id}, '{comment_text}')")
        except Exception as e:
            print(f"Error adding comment: {e}")
        db.close()
    else:
        print("User ID not found in session")
    return redirect(url_for('see_post', forum_id=forum_id, post_id=post_id))

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        comment = db.search(f"SELECT * FROM comments WHERE id={comment_id} AND user_id={user_id}", False)
        if comment:
            post_id = comment[1]
            forum_id_result = db.search(f"SELECT forum_id FROM posts WHERE id={post_id}", False)
            if forum_id_result:
                forum_id = forum_id_result[0]
                if request.method == 'POST':
                    new_comment_text = request.form.get('new_comment_text').strip()
                    new_comment_text = new_comment_text.replace('\r', '').replace('\n', '')
                    if new_comment_text:
                        try:
                            db.run_query(f"UPDATE comments SET comment_text='{new_comment_text}' WHERE id={comment_id}")
                            db.close()
                            return redirect(url_for('see_post', forum_id=forum_id, post_id=post_id))
                        except Exception as e:
                            db.close()
                            return "Error updating comment"
                    else:
                        db.close()
                        return "New comment text is empty"
                comment_text = comment[3].strip().replace('\r', '').replace('\n', '')
                comment = (*comment[:3], comment_text, *comment[4:])
                db.close()
                return render_template('edit_comment.html', comment=comment)
            else:
                db.close()
                return "Associated forum not found."
        else:
            db.close()
            return "Comment not found or you are not authorized to edit this comment."
    return redirect(url_for('login'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        comment = db.search(f"SELECT * FROM comments WHERE id={comment_id} AND user_id={user_id}", False)
        if comment:
            try:
                db.run_query(f"DELETE FROM comments WHERE id={comment_id}")
            except Exception as e:
                print(f"Error deleting comment: {e}")
            db.close()
            return redirect(request.referrer)
        else:
            return "You are not authorized to delete this comment."
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        db = DatabaseBridge('database.db')
        user_info = db.search(f"SELECT * FROM users WHERE id={user_id}", False)
        db.close()
        return render_template('profile.html', user_info=user_info)
    else:
        return redirect(url_for('login'))

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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def update_user_picture(user_id, filename):
    db = DatabaseBridge('database.db')
    try:
        db.run_query(f"UPDATE users SET profile_picture='{filename}' WHERE id={user_id}")
    except Exception as e:
        app.logger.error(f"Error updating user profile picture: {e}")
    db.close()

def upload_picture():
    if 'user_id' not in session:
        flash('You must be logged in to upload a profile picture', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    if 'profile_picture' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('edit_profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('edit_profile'))

    if file and allowed_file(file.filename):
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f'profile_{user_id}.{extension}'  # Construct new filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
            update_user_picture(user_id, filename)
            flash('Profile picture updated successfully', 'success')
        except Exception as e:
            app.logger.error(f"Error uploading profile picture: {e}")
            flash('An error occurred while uploading the profile picture. Please try again later.', 'error')
    else:
        flash('Invalid file format. Allowed formats: jpeg, jpg, png', 'error')

    return redirect(url_for('edit_profile'))

@app.route('/users')
def user_list():
    db = DatabaseBridge('database.db')
    query = """
    SELECT users.id, users.username, 
           (SELECT COUNT(*) FROM user_follows WHERE followed_id = users.id) AS follower_count
    FROM users
    """
    users = db.search(query, True)
    db.close()
    return render_template('user_list.html', users=users)


@app.route('/follow_user/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    if 'user_id' in session:
        follower_id = session['user_id']
        db = DatabaseBridge('database.db')
        existing_follow = db.search(f"SELECT * FROM user_follows WHERE follower_id={follower_id} AND followed_id={user_id}", False)
        if not existing_follow:
            try:
                db.run_query(f"INSERT INTO user_follows (follower_id, followed_id) VALUES ({follower_id}, {user_id})")
            except Exception as e:
                print(f"Error following user: {e}")
        db.close()
    return redirect(request.referrer)

@app.route('/unfollow_user/<int:user_id>', methods=['POST'])
def unfollow_user(user_id):
    if 'user_id' in session:
        follower_id = session['user_id']
        db = DatabaseBridge('database.db')
        try:
            db.run_query(f"DELETE FROM user_follows WHERE follower_id={follower_id} AND followed_id={user_id}")
        except Exception as e:
            print(f"Error unfollowing user: {e}")
        db.close()
    return redirect(request.referrer)


if __name__ == '__main__':
    app.run(debug=True)
