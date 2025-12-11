import os
import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, LargeBinary, text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def get_db_url():
    return os.environ.get("DB_URL", "postgresql://rdkit_user:mysecretpassword@localhost:5432/rdkit_database")

def get_engine():
    return create_engine(get_db_url())

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

class Issues(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)    
    user = Column(String(50), nullable=True)
    description = Column(String(2000), nullable=True)
    date_created = Column(Date, default=datetime.date.today)    
    molfile = Column(LargeBinary, nullable=True) 
    inchi  = Column(String(1000), nullable=True)
    auxinfo  = Column(String(2000), nullable=True)
    inchikey = Column(String(20), nullable=True) 
    logs  = Column(String(2000), nullable=True) 
    options  = Column(String(2000), nullable=True) 
    inchi_version  = Column(String(255), nullable=True)     

    def __repr__(self):
        return f"<Issue(id='{self.id}', description='{self.description}', user='{self.user}')>"

    @classmethod
    def check_connection(cls):
        try:
            engine = create_engine(get_db_url())
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
            "molfile": "base64-encoded-molfile",
            "inchi": "InChI=1S/example",
            "auxinfo": "AuxInfo=example",
            "inchikey": "EXAMPLEINCHIKEY",
            "logs": "Example logs",
            "options": "Example options",
            "inchi_version": "1.05"
        }
        return json.dumps(example, indent=2)

    @classmethod
    def add(cls, session, **kwargs):    
        try:
            issue = cls(**kwargs)
            session.add(issue)
            session.commit()
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