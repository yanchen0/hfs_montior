# -*- coding: UTF-8 -*-
from app import app, db
import re,time,json
from app.models import  *
from flask import render_template, redirect, session, url_for, request, g, jsonify,flash,make_response
import traceback
import sys,os
import utils
logger = utils.init_logger('hfs_web')
query_data_url=[]
query_data_md5=[]	
sys.path.append("..")
from hfs_down import get_hfs_down_file_url
from hfs_down import get_url_id_by_hfs_host_url
from hfs_down import get_host_id_by_host_port
_dir=os.path.dirname(os.getcwd())
white_file=os.path.join(_dir,'white_list.txt')
white_list=[]
if os.path.exists(white_file):
    try:
        with open (white_file,'r') as fp:
            for i in fp:
                white_list.append(i.strip())
    except:
        logger.error(traceback.format_exc())
@app.route('/', methods=['GET', 'POST'])
def hfs_host_main():
	global query_data_url
	query_data_url=[]
	if request.method == 'GET':
		#db.create_all()
		return render_template('index.html')
	else:
		temp_list=[]
		hfs_host_list=hfs_host.query.all()
		for hfs_host_date in hfs_host_list:
			_list={}
			_list["host_name"]=hfs_host_date.host_name
			_list["port"]=hfs_host_date.port
			_list["location"]=hfs_host_date.location
			_list["add_time"]=hfs_host_date.add_time
			_list["last_crawl_time"]=hfs_host_date.last_crawl_time
			_list["crawl_interval"]=hfs_host_date.crawl_interval
			_list["version"]=hfs_host_date.version
			_list["status"]=hfs_host_date.status
			temp_list.append(_list)
		return jsonify(temp_list)

def get_host_id_by_ip_port(host_name,port):
	try:
		obj=hfs_host.query.filter(hfs_host.host_name==host_name,hfs_host.port==port).first()
	except Exception:
		logger.error(traceback.print_exc())
	return obj.id

@app.route('/hfs_host_add', methods=['GET', 'POST'])
def hfs_host_add():
	if request.method == 'GET':
		return render_template('hfs_host_add.html')
	else:
		try:
			_list={}
			host_url= request.form['host_url']
			host_port= request.form['host_port']
			
			host_time= request.form['host_time']
			result=hfs_host.query.filter(hfs_host.host_name==host_url,hfs_host.port==host_port).first()
			if result!=None:
				#添加失败,数据库存在
				_list['host_url']=host_url
				_list['host_port']=host_port
				_list['host_time']=host_time
				_list['status']=0
			else:
				host_and_port=host_url+':'+host_port
				if host_and_port not in white_list:
					current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
					dt=hfs_host(host_name=host_url,port=host_port,location='',\
						add_time=current_time,last_crawl_time='',\
						crawl_interval=host_time,\
						version=''\
						,status=1)   
					db.session.add(dt)
					db.session.commit()
					db.session.close()
					#添加成功
					_list['host_url']=host_url
					_list['host_port']=host_port
					_list['host_time']=host_time
					_list['status']=1
				else:
					#添加失败，命中白名单
					_list['host_url']=host_url
					_list['host_port']=host_port
					_list['host_time']=host_time
					_list['status']=2
			print (_list)
		except Exception:	
			logger.error(traceback.print_exc())
		return jsonify(_list)

@app.route('/hfs_host_modify', methods=['GET', 'POST'])
def hfs_host_modify():
	if request.method == 'GET':
		return render_template('hfs_host_add.html')
	else:
		try:
			_list={}
			host_url= request.form['host_url']
			host_port= request.form['host_port']
			host_time= request.form['host_time']
			result=hfs_host.query.filter(hfs_host.host_name==host_url,hfs_host.port==host_port).first()
			if result!=None:
				hfs_host.query.filter(hfs_host.host_name == host_url,hfs_host.port == host_port).update({hfs_host.crawl_interval:host_time})
				db.session.commit()
				db.session.close()
				#修改成功
				_list['host_url']=host_url
				_list['host_port']=host_port
				_list['host_time']=host_time
				_list['status']=1
			else:
				#修改失败, 数据库中不存在
				_list['host_url']=host_url
				_list['host_port']=host_port
				_list['host_time']=host_time
				_list['status']=0
			print (_list)
		except Exception:	
			logger.error(traceback.print_exc())
		return jsonify(_list)

@app.route('/crawlNow_tasks', methods=['GET', 'POST'])
def crawlNow_tasks():
	_list={}
	if request.method == 'POST':
		try:
			data = json.loads(request.form.get('data'))
			host=data['host_name']
			port=data['port']
			run=get_hfs_down_file_url(host,port,'hfs_web')
			run()
			_list['status']=1
		except Exception:	
			_list['status']=0
			logger.error(traceback.print_exc())
		return jsonify(_list)

@app.route('/host_del', methods=['GET', 'POST'])
def host_del():
	_list={}
	if request.method == 'POST':
		try:
			data = json.loads(request.form.get('data'))
			host=data['host_name']
			port=data['port']
			_host_id=get_host_id_by_host_port(host,port)
			db.session.query(hfs_file_info).filter(hfs_file_info.host_id==_host_id).delete()
			db.session.commit()
			db.session.query(hfs_host_url).filter(hfs_host_url.host_id==_host_id).delete()
			db.session.commit()
			db.session.query(hfs_host).filter(hfs_host.id==_host_id).delete()
			db.session.commit()
			_list['status']=1
		except Exception:	
			_list['status']=0
			logger.error(traceback.print_exc())
		return render_template('index.html')

@app.route('/hfs_host_url', methods=['GET', 'POST'])
def hfs_host_url_main():
	global query_data_url
	global query_data_md5
	query_data_md5=[]
	if request.method == 'GET':
		return render_template('hfs_host_url.html')
	else:
		try:
			if request.get_data()!=b'':
				data = json.loads(request.get_data())
				if 'url' in data:
					global query_data_url
					query_data_url=[]
					ii=data['url'].split(':')
					host_name=ii[1].replace('//','')
					port=ii[2].split('/')[0]
					_id=get_host_id_by_host_port(host_name,port)
					hfs_host_url_list=hfs_host_url.query.filter(hfs_host_url.host_id==_id).all()
					for i in hfs_host_url_list:
						_list={}
						_list["url"]=i.url
						_list["status"]=i.status
						_list["add_time"]=i.add_time
						_list["last_crawl_time"]=i.last_crawl_time
						query_data_url.append(_list)
					return jsonify(query_data_url)
				else:
					host_name=data['data']['host_name']
					port=data['data']['port']
					_id=get_host_id_by_host_port(host_name,port)
					hfs_host_url_list=hfs_host_url.query.filter(hfs_host_url.host_id==_id).all()
					for i in hfs_host_url_list:
						_list={}
						_list["url"]=i.url
						_list["status"]=i.status
						_list["add_time"]=i.add_time
						_list["last_crawl_time"]=i.last_crawl_time
						query_data_url.append(_list)
		except Exception:	
			logger.error(traceback.print_exc())
		return jsonify(query_data_url)

@app.route('/host_url_del', methods=['GET', 'POST'])
def host_url_del():
	_list={}
	if request.method == 'POST':
		try:
			data = json.loads(request.form.get('data'))
			host_url=data['host_url']
			_id=get_url_id_by_hfs_host_url(host_url)
			db.session.query(hfs_file_info).filter(hfs_file_info.url_id==_id).delete()
			db.session.commit()
			db.session.query(hfs_host_url).filter_by(url=host_url).delete()
			db.session.commit()
			_list['status']=1
		except Exception:	
			_list['status']=0
			logger.error(traceback.print_exc())
		return render_template('index.html')

@app.route('/host_url_query_md5', methods=['GET', 'POST'])
def host_url_query_md5():
	global query_data_md5
	if request.method == 'GET':
		return render_template('hfs_host_url_md5.html')
	else:
		try:
			if request.get_data()!=b'':
				data = json.loads(request.get_data())
				host_url=data['data']['host_url']
				_id=get_url_id_by_hfs_host_url(host_url)
				hfs_host_url_md5_list=hfs_file_info.query.filter(hfs_file_info.url_id==_id).group_by(hfs_file_info.md5).all()
				for i in hfs_host_url_md5_list:
					_list={}
					_list["md5"]=i.md5
					_list["down_time"]=i.download_time
					query_data_md5.append(_list)					
		except Exception:	
			logger.error(traceback.print_exc())
		return jsonify(query_data_md5)
