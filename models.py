import logging

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer

# Setup SQLAlchemy
Base = automap_base()

logger = logging.getLogger(__name__)

class Phonebook(Base):
    __tablename__ = 'phonebook'

    id = Column('idphonebook', Integer, primary_key=True)
    firstname = Column(String(255))
    lastname = Column(String(255))
    mobile = Column('phonenumber', String(255))
    company = Column(String)
    mobile2 = Column('pv_an0', String)
    home = Column('pv_an1', String)
    home2 = Column('pv_an2', String)
    business = Column('pv_an3', String)
    business2 = Column('pv_an4', String)
    email = Column('pv_an5', String)
    other = Column('pv_an6', String)
    business_fax = Column('pv_an7', String)
    home_fax = Column('pv_an8', String)
    pager = Column('pv_an9', String)
    fkidtenant = Column(Integer)
    fkiddn = Column(Integer)


class IPBXBinder(object):

    def __init__(self, db, dbuser, dbpass, host='localhost', port=5432):
        print('toto')
        self.db = db
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.host = host
        self.port = port
        self.create_engine()
        self.prepare()
        self.session = None

    def prepare(self):
        """Create the automap using our class."""
        Base.prepare(self.engine, reflect=True)
        self.Session = sessionmaker(bind=self.engine)

    def create_engine(self):
        """Returns a connection and a metadata object."""
        # We connect with the help of the PostgreSQL URL
        # postgresql://federer:grandestslam@localhost:5432/tennis
        url = 'postgresql://{}:{}@{}:{}/{}'
        url = url.format(self.dbuser, self.dbpass, self.host, self.port, self.db)

        # The return value of create_engine() is our connection object
        self.engine = create_engine(url, client_encoding='utf8')

    def get_session(self):
        """Get a unique session accross calls."""
        if not self.session:
            self.session = self.Session()
        return self.session
