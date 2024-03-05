"""Flask app for adopt app."""

import os

from flask import Flask, redirect, render_template, flash, session

from models import db, connect_db, User

from forms import RegisterUserForm, LoginUserForm, CSRFProtectForm

USERNAME_KEY = 'username'

app = Flask(__name__)

app.config['SECRET_KEY'] = "secret"

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "postgresql:///notes")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)


@app.get('/')
def redirect_to_register():
    """Redirects to register page"""
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def add_user():
    """Show register form and handle user registration"""

    form = RegisterUserForm()

    if form.validate_on_submit():

        new_user = User.register(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )

        # want commit in view function so that if we do other database operations after adding user, we can use just a single commit total
        db.session.add(new_user)
        db.session.commit()

        session[USERNAME_KEY] = new_user.username

        flash("Registration successful!")
        return redirect(f"/users/{new_user.username}")

    else:
        return render_template("register_form.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Shows login form and handles user login"""

    form = LoginUserForm()

    if form.validate_on_submit():

        user = User.authenticate(
            username=form.username.data,
            password=form.password.data
        )

        if user:
            session[USERNAME_KEY] = user.username

            return redirect(f"/users/{user.username}")

        else:
            form.username.errors = ['Invalid username/password.']

    else:
        return render_template('login_form.html', form=form)

@app.get('/users/<username>')
def display_user_info(username):
    """Displays user info (excluding password)"""
    if USERNAME_KEY in session:
        if session[USERNAME_KEY] == username:
            user = User.query.get_or_404(username)
            form = CSRFProtectForm()
            return render_template('user.html', user=user, form=form)

        else:
            # could add functionality to throw error page for nonexisting users
            flash("Cannot access other user's information!")
            return redirect(f'/users/{session[USERNAME_KEY]}')

    else:
        flash('You must be logged in to view user information!')
        return redirect('/login')

@app.post('/logout')
def logout():
    """Logs out current user in session"""

    form = CSRFProtectForm()

    if form.validate_on_submit():
        session.pop(USERNAME_KEY, None)

        flash('Successfully logged out!')
        return redirect('/login')
