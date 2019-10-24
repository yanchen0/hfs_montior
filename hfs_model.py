import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger,String,ForeignKey,VARCHAR,CHAR,SmallInteger
engine = create_engine("mysql+pymysql://root:root@193.168.15.138/hfs_db",encoding='utf-8')
from sqlalchemy.orm import sessionmaker,relationship,scoped_session
Base = declarative_base()

class hfs_host(Base):
	__tablename__ = 'hfs_host'
	id = Column(BigInteger, primary_key=True, autoincrement=True)
	host_name = Column(VARCHAR(64),nullable=False)
	port = Column(VARCHAR(5),nullable=False)
	location = Column(VARCHAR(32),nullable=False)
	add_time = Column(VARCHAR(64),nullable=False)
	last_crawl_time = Column(VARCHAR(64),nullable=False)
	crawl_interval=Column(SmallInteger,nullable=False)
	version = Column(VARCHAR(32),nullable=False)
	status = Column(SmallInteger,nullable=False)

class hfs_host_url(Base):
	__tablename__ = 'hfs_host_url'
	id = Column(BigInteger, primary_key=True, autoincrement=True)
	url = Column(VARCHAR(255),nullable=False,unique=True)
	host_id = Column(BigInteger,ForeignKey('hfs_host.id'))
	status = Column(SmallInteger,nullable=False)
	add_time = Column(VARCHAR(64),nullable=False)
	last_crawl_time = Column(VARCHAR(64),nullable=False)

class hfs_file_info(Base):
	__tablename__ = 'hfs_file_info'
	id = Column(BigInteger, primary_key=True, autoincrement=True)
	host_id = Column(BigInteger,ForeignKey('hfs_host.id'))
	url_id = Column(BigInteger,ForeignKey('hfs_host_url.id'))
	md5 = Column(VARCHAR(32),nullable=False)
	download_time = Column(VARCHAR(64),nullable=False)

class hfs_host_scan(Base):
	__tablename__ = 'hfs_host_scan'
	id = Column(BigInteger, primary_key=True, autoincrement=True)
	host = Column(VARCHAR(64),nullable=False)
	last_scan_time = Column(VARCHAR(64),nullable=False)

DBSession = sessionmaker(bind=engine)
Session = scoped_session(DBSession)

