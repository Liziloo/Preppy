"""
Module contains routes related to personal info acquired from user, such as routine schedules, medical info, family makeup
"""

import os
import re

from dotenv import load_dotenv
from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError

from dbmodels import Calendar, Events, Families, Medical, Providers, States
from helpers import apology, login_required
from preppydb import db_session
from utils import load_states

userinfo_routes = Blueprint('userinfo_routes', __name__)


# Import Google API key
load_dotenv('global.env')
api_key = os.getenv('GOOGLE_API_KEY')


@userinfo_routes.route("/family", methods=["GET"])
@login_required
@load_states
def family():
    """
    Load user's family information from database
    """

    fam = {}

    # Check if the user has a family in db
    try:
        userfam = db_session.query(Families).filter_by(user_id=session['user_id']).first()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Database error accessing household information.")

    # If so, retrieve their family info
    if userfam:
        fam['name'] = userfam.last_name
        fam['adults'] = userfam.adults
        fam['seniors'] = userfam.seniors
        fam['children'] = userfam.children
        fam['pets'] = userfam.pets
        fam['special'] = userfam.special_needs
        try:
            fam['state'] = db_session.query(States.state).filter_by(id=userfam.state_id).scalar()
        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return apology("Database error accessing state info.")

    # if not, fill family dict with blank info
    else:
        fam['name'] = 'Unknown'
        fam['adults'] = fam['seniors'] = fam['children'] = fam['pets'] = 0
        fam['state'] = 'Unknown'
        fam['special'] = 'Unknown'

    return render_template("family.html", states=g.states, family=fam, nonce=g.nonce)


@userinfo_routes.route("/editfamily", methods=["POST"])
@login_required
@load_states
def editfamily():
    """
    Allow user to enter and/or edit family info
    """

    # Validate form data
    errors, validated_data = validate_form(request.form)

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('userinfo_routes.family'))

    # If the user already has family data in the db, update it with the new values
    try:
        row = db_session.query(Families.user_id).filter_by(user_id=session['user_id']).first()
        state_id = db_session.query(States.id).filter_by(state=validated_data["state"]).first().id
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        flash("Error updating household info.")
        return redirect(url_for('userinfo_routes.family'))

    if row:
        try:
            db_session.query(Families).filter_by(user_id=session['user_id']).update({
                'last_name': validated_data["name"],
                'adults': validated_data["adults"],
                'seniors': validated_data["seniors"],
                'children': validated_data["children"],
                'pets': validated_data["pets"],
                'state_id': state_id,
                'special_needs': validated_data["special"],
            })
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Database error updating household.")

    # if the user has no family in the db yet, insert information
    else:
        try:
            new_family = Families(user_id=session['user_id'], last_name=validated_data["name"], adults=validated_data["adults"], seniors=validated_data["seniors"],
                                  children=validated_data["children"], pets=validated_data["pets"], state_id=state_id, special_needs=validated_data["special"])
            db_session.add(new_family)
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Database error adding household information.")

    if errors:
        flash(" ".join(errors))

    # Set session last name
    session['last_name'] = validated_data["name"]

    return redirect(url_for('userinfo_routes.family'))


@userinfo_routes.route("/routines", methods=['GET'])
@login_required
def routines():
    """
    Send user's saved event data to routines page
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    try:
        results = db_session.query(Calendar.id, Calendar.name).filter_by(
            user_id=session['user_id']).all()
        events = db_session.query(Events).filter(Events.person_id.in_(
            db_session.query(Calendar.id).filter_by(user_id=session['user_id']))).all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Error retrieving schedule.")

    formatted_events = []
    for event in events:
        start = f"{event.start_day}T{event.start_time}"
        end = f"{event.end_day}T{event.end_time}"
        formatted_events.append({
            'title': event.title,
            'start': start,
            'end': end,
            'description': event.description,
            'person_id': event.person_id,
            'address': event.address,
            'eventId': event.id
        })
    return render_template('routines.html', last_name=last_name, results=results, events=formatted_events, nonce=g.nonce)


@userinfo_routes.route("/getfamily")
@login_required
def getfamily():
    """
    Sends family members saved in calendar table to fullCalendar
    """

    try:
        rows = db_session.query(Calendar.id, Calendar.name).filter_by(
            user_id=session['user_id']).all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Error retrieving household members.")

    return jsonify([{"id": row.id, "title": row.name} for row in rows])


@userinfo_routes.route("/add_family", methods=['POST'])
@login_required
def add_family():
    """
    Add family member to calendar options
    """

    if not request.form.get('name'):
        flash("Please enter a name.")
        return redirect(url_for('userinfo_routes.routines'))

    name = request.form.get('name')
    try:
        new_person = Calendar(user_id=session['user_id'], name=name)
        db_session.add(new_person)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error adding household member.")
    return redirect(url_for('userinfo_routes.routines'))


@userinfo_routes.route("/delete_family", methods=['POST'])
@login_required
def delete_family():
    """
    Handle user deletion of family member from calendar
    """

    if not request.form.get('name'):
        flash("Please enter a name.")
        return redirect(url_for('userinfo_routes.routines'))
    name = request.form.get('name')
    try:
        db_session.query(Calendar).filter_by(user_id=session['user_id'], name=name).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error deleting household member.")
    return redirect(url_for('userinfo_routes.routines'))


@userinfo_routes.route("/delete_event", methods=['POST'])
@login_required
def delete_event():
    """
    Handle user deletion of event from calendar
    """

    if not request.form.get('eventId'):
        flash("Invalid eventId")
        return redirect(url_for('userinfo_routes.routines'))
    event_id = request.form.get('eventId')
    try:
        db_session.query(Events).filter_by(id=event_id).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error deleting event.")

    return redirect(url_for('userinfo_routes.routines'))


@userinfo_routes.route("/add_event", methods=['POST'])
@login_required
def add_event():
    """
    Handle new additions and updates to events
    """

    errors = []

    required_fields = ['person_id', 'startTime', 'startDay', 'endTime', 'endDay', 'address']
    person_id = None

    if not request.form:
        flash("No form data.")
        return redirect(url_for('userinfo_routes.routines'))

    form_data = request.form
    for field in required_fields:
        if not form_data.get(field):
            errors.append(f"{field.replace('_', ' ').capitalize()} is required.")
    try:
        person_id = int(form_data.get('person_id'))
    except (ValueError, TypeError) as e:
        app.logger.error("ValueError: %s", e)
        errors.append("Invalid person ID.")

    title = form_data.get('title', '')
    start_time = form_data.get('startTime')
    start_day = form_data.get('startDay')
    end_time = form_data.get('endTime')
    end_day = form_data.get('endDay')
    address = form_data.get('address')

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('userinfo_routes.routines'))

    description = form_data.get("description", "")

    if not form_data.get('eventId'):
        try:
            new_event = Events(person_id=person_id, title=title, start_time=start_time, start_day=start_day,
                               end_time=end_time, end_day=end_day, address=address, description=description)
            db_session.add(new_event)
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error adding event.")
    else:
        event_id = form_data.get('eventId')
        try:
            db_session.query(Events).filter_by(id=event_id).update({
                'person_id': person_id,
                'title': title,
                'start_time': start_time,
                'start_day': start_day,
                'end_time': end_time,
                'end_day': end_day,
                'address': address,
                'description': description
            })
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error updating event.")
    if errors:
        flash(" ".join(errors))

    return redirect(url_for('userinfo_routes.routines'))


@userinfo_routes.route('/medical', methods=['GET'])
@login_required
def medical():
    """
    Retrieve user's saved medical info and send to front end template
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']
    try:
        results = db_session.query(Medical).filter_by(user_id=session['user_id'])
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Error retrieving medical information.")
    return render_template('medical.html', results=results, last_name=last_name, nonce=g.nonce)


@userinfo_routes.route('/add_medical', methods=['POST'])
@login_required
def add_medical():
    """
    Add new medical info submitted by user
    """

    fields = ['first_name', 'last_name', 'blood-type',
              'medications', 'allergies', 'other', 'insurance', 'policy']
    data = {field: request.form.get(field) or '' for field in fields}

    # Check for required fields
    required_fields = ['first_name', 'blood-type']
    for field in required_fields:
        if not data[field]:
            flash(f"Please provide a valid {field.replace('_', ' ')}.")
            return redirect(url_for('userinfo_routes.medical'))
    try:
        new_medical = Medical(user_id=session['user_id'], first_name=data['first_name'], last_name=data['last_name'], blood_type=data['blood-type'],
                              medications=data['medications'], allergies=data['allergies'], other=data['other'], insurance=data['insurance'], policy=data['policy'])
        db_session.add(new_medical)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error adding medical information.")
    return redirect(url_for('userinfo_routes.medical'))


@userinfo_routes.route('/delete_medical', methods=['POST'])
@login_required
def delete_medical():
    """
    Delete medical info as requested by user
    """
    if not request.form.get('person_id'):
        return apology("Invalid person ID.")
    person_id = request.form.get('person_id')

    try:
        db_session.query(Medical).filter_by(id=person_id).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error deleting medical information.")
    return redirect(url_for('userinfo_routes.medical'))


@userinfo_routes.route('/edit_medical', methods=['POST'])
@login_required
def edit_medical():
    """
    Edit medical info as requested by user
    """

    fields = ['person_id', 'first_name', 'last_name', 'blood-type',
              'medications', 'allergies', 'other', 'insurance', 'policy']

    data = {field: request.form.get(field) or '' for field in fields}
    required_fields = ['first_name', 'blood-type']
    for field in required_fields:
        if not data[field]:
            flash(f"Please provide a valid {field.replace('_', ' ')}")
            return redirect(url_for('userinfo_routes.medical'))
    try:
        db_session.query(Medical).filter_by(id=data['person_id']).update({
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'blood_type': data['blood-type'],
            'medications': data['medications'],
            'allergies': data['allergies'],
            'other': data['other'],
            'insurance': data['insurance'],
            'policy': data['policy']
        })
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error updating medical information.")
    return redirect(url_for('userinfo_routes.medical'))


@userinfo_routes.route('/providers', methods=['GET'])
@login_required
def providers():
    """
    Retrieve user's medical providers saved in database and send to template
    """

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']
    try:
        results = db_session.query(Providers).filter_by(user_id=session['user_id'])
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Error retrieving medical providers.")

    url = f'https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places'
    return render_template('med_providers.html', results=results, url=url, api_key=api_key, last_name=last_name, nonce=g.nonce)


@userinfo_routes.route('/add_provider', methods=['POST'])
@login_required
def add_provider():
    """
    Handle submission of new provider information entered by user
    """

    fields = ['first_name', 'last_name', 'patient', 'phone', 'address']
    data = {field: request.form.get(field) or '' for field in fields}
    required_fields = ['last_name', 'phone', 'address']
    for field in required_fields:
        if not data[field]:
            flash(f"Please provide a valid {field.replace('_', ' ')}.")
            return redirect(url_for('userinfo_routes.providers'))
    try:
        new_provider = Providers(user_id=session['user_id'], first_name=data['first_name'],
                                 last_name=data['last_name'], patient=data['patient'], phone=data['phone'], address=data['address'])
        db_session.add(new_provider)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error adding provider.")
    return redirect(url_for('userinfo_routes.providers'))


@userinfo_routes.route('/delete_provider', methods=['POST'])
@login_required
def delete_provider():
    """
    Delete provider info selected by user
    """

    if not request.form.get('person_id'):
        flash("Invalid person ID.")
        return redirect(url_for('userinfo_routes.providers'))
    person_id = request.form.get('person_id')
    try:
        db_session.query(Providers).filter_by(id=person_id).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error deleting provider.")
    return redirect(url_for('userinfo_routes.providers'))


@userinfo_routes.route('/edit_provider', methods=['POST'])
@login_required
def edit_provider():
    """
    Edit provider info as submitted by user
    """

    fields = ['person_id', 'first_name', 'last_name', 'patient', 'phone', 'address']
    data = {field: request.form.get(field) or '' for field in fields}
    required_fields = ['person_id', 'last_name', 'phone', 'address']
    for field in required_fields:
        if not data[field]:
            flash(f"Please provide a valid {field.replace('_', ' ')}.")
            return redirect(url_for('userinfo_routes.providers'))
    try:
        db_session.query(Providers).filter_by(id=data['person_id']).update({
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'patient': data['patient'],
            'phone': data['phone'],
            'address': data['address']
        })
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error updating provider information.")
    return redirect(url_for('userinfo_routes.providers'))


@userinfo_routes.route('/user_state', methods=["GET"])
@login_required
def user_state():
    """
    Provide user's state from db to fullCalendar
    """

    try:
        subquery = db_session.query(Families.state_id).filter_by(user_id=session['user_id'])
        state_record = db_session.query(States.full_name).filter(States.id.in_(subquery)).first()
        state = state_record.full_name if state_record else None
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return apology("Error retrieving user state.")
    return jsonify(state=state)


def validate_form(form_data):
    """
    Function to validate form data when user enters household info
    """
    errors = []
    validated_data = {}

    # Get information from form and return apology if any fields empty
    required_fields = ['name', 'adults', 'seniors', 'children', 'pets', 'state', 'special']

    if not request.form:
        errors.append("No form data.")
        return errors, validated_data

    form_data = request.form
    for field in required_fields:
        if not form_data.get(field):
            errors.append(f"{field.replace('_', ' ').capitalize()} is required.")

    try:
        validated_data["adults"] = int(form_data.get('adults'))
        validated_data["seniors"] = int(form_data.get('seniors'))
        validated_data["children"] = int(form_data.get('children'))
        validated_data["pets"] = int(form_data.get('pets'))
    except ValueError as e:
        app.logger.error("Value error: %s", e)
        errors.append("Please enter valid numbers for adults, seniors, children, and pets.")

    # Validate state against db
    state = form_data.get('state')
    if not re.match("^[A-Za-z]+$", state) or state not in g.states:
        app.logger.error("Invalid state.")
        errors.append("Not a valid state.")
    if not errors:
        validated_data["name"] = form_data.get('name')
        validated_data["special"] = form_data.get('special')
        validated_data["state"] = state

    return errors, validated_data
