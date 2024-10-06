"""
Module handles routes related to contacts, secure files, and meetup locations saved by user
"""

import os
import uuid

from io import BytesIO

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from flask import Blueprint, flash, g, redirect, render_template, request, session, jsonify, send_file, url_for
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError

from dbmodels import Contacts, Coordinates, SecFileMetadata
from helpers import apology, login_required
from preppydb import db_session

data_routes = Blueprint('data_routes', __name__)

load_dotenv('global.env')

# Configure encryption key
KEYFILE = 'keyfile'

if not os.path.exists(KEYFILE):
    key = Fernet.generate_key()
    with open(KEYFILE, 'wb') as f:
        f.write(key)
else:
    with open(KEYFILE, 'rb') as f:
        key = f.read()
cipher_suite = Fernet(key)

# Import Google API key
api_key = os.getenv('GOOGLE_API_KEY')


@data_routes.route('/contacts', methods=['GET'])
@login_required
def contacts():
    """
    Retrieves db information about user's stored emergency contacts and sends to front end
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    try:
        results = db_session.query(Contacts).filter_by(user_id=session['user_id']).all()
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        return apology("Error retrieving contacts.")

    url = f'https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places'
    return render_template('contacts.html', last_name=last_name, results=results, url=url, api_key=api_key, nonce=g.nonce)


@data_routes.route('/new_contact', methods=['POST'])
@login_required
def new_contact():
    """
    Handles form submission of new contact information
    """

    fields = ['first_name', 'last_name', 'phone', 'email', 'address']

    data = {field: request.form.get(field) or '' for field in fields}
    try:
        new_person = Contacts(
            user_id=session['user_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            email=data['email'],
            address=data['address']
        )
        db_session.add(new_person)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {e}")
        flash("Error adding contact.")
    return redirect(url_for('data_routes.contacts'))


@data_routes.route('/delete_contact', methods=['POST'])
@login_required
def delete_contact():
    """
    Handles deletion of user's emergency contacts
    """

    if not request.form.get('person_id'):
        flash("No such person in database")
        return redirect(url_for('data_routes.contacts'))
    person_id = request.form.get('person_id')

    try:
        db_session.query(Contacts).filter_by(id=person_id).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {e}")
        flash("Error deleting contact.")

    return redirect(url_for('data_routes.contacts'))


@data_routes.route('/edit_contact', methods=['POST'])
@login_required
def edit_contact():
    """
    Handles updating emergency contact information changed by user
    """

    fields = ['person_id', 'first_name', 'last_name', 'phone', 'email', 'address']
    data = {field: request.form.get(field) or '' for field in fields}

    try:
        db_session.query(Contacts).filter_by(id=data['person_id']).update({
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data['phone'],
            'email': data['email'],
            'address': data['address']
        })
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {e}")
        flash("Error updating contact.")

    return redirect(url_for('data_routes.contacts'))


@data_routes.route('/evacuation', methods=["GET"])
@login_required
def evacuation():
    """
    Retrieves coordinates of user's saved meetup locations and sends to front end for display in javascript map
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))
    last_name = session['last_name']
    try:
        pins = db_session.query(Coordinates.latitude, Coordinates.longitude,
                                Coordinates.title).filter_by(user_id=session['user_id']).all()
        pins = [pin._asdict() for pin in pins]
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        return apology("Error loading saved pin data.")
    return render_template('evacuation.html', api_key=api_key, pins=pins, last_name=last_name, nonce=g.nonce)


@data_routes.route('/save_coords', methods=["POST"])
@login_required
def save_coords():
    """
    Updates coordinates for locations saved by user in db
    """

    errors = []

    pins = request.json
    try:
        dbpins = db_session.query(Coordinates.latitude, Coordinates.longitude,
                                  Coordinates.title).filter_by(user_id=session['user_id']).all()
        pin_tuples = {(pin[0], pin[1]) for pin in pins}
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        flash("Error saving coordinates.")
        return redirect(url_for('data_routes.evacuation'))

    # Delete any pins that don't exist in most recent coordinates sent by user
    for row in dbpins:
        database_tuple = (row.latitude, row.longitude)
        if database_tuple not in pin_tuples:
            try:
                db_session.query(Coordinates).filter_by(
                    user_id=session['user_id'], latitude=row.latitude, longitude=row.longitude).delete()
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                app.logger.error(f"Database error: {e}")
                errors.append("Error deleting pins.")
                break

    # Extract latitude and longitude
    for pin in pins:
        latitude = pin[0]
        longitude = pin[1]
        title = pin[2] if len(pin) == 3 else ""

        # Check for each pin's coordinates in database
        try:
            result = db_session.query(Coordinates).filter_by(
                user_id=session['user_id'], latitude=latitude, longitude=longitude).first()
        except SQLAlchemyError as e:
            app.logger.error(f"Database error: {e}")
            errors.append("Error retrieving coordinates from database.")
            break

        # If not present, insert new row
        if not result:
            try:
                new_coord = Coordinates(
                    user_id=session['user_id'],
                    latitude=latitude,
                    longitude=longitude,
                    title=title
                )
                db_session.add(new_coord)
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                app.logger.error(f"Database error: {e}")
                errors.append("Error adding coordinates.")
                break

        # If the pin's title has changed, update
        if result:
            if result.title != title:
                try:
                    db_session.query(Coordinates).filter_by(
                        user_id=session['user_id'], latitude=latitude, longitude=longitude).update({'title': title})
                    db_session.commit()
                except SQLAlchemyError as e:
                    db_session.rollback()
                    app.logger.error(f"Database error: {e}")
                    errors.append("Error updating title.")

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('data_routes.evacuation'))
    return jsonify({"success": True})


@data_routes.route('/uploads', methods=["GET"])
@login_required
def uploads():
    """
    Retrieves information about user's stored encrypted files and sends to template
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    try:
        results = db_session.query(SecFileMetadata.filename).filter_by(user_id=session['user_id'])
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        return apology("Error accessing uploads information.")
    return render_template('uploads.html', results=results, last_name=last_name, nonce=g.nonce)


@data_routes.route('/new_upload', methods=["POST"])
@login_required
def new_upload():
    """
    Reads, encrypts and stores newly uploaded files from user
    """

    errors = []

    if 'file' not in request.files:
        errors.append('No file part.')
    file = request.files['file']
    if file.filename == '':
        errors.append('No selected file.')
    if errors:
        flash(" ".join(errors))
        return redirect(url_for('data_routes.uploads'))

    if file:
        file_name = file.filename
        file_data = file.read()
        encrypted_data = cipher_suite.encrypt(file_data)
        secure_filename = str(uuid.uuid4()) + ".enc"
        try:
            row = db_session.query(SecFileMetadata.secure_filename).filter_by(
                user_id=session['user_id'], filename=file_name).first()
        except SQLAlchemyError as e:
            app.logger.error(f"Database error: {e}")
            errors.append("Error accessing file data.")

        if row:
            old_secfilename = row.secure_filename
            try:
                db_session.query(SecFileMetadata).filter_by(
                    user_id=session['user_id'], filename=file_name).update({'secure_filename': secure_filename})
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_secfilename))
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                app.logger.error(f"Database error: {e}")
                errors.append("Error updating file data.")
        else:
            try:
                new_file = SecFileMetadata(
                    user_id=session['user_id'], filename=file_name, secure_filename=secure_filename)
                db_session.add(new_file)
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                errors.append("Database error: " + str(e))

        if errors:
            flash(" ".join(errors))
            return redirect(url_for('data_routes.uploads'))

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
        with open(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename), 'wb') as file:
            file.write(encrypted_data)
            return redirect(url_for('data_routes.uploads'))

    errors.append("No such file")
    flash(" ".join(errors))
    return redirect(url_for('data_routes.uploads'))


@data_routes.route('/download', methods=["POST"])
@login_required
def download():
    """
    Decrypts encrypted file on server and sends unencrypted file to user
    """

    if not request.form.get('filename'):
        flash("Please enter a valid filename")
        return redirect(url_for('data_routes.uploads'))
    file_name = request.form.get('filename')

    try:
        row = db_session.query(SecFileMetadata.secure_filename).filter_by(
            user_id=session['user_id'], filename=file_name).first()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        flash("Error accessing file.")

    if row:
        secure_filename = row.secure_filename
        try:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename), 'rb') as file:
                encrypted_data = file.read()
                try:
                    decrypted_data = cipher_suite.decrypt(encrypted_data)
                except InvalidToken as e:
                    app.logger.error(f"Decryption error: {e}")
                    flash("Decryption error.")
                    return redirect(url_for('data_routes.uploads'))
        except (FileNotFoundError, PermissionError) as e:
            app.logger.error(f"File error: {e}")
            flash("File error.")
            return redirect(url_for('data_routes.uploads'))

        stream = BytesIO(decrypted_data)
        stream.seek(0)

        try:
            return send_file(stream, mimetype=None, as_attachment=True, download_name=file_name, conditional=False)
        except (FileNotFoundError, PermissionError) as e:
            app.logger.error(f"File error: {e}")
            flash("Error sending file.")
            return redirect(url_for('data_routes.uploads'))
    else:
        flash("File not found.")
        return redirect(url_for('data_routes.uploads'))


@data_routes.route('/delete_file', methods=["POST"])
@login_required
def delete_file():
    """
    Handles user deletion of encrypted stored file
    """

    if not request.form.get('filename'):
        return apology("Please enter a valid filename")
    file_name = request.form.get('filename')

    try:
        row = db_session.query(SecFileMetadata.secure_filename).filter_by(
            user_id=session['user_id'], filename=file_name).first()
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        flash("Error finding file.")
        return redirect(url_for('data_routes.uploads'))

    if row:
        secure_filename = row.secure_filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        try:
            db_session.query(SecFileMetadata).filter_by(
                user_id=session['user_id'], filename=file_name).delete()
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error(f"Database error: {e}")
            flash("Error deleting file.")
        return redirect(url_for('data_routes.uploads'))

    flash("File not found.")
    return redirect(url_for('data_routes.uploads'))
