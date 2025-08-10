import re
import sqlalchemy as sa

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, mapped_column, backref
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Boolean, JSON, \
    ARRAY

from db import Base


class User(Base):
    """
    Represents a NLP user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        name (str): The full name of the user. This field is optional.
        nickname (str): A nickname for the user. This field is optional.
        lastActive (datetime): The last time the user was active. This field is optional.
        onServer (bool): Indicates whether the user is currently active on the server. Defaults to True.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    lastActive = Column(DateTime, nullable=True)
    onServer = Column(Boolean, nullable=True, default=True)


class Character(Base):
    """
    Represents a D&D Beyond character that has been approved on the NLP Server

    Attributes:
        id (int): The unique identifier for the character.
        name (str): The name of the character. This field is required.
        url (str): A URL associated with the character. This field is required.
        race (str): The race of the character. This field is required.
        level (int): The level of the character. This field is required.
        stats (dict): A JSON object containing various statistics for the character. This field is required.
        classes (dict): A JSON object listing the classes and levels of the character. This field is required.
        subclasses (dict): A JSON object listing the subclasses of the character. This field is required.
        feats (dict): A JSON array listing the feats of the character. This field is required.
        invocations (dict): A JSON array listing the invocations of the character. This field is required.
        valid (bool): Indicates whether the character is valid. Defaults to True.
        user_id (int): The foreign key that relates the character to a user.

    Relationships:
        user (User): The user that owns this character.
    """
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    race = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    stats = Column(JSON, nullable=False)
    classes = Column(JSON, nullable=False)
    subclasses = Column(JSON, nullable=False)
    feats = Column(JSON, nullable=False)
    invocations = Column(JSON, nullable=False)
    valid = Column(Boolean, nullable=False, default=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", lazy="joined")
