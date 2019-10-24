# -*- coding: UTF-8 -*-

from app import db
class hfs_host(db.Model):
	__tablename__ = 'hfs_host'
	id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
	host_name = db.Column(db.String(64),nullable=False)
	port = db.Column(db.String(5),nullable=False)
	location = db.Column(db.String(32),nullable=False)
	add_time = db.Column(db.String(64),nullable=False)
	last_crawl_time = db.Column(db.String(64),nullable=False)
	crawl_interval=db.Column(db.SmallInteger,nullable=False)
	version = db.Column(db.String(32),nullable=False)
	status = db.Column(db.SmallInteger,nullable=False)
	

class hfs_host_url(db.Model):
	__tablename__ = 'hfs_host_url'
	id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
	url = db.Column(db.String(255),nullable=False,unique=True)
	host_id = db.Column(db.BigInteger,db.ForeignKey('hfs_host.id'))
	status = db.Column(db.SmallInteger,nullable=False)
	add_time = db.Column(db.String(64),nullable=False)
	last_crawl_time = db.Column(db.String(64),nullable=False)


class hfs_file_info(db.Model):
	__tablename__ = 'hfs_file_info'
	id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
	host_id= db.Column(db.BigInteger,db.ForeignKey('hfs_host.id'))
	url_id = db.Column(db.BigInteger,db.ForeignKey('hfs_host_url.id'))
	md5 = db.Column(db.String(32),nullable=False)
	download_time = db.Column(db.String(64),nullable=False)


