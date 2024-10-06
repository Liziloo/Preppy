"""
SQLAlchemy table model definitions
"""

import os

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

load_dotenv()

Base = declarative_base()


class Calendar(Base):
    """
    Table to store household member names input by users for use in the routine schedule
    """
    __tablename__ = 'calendar'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(Text)


class Contacts(Base):
    """
    Table to store user emergency contacts
    """
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)


class Coordinates(Base):
    """
    Table to store coordinates of user emergency meetup locations
    """
    __tablename__ = 'coordinates'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    latitude = Column(Float, primary_key=True, nullable=False)
    longitude = Column(Float, primary_key=True, nullable=False)
    title = Column(Text, default='')


class CustomInput(Base):
    """
    Table to store custom supplies and tasks input by users
    """
    __tablename__ = 'custominput'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    uuid = Column(Text, primary_key=True, nullable=False)


class CustomTasks(Base):
    """
    Table to store the ids of tasks that users want included in their to-do lists
    """
    __tablename__ = 'customtasks'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    task_uuid = Column(Text, primary_key=True, nullable=False)


class DisasterSupplies(Base):
    """
    Table associating item ids with the ids of disasters they might be needed for
    """
    __tablename__ = 'disastersupplies'
    disaster_id = Column(Integer, ForeignKey('sits.id'), primary_key=True, nullable=False)
    item_id = Column(Integer, ForeignKey('supplies.id'), primary_key=True, nullable=False)


class DisasterTasks(Base):
    """
    Table associating task ids with the ids of disasters they might be needed for
    """
    __tablename__ = 'disastertasks'
    disaster_id = Column(Integer, ForeignKey('sits.id'), primary_key=True, nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True, nullable=False)
    task_uuid = Column(Integer, ForeignKey('tasks.uuid'), primary_key=True, nullable=False)


class Events(Base):
    """
    Table to store routine schedule events input by users
    """
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    person_id = Column(Integer, ForeignKey('calendar.id'), nullable=False)
    title = Column(Text, nullable=False)
    start_time = Column(Text, nullable=False)
    start_day = Column(Text, nullable=False)
    end_time = Column(Text, nullable=False)
    end_day = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    description = Column(Text)


class Families(Base):
    """
    Table to store household makeup information, including whether anyone has special needs (a column for use in later development)
    """
    __tablename__ = 'families'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    last_name = Column(Text, nullable=False)
    adults = Column(Integer, default=0, nullable=False)
    seniors = Column(Integer, default=0, nullable=False)
    children = Column(Integer, default=0, nullable=False)
    pets = Column(Integer, default=0, nullable=False)
    state_id = Column(Integer, ForeignKey('states.id'))
    special_needs = Column(Text, default='No', nullable=False)


class GoBags(Base):
    """
    Table to record what supplies users want for their gobags
    """
    __tablename__ = 'gobags'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    supply_uuid = Column(Text, ForeignKey('supplies.uuid'), primary_key=True, nullable=False)


class Medical(Base):
    """
    Table to store user household personal medical information
    """
    __tablename__ = 'medical'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    blood_type = Column(Text, nullable=False)
    medications = Column(Text)
    allergies = Column(Text)
    other = Column(Text)
    insurance = Column(Text)
    policy = Column(Text)


class Providers(Base):
    """
    Table to store user medical provider info
    """
    __tablename__ = 'providers'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    first_name = Column(Text)
    last_name = Column(Text, nullable=False)
    patient = Column(Text)
    phone = Column(Text, nullable=False)
    address = Column(Text)


class SavedSupplies(Base):
    """
    Table to store supplies users have already checked off, as well as whether they're included in a gobag or shelter-in-place kit
    """
    __tablename__ = 'savedsupplies'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    supply_uuid = Column(Text, ForeignKey('supplies.uuid'), primary_key=True, nullable=False)
    gobag = Column(Text, nullable=False, default='No')
    shelter = Column(Text, nullable=False, default='No')


class SavedTasks(Base):
    """
    Table to store tasks users have already checked off
    """
    __tablename__ = 'savedtasks'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    task_uuid = Column(Text, ForeignKey('tasks.uuid'), primary_key=True, nullable=False)


class SecFileMetadata(Base):
    """
    Table to store metadata for encrypted files uploaded by users
    """
    __tablename__ = 'secfilemetadata'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(Text, nullable=False)
    secure_filename = Column(Text, nullable=False)


class Shelters(Base):
    """
    Table to store information on what supplies users choose to include in their shelter-in-place kits
    """
    __tablename__ = 'shelters'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    supply_uuid = Column(Text, ForeignKey('supplies.uuid'), primary_key=True, nullable=False)


class Sits(Base):
    """
    Table listing common emergency situations and assigning an id to each
    """
    __tablename__ = 'sits'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    sit = Column(Text, nullable=False)
    probability = Column(Integer, nullable=False)


class StateDisasters(Base):
    """
    Table associating state ids with the ids of disasters most likely to affect residents
    """
    __tablename__ = 'statedisasters'
    state_id = Column(Integer, ForeignKey('states.id'), primary_key=True, nullable=False)
    disaster_id = Column(Integer, ForeignKey('sits.id'), primary_key=True)


class States(Base):
    """
    List of U.S. states for use by various functions
    """
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    state = Column(Text, unique=True, nullable=False)
    full_name = Column(Text, unique=True, nullable=False)


class Supplies(Base):
    """
    Table with predefined supplies with info on age class as well as per-person amount (for later development) and whether for gobags or shelter-in-place
    """
    __tablename__ = 'supplies'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(Text, unique=True, nullable=False)
    item = Column(Text, nullable=False)
    per_person = Column(Float)
    gobag = Column(Text, default='No', nullable=False)
    shelter = Column(Text, default='No', nullable=False)
    adult = Column(Text, default='No', nullable=False)
    child = Column(Text, default='No', nullable=False)
    senior = Column(Text, default='No', nullable=False)
    pet = Column(Text, default='No', nullable=False)


class Tasks(Base):
    """
    Table of predefined tasks associated with emergency prep. Column for task description included for further development
    """
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(Text, unique=True)
    task = Column(Text, nullable=False)
    description = Column(Text)


class Tokens(Base):
    """
    Table to store password reset tokens with timestamps and associated user ids
    """
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    timestamp = Column(DateTime, default=func.now, nullable=False)


class Users(Base):
    """
    Table for all registered users, their ids and hashed passwords
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(255), nullable=False, unique=True)
    hash = Column(String(128), nullable=False)


database_url = os.getenv("DATABASE_URL", "sqlite:///preppy.db")
engine = create_engine(database_url)
Base.metadata.create_all(engine)
