from flask import Flask, request, redirect, render_template, flash, session
from flask_debugtoolbar import DebugToolbarExtension 
from forms import RegisterUserForm, LoginForm, FeebackForm
from models import db, connect_db, User, Feedback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = 'lol_secret_key'

app.app_context().push()

debug = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

@app.route('/')
def root():
    """homepage"""
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """User Sign up"""
    form = RegisterUserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = new_user.username
        flash('Account created successfully!')
        return redirect(f'/users/{new_user.username}')
    else:    
        return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    """User Login"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f'Welcome Back {user.username}')
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid Username/Password']

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/users/<username>')
def display_user(username):
    """only logged in users can visit this page"""
    if 'username' not in session or username != session['username']:
        flash('Please login to view')
        return redirect('/')

    user = User.query.get_or_404(username)
    return render_template('display_user.html', user=user)

@app.route('/users/<username>/delete')
def delete_user(username):
    """only logged in users can visit this page"""
    if 'username' not in session or username != session['username']:
        flash('Not allowed to delete user')
        return redirect('/')
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop('username')
    return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def create_feedback(username):
    user = User.query.get_or_404(username)
    form = FeebackForm()
    if 'username' not in session or username != session['username']:
        flash('Must Log in to post feedback')
        return redirect('/')
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        username = session['username']
        feedback = Feedback(title=title, content=content, username=username)
        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/users/{user.username}')
    return render_template('create_feedback.html', user=user, form=form)

@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.username
    form = FeebackForm(obj=feedback)
    if 'username' not in session or username != session['username']:
        flash('Must Log in to edit feedback')
        return redirect('/')
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/users/{feedback.username}')
    return render_template('edit_feedback.html',form=form, feedback=feedback)
    
@app.route('/feedback/<int:feedback_id>/delete')
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    username = feedback.username
    if 'username' not in session or username != session['username']:
        flash('Must be logged in to delete feedback')
        redirect('/login')
    db.session.delete(feedback)
    db.session.commit()
    return redirect(f'/users/{username}')