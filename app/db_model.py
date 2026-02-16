import os
import datetime
import json
from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey, DateTime, LargeBinary, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel
from typing import Optional
from config import settings

Base = declarative_base()

def get_engine():    
    
    engine = None
    
    try:
        engine = create_engine(settings.database_url)
    except Exception as ex:
        print("ERROR in get_engine", str(ex))
        
    return engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine) 
    session = Session()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initializes the database and creates tables if they do not exist."""
    try:
        Base.metadata.create_all(get_engine())
        return True
    except Exception as ex:
        print("ERROR initializing DB", str(ex))
        return False

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    disabled = Column(Boolean, nullable=False)
        
    @classmethod
    def get_user_by_username(cls, session, username: str):
        return session.query(cls).filter(cls.username == username).first()


class Issues(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)    
    user = Column(String(50), nullable=True)
    description = Column(String(2000), nullable=True)
    date_created = Column(DateTime, default=datetime.datetime.now)    
    molfile_v2 = Column(String(10000), nullable=True)     
    molfile_v3 = Column(String(10000), nullable=True)
    inchi  = Column(String(2000), nullable=True)
    auxinfo  = Column(String(4000), nullable=True)
    input_source = Column(String(500), nullable=True)
    inchikey = Column(String(50), nullable=True) 
    logs  = Column(String(2000), nullable=True) 
    options  = Column(String(2000), nullable=True) 
    inchi_version  = Column(String(255), nullable=True)     

    def __repr__(self):
        return f"<Issue(id='{self.id}', description='{self.description}', user='{self.user}')>"

    @classmethod
    def check_connection(cls):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, ""
        except Exception as ex:
            print("Error", str(ex))
            return False, str(ex)

    @classmethod
    def example_json(cls):
        example = {
            "id": 1,
            "user": "example_user",
            "description": "Example issue description",
            "date_created": "2025-01-01",
            "molfile_v2": "molfile as string",
            "molfile_v3": "molfile as string",
            "inchi": "InChI=1S/example",
            "auxinfo": "AuxInfo=example",
            "inchikey": "EXAMPLEINCHIKEY",
            "logs": "Example logs",
            "options": "Example options",
            "inchi_version": "1.05",
            "input_source": "inchi_web_demo"
        }
        return json.dumps(example, indent=2)

    @classmethod
    def add(cls, session, **kwargs):    
        try:
            issue = cls(**kwargs)
            session.add(issue)
            session.commit()
            session.refresh(issue)
            return issue
        finally:
            session.close()
    
    @classmethod
    def get_all_sorted_by_date(cls, session):
        """Get all issues sorted by date_created ascending."""
        return session.query(cls).order_by(cls.date_created.asc()).all()
    
    @classmethod
    def get_nof_issues(cls, session):        
        return session.query(cls).count()
    
    @classmethod
    def to_dict(cls, issue):

        data = {
            "id": issue.id,
            "user": issue.user,
            "description": issue.description,
            "date_created": str(issue.date_created) if issue.date_created else None,
            "molfile_v2": issue.molfile_v2,
            "molfile_v3": issue.molfile_v3,
            "inchi": issue.inchi,
            "auxinfo": issue.auxinfo,
            "inchikey": issue.inchikey,
            "logs": issue.logs,
            "options": issue.options,
            "inchi_version": issue.inchi_version,
            "input_source": issue.input_source
        }
        return data    

class Issue_in(BaseModel):
    user: Optional[str] = None
    description: Optional[str] = None
    molfile_v2: Optional[str] = None
    molfile_v3: Optional[str] = None
    inchi: Optional[str] = None
    auxinfo: Optional[str] = None
    inchikey: Optional[str] = None
    logs: Optional[str] = None
    options: Optional[str] = None
    inchi_version: Optional[str] = None
    input_source: Optional[str] = None
    