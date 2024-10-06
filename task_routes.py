"""
This module contains routes pertaining to the functionality of the task list and customization of it by the user
"""

import uuid

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError

from dbmodels import CustomInput, DisasterTasks, Families, SavedTasks, CustomTasks, Sits, StateDisasters, Tasks
from helpers import apology, login_required
from preppydb import db_session

task_routes = Blueprint('task_routes', __name__)


@task_routes.route('/tasks', methods=['GET'])
@login_required
def tasks():
    """
    Loads suggested task-list items according to user info
    """

    errors = []

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    # Make dic from all disasters from database as well as their associated tasks
    try:
        rows = db_session.query(Sits.sit, Tasks.task).join(DisasterTasks, Sits.id == DisasterTasks.disaster_id).join(
            Tasks, DisasterTasks.task_uuid == Tasks.uuid).order_by(Sits.probability).all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error accessing disaster database.")

    sits = {}
    sittasks = []
    for row in rows:
        if row.sit in sits:
            sits[row.sit]['tasks'].append(row.task)
        else:
            sits[row.sit] = {'tasks': [row.task]}
        if row.task not in sittasks:
            sittasks.append(row.task)

    # Mark true all disasters associated with user's home state
    try:
        result = db_session.query(Families.state_id).filter_by(user_id=session['user_id']).first()

    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error accessing state information.")

    if result:
        state_id = result.state_id
        try:
            state_disasters = [row.sit for row in db_session.query(Sits.sit).filter(Sits.id.in_(
                db_session.query(StateDisasters.disaster_id).filter_by(state_id=state_id))).all()]
        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            errors.append("Error accessing state information.")

        for sit, details in sits.items():
            details['checked'] = sit in state_disasters
    else:
        errors.append("Household state not defined.")

    if errors:
        return apology(" ".join(errors))
    return render_template('tasks.html', sits=sits, tasks=sittasks, last_name=last_name, nonce=g.nonce)


@task_routes.route('/posttasks', methods=['POST'])
@login_required
def posttasks():
    """
    Save tasks chosen by user to db and redirect to checklist
    """

    errors = []

    # Clear old data
    try:
        db_session.query(SavedTasks).filter_by(user_id=session['user_id']).delete()
        db_session.query(CustomTasks).filter_by(user_id=session['user_id']).delete()
        db_session.query(CustomInput).filter_by(user_id=session['user_id'], type='task').delete()
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        errors.append("Error clearing old data.")

    # Get form data from tasks.html
    chosentasks = request.form.getlist('task')
    if not chosentasks:
        errors.append("No tasks selected.")

    # Save tasks user has selected to database
    for task in chosentasks:
        try:
            result = db_session.query(Tasks.uuid).filter_by(task=task).first()
            if result:
                task_uuid = result.uuid
                new_task = CustomTasks(user_id=session['user_id'], task_uuid=task_uuid)
                db_session.add(new_task)
                db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            errors.append("Error saving tasks to database.")

    if errors:
        flash(" ".join(errors))
        return redirect(url_for('task_routes.tasks'))

    return redirect(url_for('task_routes.customtasks'))


@task_routes.route('/customtasks', methods=['GET'])
@login_required
def customtasks():
    """
    Route to display task checklist to user and allow them to save progress and add/delete tasks.
    """
    errors = []
    has_error = False

    if 'last_name' not in session:
        flash("Please provide your family info first. This will help us to help you prepare.")
        return redirect(url_for('userinfo_routes.family'))

    last_name = session['last_name']

    try:
        # Get tasks that user has saved as done
        done_tasks = [row.task_uuid for row in db_session.query(
            SavedTasks.task_uuid).filter_by(user_id=session['user_id']).all()]

        # Get all tasks that user has decided they need to do
        sq1 = db_session.query(Tasks.task.label('task_name'), Tasks.uuid.label('task_uuid')).filter(
            Tasks.uuid.in_(db_session.query(CustomTasks.task_uuid).filter_by(user_id=session['user_id'])))
        sq2 = db_session.query(CustomInput.name.label('task_name'), CustomInput.uuid.label(
            'task_uuid')).filter_by(user_id=session['user_id'], type='task')
        query = sq1.union(sq2).order_by('task_name')
        custom_rows = query.all()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error retrieving tasks from database.")
        has_error = True

    if not custom_rows:
        flash("Please choose what tasks you'd like to include before proceeding.")
        return redirect(url_for('task_routes.tasks'))
    dbtasks = [{'task_name': row.task_name, 'task_uuid': row.task_uuid}
               for row in custom_rows]

    # Add boolean that indicates whether a task should be checked as done in the html checklist
    tasks_checked = {task['task_uuid']: {'task_name': task['task_name'],
                                         'done': task['task_uuid'] in done_tasks} for task in dbtasks}

    if has_error:
        return apology(" ".join(errors))

    return render_template("customtasks.html", tasks_checked=tasks_checked, last_name=last_name, nonce=g.nonce)


@task_routes.route('/tasksave', methods=['POST'])
@login_required
def tasksave():
    """
    Route to save user progress on tasks checklist
    """

    errors = []
    has_error = False

    # Get tasks that the user wants to save as done
    new_tasks = request.form.getlist('task')
    saved_tasks = []

    # Get tasks the user has already saved as done
    try:
        rows = db_session.query(SavedTasks.task_uuid).filter_by(user_id=session['user_id'])
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        errors.append("Error loading saved tasks.")
        has_error = True
    if rows:
        saved_tasks = [row.task_uuid for row in rows]

    # Uncheck in db any tasks that aren't in the new list
    uncheck_task(saved_tasks, new_tasks, errors)

    # Insert new tasks into saved_tasks
    for task in new_tasks:
        if task not in saved_tasks:
            try:
                new_task = SavedTasks(user_id=session['user_id'], task_uuid=task)
                db_session.add(new_task)
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                app.logger.error("Database error: %s", e)
                errors.append("Error saving tasks.")
                has_error = True
    if has_error:
        flash(" ".join(errors))
    return redirect(url_for('task_routes.customtasks'))


@task_routes.route('/customadd', methods=['POST'])
@login_required
def customadd():
    """
    Allow user to add custom tasks to db
    """
    # Insert new tasks created by user into db
    if not request.form.get('custom_task'):
        flash("Please enter a name for your task.")

    custom_task = request.form.get('custom_task').replace(" ", "_")
    task_uuid = str(uuid.uuid4())
    try:
        new_input = CustomInput(user_id=session['user_id'],
                                type='task', name=custom_task, uuid=task_uuid)
        db_session.add(new_input)
        db_session.commit()
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        flash("Error saving custom task.")
    return redirect(url_for('task_routes.customtasks'))


@task_routes.route("/delete_task", methods=['POST'])
@login_required
def delete_task():
    """
    Delete task indicated by user via json
    """
    data = request.get_json()
    task_uuid = data.get('task_uuid')
    try:
        db_session.query(SavedTasks).filter_by(
            user_id=session['user_id'], task_uuid=task_uuid).delete()
        db_session.query(CustomTasks).filter_by(
            user_id=session['user_id'], task_uuid=task_uuid).delete()
        db_session.query(CustomInput).filter_by(user_id=session['user_id'], uuid=task_uuid).delete()
        db_session.commit()
        return jsonify(success=True)
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        flash("Error deleting task.")
        return redirect(url_for('task_routes.customtasks'))


def uncheck_task(saved, new, errors):
    """
    Update db with tasks user has unchecked
    """
    for task in saved:
        if task not in new:
            try:
                db_session.query(SavedTasks).filter_by(
                    user_id=session['user_id'], task_uuid=task).delete()
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                app.logger.error("Database error: %s", e)
                errors.append("Error updating checked tasks.")
    return errors
