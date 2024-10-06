"""
Module sets up database connection based on .env file
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

database_url = os.getenv("DATABASE_URL", "sqlite:///preppy.db")
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
db_session = Session()
