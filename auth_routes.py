"""
This module contains all the routes related to authorization/authentication
"""

import os
import re
import secrets
import sqlite3

from datetime import datetime, timedelta
from flask import Blueprint, flash, g, get_flashed_messages, redirect, render_template, request, session, url_for
from flask import current_app as app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from preppydb import db_session
from helpers import apology
from dbmodels import Families, Tokens, Users
from utils import mail

auth_routes = Blueprint('auth_routes', __name__)


@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        has_error = False

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please provide username.")
            has_error = True

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("Please provide password.")
            has_error = True

        # Query database for username
        if not has_error:
            try:
                user = db_session.query(Users).filter_by(
                    username=request.form.get("username")).first()
            except SQLAlchemyError as e:
                app.logger.error("Database error: %s", e)
                has_error = True

            # Ensure username exists and password is correct
            if not user or not check_password_hash(
                user.hash, request.form.get("password")
            ):
                flash("Invalid username and/or password.")
                has_error = True

        # Remember which user has logged in
        if not has_error:
            session["user_id"] = user.id

            # Remember user's last name
            try:
                last_name = db_session.query(Families.last_name).filter_by(
                    user_id=session['user_id']).scalar()
            except SQLAlchemyError as e:
                app.logger.error("Database error: %s", e)
                has_error = True
            if last_name:
                session['last_name'] = last_name

        # Redirect user to home page
        if not has_error:
            return redirect(url_for('index'))

        # Or back to login if errors
        return redirect(url_for('auth_routes.login'))

    print(get_flashed_messages)
    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html", nonce=g.nonce)


@auth_routes.route("/forgot", methods=['GET', 'POST'])
def forgot():
    """
    Route allows user to request password reset token
    """

    if request.method == 'POST':
        errors = []
        has_error = False

        if not request.form.get('username'):
            errors.append("Please provide a valid email.")
            has_error = True
        email = request.form.get('username')
        user_id = None

        try:
            user_id = db_session.query(Users.id).filter_by(username=email).scalar()
        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            errors.append("Error accessing user id.")
            has_error = True
        if not user_id:
            errors.append("No such user.")
            has_error = True
        if has_error:
            return apology(" ".join(errors))

        token = secrets.token_urlsafe(16)

        try:
            # Delete old tokens
            db_session.query(Tokens).filter_by(user_id=user_id).delete()

            # Insert new token
            new_token = Tokens(user_id=user_id, token=token, timestamp=datetime.now())
            db_session.add(new_token)
            db_session.commit()

            # Send message with new token
            msg = Message('Your token', sender=os.getenv(
                'MAIL_USERNAME'), recipients=[email])
            msg.body = f"Your token is: {token}"
            mail.send(msg)

        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error creating and sending token.")
            has_error = True
        if has_error:
            return apology(" ".join(errors))
        return redirect(url_for('auth_routes.verify'))

    return render_template('forgot.html', nonce=g.nonce)


@auth_routes.route("/verify", methods=['GET', 'POST'])
def verify():
    """
    Route verifies the user's password reset token
    """

    if request.method == 'POST':
        errors = []

        entered_token = request.form.get('token')
        if not entered_token:
            errors.append("Please enter a valid token.")
        else:
            try:
                stored_timestamp = db_session.query(
                    Tokens.user_id, Tokens.timestamp).filter_by(token=entered_token).first()
            except SQLAlchemyError as e:
                app.logger.error("Database error: %s", e)
                errors.append("Error accessing stored timestamp.")
            if stored_timestamp:
                stored_time = stored_timestamp[1]
                if datetime.now() - stored_time > timedelta(minutes=10):
                    errors.append("Your token has expired.")
                else:
                    session['user_id'] = stored_timestamp[0]
            else:
                errors.append("Not a valid token")
        if errors:
            flash(" ".join(errors))
            return redirect(url_for('auth_routes.verify'))

        return redirect(url_for('auth_routes.reset'))

    return render_template("verify.html", nonce=g.nonce)


@auth_routes.route("/reset", methods=['GET', 'POST'])
def reset():
    """
    Route allows users to set a new password upon recovery
    """

    if request.method == 'GET':
        if "user_id" not in session:
            flash("Session expired or invalid.")
            return redirect(url_for('auth_routes.verify'))
        return render_template("reset.html", nonce=g.nonce)

    # check for errors
    has_error = False
    errors = []

    if "user_id" not in session:
        flash("Session expired or invalid.")
        return redirect(url_for('auth_routes.verify'))

    if not request.form.get("password"):
        errors.append("Password required.")
        has_error = True

    else:
        if not request.form.get("confirmation"):
            errors.append("Confirmation of password required.")
            has_error = True
        else:
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")

            if password != confirmation:
                errors.append("Password confirmation doesn't match.")
                has_error = True

    if has_error:
        flash(" ".join(errors))
        return redirect(url_for('auth_routes.reset'))

    try:
        username = db_session.query(Users.username).filter_by(id=session['user_id']).scalar()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error accessing username.")

    if not username:
        errors.append("No such username.")
        has_error = True

    # hash password
    hashpass = generate_password_hash(password)

    # insert into user table and log user in
    if not has_error:
        try:
            db_session.query(Users).filter_by(id=session['user_id']).update({'hash': hashpass})
            db_session.commit()
            session['last_name'] = db_session.query(
                Families.last_name).filter_by(user_id=session['user_id']).scalar()
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error adding password.")
            has_error = True

    return apology(" ".join(errors))


@auth_routes.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for('index'))


@auth_routes.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        has_error = False

        # check for errors
        errors = []

        if not request.form.get("username"):
            errors.append("Username required.")
            has_error = True
        if not request.form.get("password"):
            errors.append("Password required.")
            has_error = True
        if not request.form.get("confirmation"):
            errors.append("Password confirmation required.")
            has_error = True

        entered_username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check password confirmation
        if password != confirmation:
            errors.append("Password confirmation doesn't match.")
            has_error = True
        if has_error:
            flash(" ".join(errors))
            return redirect(url_for('auth_routes.register'))

        # Check if username already in db
        try:
            username = db_session.query(Users.username).filter_by(username=entered_username).first()
        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            errors.append("Error checking username.")

        if username is not None:
            errors.append("Username already exists.")
            has_error = True

        if has_error:
            flash(" ".join(errors))
            return redirect(url_for('auth_routes.register'))

        # hash password
        hashpass = generate_password_hash(password)

        # insert into user table
        try:
            new_user = Users(username=entered_username, hash=hashpass)
            db_session.add(new_user)
            db_session.commit()
        except sqlite3.Error as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error adding new user.")

        # log user in
        try:
            session['user_id'] = db_session.query(Users.id).filter_by(
                username=entered_username).scalar()

        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            errors.append("Error setting user id.")
        if errors:
            return apology(" ".join(errors))

        return redirect(url_for('index'))

    # if requested via get, display registration form
    return render_template("register.html", nonce=g.nonce)


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None
