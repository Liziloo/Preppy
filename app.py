"""
This module sets up the main application and routing, as well
as configures the mailserver and error logging.
"""

import base64
from email.message import EmailMessage
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import smtplib
import sys

from dotenv import load_dotenv
from flask import Flask, g, render_template, request
from flask_mail import Mail
from flask_wtf import CSRFProtect

from auth_routes import auth_routes
from data_routes import data_routes
from dbmodels import Base
from flask_session import Session
from helpers import apology, login_required
from preppydb import db_session
from supply_routes import supply_routes
from task_routes import task_routes
from userinfo_routes import userinfo_routes

load_dotenv()
csrf = CSRFProtect()

# Configure application
app = Flask(__name__)

# Initialize db models
Base.metadata.create_all(bind=db_session.bind)

# Secret key for flash
if os.environ.get('FLASK_ENV') == 'production':
    app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
else:
    app.secret_key = 'development-secret-key'


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Enable CSRFProtection
csrf.init_app(app)


# Register route blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(data_routes)
app.register_blueprint(supply_routes)
app.register_blueprint(task_routes)
app.register_blueprint(userinfo_routes)

if __name__ == "__main__":
    app.run()

# Configure mail server and upload directory for user files
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
mail = Mail(app)


# Set SameSite cookie attribute to strict
app.config.update(
    SESSION_COOKIE_SAMESITE='Strict'
)


@app.before_request
def generate_nonce():
    """
    Function to generate nonce for use in csp headers
    """
    g.nonce = base64.b64encode(os.urandom(16)).decode('utf-8')


@app.context_processor
def inject_nonce():
    """
    Function to inject nonce into all routes for use in csp headers
    """
    return {"nonce": g.nonce}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    # Set CSP headers
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        f"script-src 'nonce-{g.nonce}' 'strict-dynamic'; "
        "img-src 'self' data: https://maps.gstatic.com https://maps.googleapis.com/ https://api.memegen.link/;"
        f"style-src 'self' 'nonce-{g.nonce}' data: https://*.googleapis.com https://maps.gstatic.com https://maps.googleapis.com https://fonts.googleapis.com https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com;"
        "font-src 'self' data: https://fonts.gstatic.com/;"
        "connect-src 'self' https://maps.googleapis.com/ https://maps.gstatic.com;"
        "frame-ancestors 'none'; "
        "form-action 'self' https://validator.w3.org/check;"
    )
    response.headers['X-Frame-Options'] = 'DENY'
    request_origin = request.headers.get('Origin')
    allowed_origins = ['self' "https://maps.googleapis.com", "https://stackpath.bootstrapcdn.com", "https://fullcalendar.io"]
    if request_origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = request_origin
    else:
        response.headers['Access-Control-Allow-Origin'] = 'null'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


# Error handling

class CustomSMTPHandler(SMTPHandler):
    """
    Set up custom handler so can handle SSL or TLS depending on user-set environmental variables
    """

    def emit(self, record):
        try:
            if app.config['MAIL_USE_SSL']:
                smtp = smtplib.SMTP_SSL(self.mailhost, self.mailport, timeout=self.timeout)
            else:
                smtp = smtplib.SMTP(self.mailhost, self.mailport, timeout=self.timeout)
                if app.config['MAIL_USE_TLS']:
                    smtp.starttls()
            smtp.login(self.username, self.password)

            # Format log record
            msg = self.format(record)

            # Create the email message
            email = EmailMessage()
            email.set_content(msg)
            email['Subject'] = self.getSubject(record)
            email['From'] = self.fromaddr
            email['To'] = ', '.join(self.toaddrs)

            # Send email
            smtp.send_message(email)
            smtp.quit()
        except (smtplib.SMTPException, KeyError, smtplib.SMTPAuthenticationError) as e:
            app.logger.error("Failed to set up CustomSMTPHandler: %s", e)
            self.handleError(record)


if not app.debug:
    # Log info level events to a file
    file_handler = RotatingFileHandler(
        'logs/error.log', maxBytes=10240, backupCount=10
    )

    file_handler.setLevel(logging.INFO)

    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)

    # Email error-level events
    if app.config['MAIL_SERVER']:
        try:
            mail_handler = CustomSMTPHandler(
                mailhost=(
                    app.config['MAIL_SERVER'],
                    app.config['MAIL_PORT']),

                fromaddr=app.config['MAIL_USERNAME'],
                toaddrs=[os.getenv('MAIL_RECIPIENT')],

                subject='Preppy Error',
                credentials=(app.config['MAIL_USERNAME'],
                             app.config['MAIL_PASSWORD']),
                secure=() if app.config['MAIL_USE_TLS'] else None,
                timeout=30
            )

            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        except (smtplib.SMTPException, KeyError) as e:
            app.logger.error("Failed to set up mail handler: %s", e)

    # Console handler for docker
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(console_handler)


@app.errorhandler(500)
def internal_error(error):
    return apology("We're so sorry, you've encountered an internal server error.", 500)


@app.route("/", methods=["GET"])
@login_required
def index():
    """
    Routing to the index page.
    """
    return render_template("index.html")
