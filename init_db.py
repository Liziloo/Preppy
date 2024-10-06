"""
Module to set up sql database inside docker container
"""

import csv

from dbmodels import Base, DisasterSupplies, DisasterTasks, Sits, StateDisasters, States, Supplies, Tasks
from preppydb import db_session


def init_db():
    """
    Function to create database inside docker container and fill with initial data
    """

    # Drop existing tables
    Base.metadata.drop_all(bind=db_session.bind)

    # Create db tables
    Base.metadata.create_all(bind=db_session.bind)

    # Insert initial data into tables from csv files
    with open('sits.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        sits_data = [Sits(**row) for row in reader]
        db_session.bulk_save_objects(sits_data)
        db_session.commit()

    with open('states.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        states_data = [States(**row) for row in reader]
        db_session.bulk_save_objects(states_data)
        db_session.commit()

    with open('supplies.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        supplies_data = [Supplies(**row) for row in reader]
        db_session.bulk_save_objects(supplies_data)
        db_session.commit()

    with open('tasks.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        tasks_data = [Tasks(**row) for row in reader]
        db_session.bulk_save_objects(tasks_data)
        db_session.commit()

    with open('disastersupplies.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        disaster_supplies_data = [DisasterSupplies(**row) for row in reader]
        db_session.bulk_save_objects(disaster_supplies_data)
        db_session.commit()

    with open('disastertasks.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        disaster_tasks_data = [DisasterTasks(**row) for row in reader]
        db_session.bulk_save_objects(disaster_tasks_data)
        db_session.commit()

    with open('statedisasters.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        state_disasters_data = [StateDisasters(**row) for row in reader]
        db_session.bulk_save_objects(state_disasters_data)
        db_session.commit()


if __name__ == "__main__":
    init_db()
