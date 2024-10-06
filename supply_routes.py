"""
This module contains routes related to supply checklists for the gobag and shelter sections
"""

import uuid

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask import current_app as app
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from helpers import apology, login_required
from preppydb import db_session
from dbmodels import CustomInput, DisasterSupplies, Families, GoBags, SavedSupplies, Shelters, Sits, StateDisasters, Supplies

supply_routes = Blueprint('supply_routes', __name__)


@supply_routes.route("/buildgobag", methods=["GET", "POST"])
@login_required
def buildgobag():
    """
    Retrieves information from db about disasters and supplies and sends them to the front end
    """

    errors = []

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    # Get family info
    rows = retrieve_family('gobag', errors)
    if rows is None:
        return apology("Error loading household information.")

    sits = {}
    supplies = []
    for row in rows:
        if row[0] in sits:
            sits[row[0]]['items'].append(row[1])
        else:
            sits[row[0]] = {'items': [row[1]]}
        if row[1] not in supplies:
            supplies.append(row[1])

    # Mark true all disasters associated with user's home state
    try:
        state_id = db_session.query(Families.state_id).filter_by(
            user_id=session['user_id']).first().state_id
        sq = db_session.query(StateDisasters.disaster_id).filter_by(state_id=state_id)
        state_disasters = [disaster.sit for disaster in db_session.query(
            Sits.sit).filter(Sits.id.in_(sq)).all()]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error retrieving database information.")

    for sit, details in sits.items():
        if sit in state_disasters:
            details['checked'] = True
        else:
            details['checked'] = False

    if errors:
        return apology(" ".join(errors))

    return render_template("buildgobag.html", sits=sits, supplies=supplies, nonce=g.nonce)


@supply_routes.route("/postbuild", methods=["GET", "POST"])
@login_required
def postbuild():
    """
    Processes tasks toggled by user in gobag form and saves to db
    """

    errors = []

    # Clear old data
    try:
        db_session.query(SavedSupplies).filter_by(
            user_id=session['user_id'], gobag='Yes').update({'gobag': 'No'})
        db_session.query(GoBags).filter_by(user_id=session['user_id']).delete()
        db_session.query(CustomInput).filter_by(user_id=session['user_id'], type='gobag').delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error clearing old data.")

    # Get form data
    if not request.form.getlist('supply'):
        flash("Please choose some supplies")
        return redirect(url_for('supply_routes.buildgobag'))
    supplies = request.form.getlist('supply')

    # Save supplies user has selected to database
    for supply in supplies:
        try:
            supply_uuid = db_session.query(Supplies).filter_by(item=supply).first().uuid
            new_gobag = GoBags(user_id=session['user_id'], supply_uuid=supply_uuid)
            db_session.add(new_gobag)
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error saving supplies.")

    if errors:
        return apology(" ".join(errors))

    return redirect(url_for('supply_routes.gobag'))


@supply_routes.route("/gobag", methods=["GET"])
@login_required
def gobag():
    """
    Retrieves database information about user's gobag supplies and sends them to front end
    """

    errors = []

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    # Get supplies that user has saved as needing
    try:
        sq1 = db_session.query(Supplies.item.label('supply_name'),
                               Supplies.uuid.label('supply_uuid')).filter(Supplies.uuid.in_(db_session.query(GoBags.supply_uuid).filter_by(user_id=session['user_id'])))
        sq2 = db_session.query(CustomInput.name.label('supply_name'),
                               CustomInput.uuid.label('supply_uuid')).filter_by(
                                   user_id=session['user_id'], type='gobag'
        )
        query = sq1.union(sq2).order_by('supply_name')
        rows = query.all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error loading requested supplies.")
    if not rows:
        flash("Please choose what you'd like to include in your go-bag before proceeding.")
        return redirect(url_for('supply_routes.buildgobag'))

    supplies = [{'supply_name': row.supply_name,
                 'supply_uuid': row.supply_uuid} for row in rows]

    # Get supplies user has already acquired
    try:
        done_supplies = [supply.supply_uuid for supply in db_session.query(
            SavedSupplies.supply_uuid).filter_by(user_id=session['user_id'], gobag='Yes').all()]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error loading saved supplies.")

    # Add boolean that indicates whether an item has been acquired
    supplies_checked = {supply['supply_uuid']: {
        'supply_name': supply['supply_name'], 'done': supply['supply_uuid'] in done_supplies} for supply in supplies}

    if errors:
        return apology(" ".join(errors))

    return render_template("gobag.html", supplies_checked=supplies_checked, last_name=last_name, nonce=g.nonce)


@supply_routes.route("/postgobag", methods=["POST"])
@login_required
def postgobag():
    """
    Retrieves database information about user's gobag supplies and sends them to front end
    """

    errors = []

    # Get supplies that the user wants to save as acquired
    new_supplies = request.form.getlist('supply')
    saved_supplies = []

    # Get supplies that user has already saved as acquired
    try:
        saved_supplies = [supply.supply_uuid for supply in db_session.query(
            SavedSupplies.supply_uuid).filter_by(user_id=session['user_id'], gobag='Yes')]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error accessing saved supplies.")

    if not errors:
        # Insert new supplies into saved_supplies
        for supply in new_supplies:
            if supply not in saved_supplies:
                try:
                    existing_supplies = [row.supply_uuid for row in db_session.query(
                        SavedSupplies).filter_by(user_id=session['user_id'])]
                except SQLAlchemyError as e:
                    app.logger.error("Database error: %s", e)
                    errors.append("Error accessing supplies in database.")
                    break

                if supply not in existing_supplies:
                    try:
                        new_supply = SavedSupplies(
                            user_id=session['user_id'], supply_uuid=supply, gobag='Yes')
                        db_session.add(new_supply)
                        db_session.commit()
                    except SQLAlchemyError as e:
                        db_session.rollback()
                        app.logger.error("Database error: %s", e)
                        errors.append("Error adding new supplies.")
                else:
                    update_supplies('gobag', 'Yes', session['user_id'], supply, errors)

        # Delete previously saved supplies not in new list
        for supply in saved_supplies:
            if supply not in new_supplies:
                update_supplies('gobag', 'No', session['user_id'], supply, errors)

    else:
        flash(" ".join(errors))

    return redirect(url_for('supply_routes.gobag'))


@supply_routes.route("/customsupply", methods=["POST"])
@login_required
def customsupply():
    """
    Insert new supplies created by user into db
    """

    errors = []

    if not request.form.get('custom_supply'):
        errors.append("Please enter the name of a custom supply.")

    custom_supply = request.form.get('custom_supply').replace(" ", "_")
    supply_uuid = str(uuid.uuid4())
    try:
        new_custominput = CustomInput(
            user_id=session['user_id'], type='gobag', name=custom_supply, uuid=supply_uuid)
        db_session.add(new_custominput)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error adding custom supply.")

    if errors:
        flash(" ".join(errors))

    return redirect(url_for('supply_routes.gobag'))


@supply_routes.route("/delete_supply", methods=['POST'])
@login_required
def delete_supply():
    """
    Allow user to delete supplies from checklist
    """

    errors = []

    data = request.get_json()

    if not data.get('supply_uuid'):
        errors.append("Please choose a supply to delete.")
    supply_uuid = data.get('supply_uuid')

    if not data.get('source'):
        errors.append("No source page detected.")
    source = data.get('source')

    if errors:
        return apology(" ".join(errors))

    try:
        db_session.query(CustomInput).filter_by(
            user_id=session['user_id'], uuid=supply_uuid).delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error deleting custom supply.")

    if source == 'gobag.html':
        try:
            # Update selected supply in table with user's acquired supplies
            db_session.query(SavedSupplies).filter_by(
                user_id=session['user_id'], supply_uuid=supply_uuid).update({'gobag': 'No'})

            # Remove selected supply from user's desired gobag supplies
            db_session.query(GoBags).filter_by(
                user_id=session['user_id'], supply_uuid=supply_uuid).delete()
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error deleting supplies.")

    if source == 'stockshelter.html':
        try:
            # Update selected supply in table with user's acquired supplies
            db_session.query(SavedSupplies).filter_by(
                user_id=session['user_id'], supply_uuid=supply_uuid).update({'shelter': 'No'})

            # Remove selected supply from user's desired gobag supplies
            db_session.query(Shelters).filter_by(
                user_id=session['user_id'], supply_uuid=supply_uuid).delete()
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error deleting supplies.")

    if errors:
        return apology(" ".join(errors))

    return jsonify(success=True)


@supply_routes.route("/shelter", methods=["GET"])
@login_required
def shelter():
    """
    Retrieve db data about disasters and associated supplies, render to shelter template
    """

    errors = []

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    # Get family info
    rows = retrieve_family('shelter', errors)
    if rows is None:
        return apology(" ".join(errors))

    sits = {}
    supplies = []
    for row in rows:
        if row[0] in sits:
            sits[row[0]]['items'].append(row[1])
        else:
            sits[row[0]] = {'items': [row[1]]}

        if row[1] not in supplies:
            supplies.append(row[1])

    # Mark true all disasters associated with user's home state
    try:
        state_id = db_session.query(Families.state_id).filter_by(user_id=session['user_id']).first()
        if state_id:
            state_id = state_id.state_id
        else:
            return apology("No home state for user")

        disaster_ids = [d.disaster_id for d in db_session.query(
            StateDisasters.disaster_id).filter_by(state_id=state_id).all()]
        state_disasters = [row.sit for row in db_session.query(
            Sits.sit).filter(Sits.id.in_(disaster_ids)).all()]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error accessing state disaster data.")

    for sit, details in sits.items():
        details['checked'] = sit in state_disasters

    if errors:
        return apology(" ".join(errors))

    return render_template("shelter.html", sits=sits, supplies=supplies, nonce=g.nonce)


@supply_routes.route("/postshelter", methods=["POST"])
@login_required
def postshelter():
    """
    Record user's preferences for shelter supplies, deleting old data as necessary
    """

    errors = []

    # Clear old data
    try:
        db_session.query(SavedSupplies).filter_by(
            user_id=session['user_id'], shelter='Yes').update({'shelter': 'No'})
        db_session.query(Shelters).filter_by(user_id=session['user_id']).delete()
        db_session.query(CustomInput).filter_by(user_id=session['user_id'], type='shelter').delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error updating supplies.")

    # Get form data
    if not request.form.getlist('supply'):
        errors.append("Please toggle some supplies to include.")
    supplies = request.form.getlist('supply')

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('supply_routes.shelter'))

    # Save supplies user has selected to database
    for supply in supplies:
        try:
            result = db_session.query(Supplies).filter_by(item=supply).first()
            if result:
                supply_uuid = result.uuid
                new_supply = Shelters(user_id=session['user_id'], supply_uuid=supply_uuid)
                db_session.add(new_supply)
                db_session.commit()
            else:
                errors.append("Supply not found: " + supply)
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error saving supplies to custom shelter list.")

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('supply_routes.shelter'))

    return redirect(url_for('supply_routes.stockshelter'))


@supply_routes.route("/stockshelter", methods=["GET"])
@login_required
def stockshelter():
    """
    Retrieve user's saved progress on shelter supply list from db and render template
    """

    errors = []

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    # Get supplies that user has saved as needing
    try:
        sq1 = db_session.query(Supplies.item.label('supply_name'),
                               Supplies.uuid.label('supply_uuid')).filter(Supplies.uuid.in_(db_session.query(Shelters.supply_uuid).filter_by(user_id=session['user_id'])))
        sq2 = db_session.query(CustomInput.name.label('supply_name'),
                               CustomInput.uuid.label('supply_uuid')).filter_by(user_id=session['user_id'], type='shelter')
        query = sq1.union(sq2).order_by('supply_name')
        rows = query.all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error retrieving requested supplies.")

    if not rows:
        flash("Please design your shelter supply list before proceeding.")
        return redirect(url_for('supply_routes.shelter'))

    supplies = [{'supply_name': row[0],
                 'supply_uuid': row[1]} for row in rows]

    # Get supplies user has already acquired
    try:
        done_supplies = [row.supply_uuid for row in db_session.query(
            SavedSupplies.supply_uuid).filter_by(user_id=session['user_id'], shelter='Yes')]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error retrieving acquired supplies.")

    # Add boolean that indicates whether an item has been acquired
    supplies_checked = {supply['supply_uuid']: {
        'supply_name': supply['supply_name'], 'done': supply['supply_uuid'] in done_supplies} for supply in supplies}

    if errors:
        return apology(" ".join(errors))

    return render_template("stockshelter.html", supplies_checked=supplies_checked, last_name=last_name, nonce=g.nonce)


@supply_routes.route("/poststock", methods=["POST"])
@login_required
def poststock():
    """
    Save updated list of user's shelter supplies progress to db
    """

    errors = []

    # Get supplies that the user wants to save
    new_supplies = request.form.getlist('supply')
    saved_supplies = []

    # Get supplies user has already acquired
    try:
        saved_supplies = [row.supply_uuid for row in db_session.query(
            SavedSupplies.supply_uuid).filter_by(user_id=session['user_id'], shelter='Yes')]
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error loading acquired supplies.")

    if not errors:
        # Insert new supplies into saved_supplies
        for supply in new_supplies:
            if supply not in saved_supplies:
                try:
                    existing_supplies = [row.supply_uuid for row in db_session.query(
                        SavedSupplies.supply_uuid).filter_by(user_id=session['user_id'])]
                except SQLAlchemyError as e:
                    app.logger.error("Database error: %s", e)
                    errors.append("Error retrieving existing supplies.")
                    break

                if supply not in existing_supplies:
                    try:
                        new_supply = SavedSupplies(
                            user_id=session['user_id'], supply_uuid=supply, shelter='Yes')
                        db_session.add(new_supply)
                        db_session.commit()
                    except SQLAlchemyError as e:
                        app.logger.error("Database error: %s", e)
                        errors.append("Error saving new supplies.")
                        break

                else:
                    update_supplies('shelter', 'Yes', session['user_id'], supply, errors)

    if not errors:
        # Update any supplies that aren't in the new list
        for supply in saved_supplies:
            if supply not in new_supplies:
                update_supplies('shelter', 'No', session['user_id'], supply, errors)

    if errors:
        flash(" ".join(errors))

    return redirect(url_for('supply_routes.stockshelter'))


@supply_routes.route("/customstock", methods=["POST"])
@login_required
def customstock():
    """
    Process custom supply input from user
    """

    errors = []

    # Insert new supplies created by user into db
    if not request.form.get('custom_supply'):
        errors.append("Please enter a name for your supply.")

    custom_supply = request.form.get('custom_supply').replace(" ", "_")
    supply_uuid = str(uuid.uuid4())

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('supply_routes.stockshelter'))

    try:
        new_supply = CustomInput(user_id=session['user_id'],
                                 type='shelter', name=custom_supply, uuid=supply_uuid)
        db_session.add(new_supply)
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error adding custom supply.")

    if errors:
        flash(" ".join(errors))

    return redirect(url_for('supply_routes.stockshelter'))


def retrieve_family(filter_type, errors):
    """
    Gather db info on user's family and use it to fill in suggested supplies
    """

    try:
        family = db_session.query(Families).filter_by(user_id=session['user_id']).first()

        has_adults = family.adults > 0
        has_seniors = family.seniors > 0
        has_children = family.children > 0
        has_pets = family.pets > 0

        query = (
            db_session.query(Sits.sit, Supplies.item, DisasterSupplies.item_id,
                             DisasterSupplies.disaster_id)
            .join(DisasterSupplies, Sits.id == DisasterSupplies.disaster_id)
            .join(Supplies, DisasterSupplies.item_id == Supplies.id)

            .filter(getattr(Supplies, filter_type) == 'y')
            .filter(
                (Supplies.adult == 'y' and has_adults) |
                (Supplies.senior == 'y' and has_seniors) |
                (Supplies.child == 'y' and has_children) |
                (Supplies.pet == 'y' and has_pets)
            ).order_by(Sits.probability)
        )
        rows = query.all()

    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error retrieving household information.")
        return errors
    return rows


def update_supplies(kit, insupplies, user_id, supply, errors):
    """
    Update table recording user's progress on supply list
    """

    try:
        stmt = update(SavedSupplies).where(
            (SavedSupplies.user_id == user_id) &
            (SavedSupplies.supply_uuid == supply)
        ).values({kit: insupplies})
        db_session.execute(stmt)
        db_session.commit()

    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error updating supplies.")
    return errors
