"""
Module contains helper functions and initializations
"""

import os

from functools import wraps

from flask import g
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

from dbmodels import States
from preppydb import db_session

mail = Mail()

# Secret key for password reset
secret_key = os.getenv('SECRET_KEY')


def load_states(f):
    """
    Provides list of U.S. states to all routes that need it
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.states = [row.state for row in db_session.query(States.state).all()]
        return f(*args, **kwargs)
    return decorated_function


def generate_reset_token(email):
    """
    Generates a secure password reset token upon request
    """
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt='password-reset-salt')
