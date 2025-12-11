import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, BLOB
from sqlalchemy.orm import sessionmaker, declarative_base


DB_URL = "postgresql://rdkit_user:mysecretpassword@localhost:5432/rdkit_database"

# Create an engine and a session
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initializes the database and creates tables if they do not exist."""
    Base.metadata.create_all(engine)

class Issues(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)    
    user = Column(String(50), nullable=True)
    description = Column(String(2000), nullable=True)
    date_created = Column(Date, default=datetime.date.today)    
    molfile = Column(BLOB, nullable=True) 
    inchi  = Column(String(1000), nullable=True)
    auxinfo  = Column(String(2000), nullable=True)
    inchikey = Column(String(20), nullable=True) 
    logs  = Column(String(2000), nullable=True) 
    options  = Column(String(2000), nullable=True) 
    inchi_version  = Column(String(255), nullable=True)     

    def __repr__(self):
        return f"<Issue(id='{self.id}', description='{self.description}', user='{self.user}')>"

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
    