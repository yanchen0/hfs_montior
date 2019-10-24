import pika,time,json,logging,os
import utils,time,datetime
from lxml import etree
import traceback
import subprocess
from hfs_model import *
from get_hfs20_fileinfo import *
from get_hfs2122_fileinfo import *
from get_hfs23_fileinfo import *
from get_hfs23beta_fileinfo import *
import requests
import random
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock
import const
import re
import platform as pf
from query_ip_db import CzIp
import concurrent.futures
cz = CzIp()
lock = Lock()
logger = utils.init_logger('hfs_down')
def _upload_file(f_local,md5_):
    print ('upload:',f_local)
    try:
        from dfs_util import Uploader
        uploader = Uploader('g2.rising.net', 'yfgfs', 'qAtL0Q5M')
        for i in range(3):
            try:
                uploader.upload_to_weedfs(md5_, f_local)
                return
            except:
                logger.error(traceback.print_exc())
    except:
        logger.error(traceback.format_exc())

def _submit_sample_info(f_local,download_url,tags):
    if f_local is None or not os.path.isfile(f_local):
        return
    s_info = {
        'md5': utils.calc_file_hash(f_local, 'md5'),
        'sha1': utils.calc_file_hash(f_local, 'sha1'),
        'sha256': utils.calc_file_hash(f_local, 'sha256'),
        'size': os.path.getsize(f_local),
        'source': {
            'key': tags,
            'fname': os.path.split(f_local)[1],
            'info': {
                'download_url': download_url,
                'msg': 'downloaded from Malicious URL'
            }
        }
    }
    url = 'http://193.168.15.10/centralservice/dataservice.ashx'
    headers = {'content-type': 'application/json'}
    payload = {
        'method': 'sample_submit',
        'params': {
            'sample': s_info
        },
        'jsonrpc': '2.0',
        'id': random.randint(10 ** 6, 10 ** 7)
    }
    print('submit sample info: {}'.format(s_info))
    try:    
        resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        if resp.status_code != 200:
            print('submit sample info failed, status_code: {}, {}'.format(resp.status_code, resp.content))
            logger.error('submit sample info failed, status_code: {}, {}'.format(resp.status_code, resp.content))
            #return False
        else:
            logger.info("submit sample info successfully")
    except :
        traceback.print_exc()

def update_hfs_host(host,port,location,hfs_version,host_status,hfs_tag):
    try:
        session = Session()
        if hfs_tag=='hfs_down':
            current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            query = session.query(hfs_host)
            query.filter(hfs_host.host_name == host,hfs_host.port == port).update({\
                hfs_host.last_crawl_time:current_time,\
                hfs_host.location:location,\
                hfs_host.version:hfs_version,\
                hfs_host.status:host_status})
            session.commit()
            print ('update hfs_host: host:%s, port:%s,location:%s,hfs_host_last_crawl_time:%s,hfs_version:%s,status:%s'%(host,port,location,current_time,hfs_version,host_status))
            logger.info('update hfs_host: host:%s, port:%s,location:%s,hfs_host_last_crawl_time:%s,hfs_version:%s,status:%s'%(host,port,location,current_time,hfs_version,host_status))
        else:
            current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            query = session.query(hfs_host)
            query.filter(hfs_host.host_name == host,hfs_host.port == port).update({\
                hfs_host.version:hfs_version,\
                hfs_host.location:location,\
                hfs_host.status:host_status})
            session.commit()
            print ('update hfs_host: host:%s, port:%s,location:%s,hfs_version:%s,status:%s'%(host,port,location,hfs_version,host_status))
            logger.info('update hfs_host: host:%s, port:%s,location:%s,hfs_version:%s,status:%s'%(host,port,location,hfs_version,host_status))
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()

def insert_hfs_file_info(host_id,url_id,md5):
    try:
        session = Session()
        current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session.add(hfs_file_info(host_id=host_id,url_id=url_id, md5=md5,download_time=current_time))
        session.commit()
        print ('insert hfs_file_info: host_id:%s,url_id:%s, md5:%s,download_time:%s'%(host_id,url_id,md5,current_time))
        logger.info('insert hfs_file_info: host_id:%s, url_id:%s,md5:%s,download_time:%s'%(host_id,url_id,md5,current_time))
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()

def get_host_id_by_host_port(host,port):
    try:
        session = Session()
        query = session.query(hfs_host)
        obj=query.filter(hfs_host.host_name == host,hfs_host.port == port).first()
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()
    return obj.id

def get_url_id_by_hfs_host_url(url):
    try:
        session = Session()
        query = session.query(hfs_host_url)
        obj=query.filter(hfs_host_url.url == url).first()
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()
    return obj.id

def insert_hfs_host_url(host_id,hfs_file_url,host_status):
    try:
        session = Session()
        current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session.add(hfs_host_url(url=hfs_file_url,host_id=host_id,status=1,add_time=current_time,last_crawl_time=''))
        print ('insert hfs_host_url : url:%s,host_id:%s,status:%s,add_time:%s'%(hfs_file_url,host_id,host_status,current_time))
        logger.info('insert hfs_host_url : url:%s,host_id:%s,status:%s,add_time:%s'%(hfs_file_url,host_id,host_status,current_time))
        session.commit()
    except Exception:
        pass
        #logger.error(traceback.format_exc())
    finally:
        Session.remove()

def get_hfs_host_status(host,url):
    try:
        hfs_version=''
        location=''
        status=0
        try:
            if re.match(r"\d+\.\d+\.\d+\.\d+", host):
                result=cz.get_addr_by_ip(host)
                if result!='未找到该IP的地址':
                    location=result.split(' ')[0]
        except Exception:
            logger.error(traceback.format_exc())
        result = requests.get(url, timeout=20, allow_redirects=False)
        if result.status_code==200:
            if 'Server' in result.headers:
                if "HFS" in result.headers['Server']:
                    status=1
                    hfs_version=result.headers['Server']
    except Exception:
        logger.error(traceback.format_exc())
    return location,hfs_version,status

def time_calc(startTime, endTime):
    try:
        startTime2 = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
        endTime2 = datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
        seconds = (endTime2 - startTime2).seconds
        total_seconds = (endTime2 - startTime2).total_seconds()
        hous = total_seconds / 3600
    except Exception:
        logger.error(traceback.format_exc())
    return int(hous)

def hfs_down_file(host_id,url_id,hfs_file_url):
    try:
        down_path='tmp'
        file_name = hfs_file_url[hfs_file_url.rfind('/') + 1:]
        local_file = os.path.join(down_path, file_name)
        timestamp ='{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())
        local_file = local_file + "_" + timestamp
        if pf.system()=="Windows":
            subprocess.call(["wget.exe",'-t','3','-T','10','-c',hfs_file_url,'-O',os.path.join(local_file)])
        else:
            subprocess.call(["wget",'-t','3','-T','10','-c',hfs_file_url,'-O',os.path.join(local_file)])
        if os.path.getsize(os.path.join(os.getcwd(),local_file))>0:
            file_md5=utils.calc_file_hash(local_file, 'md5')
            insert_hfs_file_info(host_id,url_id,file_md5)
            return local_file,file_md5
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        if os.path.getsize(os.path.join(os.getcwd(),local_file))==0:
            try:
                os.remove(os.path.join(os.getcwd(),local_file))
            except Exception:
                logger.error(traceback.format_exc())
    return False,False

def update_hfs_host_url(hfs_file_url,hfs_host_url_status,tags):
    if tags:
        try:
            session = Session()
            query = session.query(hfs_host_url)
            query.filter(hfs_host_url.url == hfs_file_url).update({\
                hfs_host_url.status:hfs_host_url_status})
            session.commit()
            print ('update_hfs_host_url : hfs_file_url:%s,status:%s'%(hfs_file_url,hfs_host_url_status))
            logger.info('update_hfs_host_url : hfs_file_url:%s,status:%s'%(hfs_file_url,hfs_host_url_status))
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            Session.remove()
    else:
        try:
            current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            session = Session()
            query = session.query(hfs_host_url)
            query.filter(hfs_host_url.url == hfs_file_url).update({\
                hfs_host_url.last_crawl_time:current_time})
            session.commit()
            print ('update_hfs_host_url : hfs_file_url:%s,last_crawl_time:%s'%(hfs_file_url,current_time))
            logger.info('update_hfs_host_url : hfs_file_url:%s,last_crawl_time:%s'%(hfs_file_url,current_time))
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            Session.remove()

def convert_size_to_bytes(size_str):
    try:
        multipliers = {
            'kilobyte':  1024,
            'megabyte':  1024 ** 2,
            'gigabyte':  1024 ** 3,
            'terabyte':  1024 ** 4,
            'petabyte':  1024 ** 5,
            'exabyte':   1024 ** 6,
            'zetabyte':  1024 ** 7,
            'yottabyte': 1024 ** 8,
            'kb': 1024,
            'mb': 1024**2,
            'gb': 1024**3,
            'tb': 1024**4,
            'pb': 1024**5,
            'eb': 1024**6,
            'zb': 1024**7,
            'yb': 1024**8,
        }

        for suffix in multipliers:
            size_str = size_str.lower().strip().strip('s')
            if size_str.lower().endswith(suffix):
                return int(float(size_str[0:-len(suffix)]) * multipliers[suffix])
        else:
            if size_str.endswith('b'):
                size_str = size_str[0:-1]
            elif size_str.endswith('byte'):
                size_str = size_str[0:-4]
        return int(size_str)
    except Exception:
        logger.error(traceback.format_exc())

class get_hfs_down_file_url:
    def __init__(self,host,port,hfs_tag):
        self.host = host
        self.port = port
        self.hfs_tag = hfs_tag
        self.interrupt_requested = False

    def download_and_submit_files_by_host_id(self,host_id):
        try:
            session = Session()
            query = session.query(hfs_host_url)
            hfs_host_url_list=query.filter(hfs_host_url.host_id ==host_id).all()
            Session.remove()
            for hfs_file_url in hfs_host_url_list:
                if self.interrupt_requested:
                    print("Interrupted at", hfs_file_url)
                    break 
                tags=False
                update_hfs_host_url(hfs_file_url.url,-1,tags)
                tags=True
                url_id=get_url_id_by_hfs_host_url(hfs_file_url.url)
                file_path,file_md5=hfs_down_file(host_id,url_id,hfs_file_url.url)
                if file_path:
                    update_hfs_host_url(hfs_file_url.url,1,tags)
                    logger.info("upload file:{0} {1}".format(file_path,file_md5))
                    _upload_file(file_path,file_md5)
                    logger.info("submit file info:{0} {1}".format(file_path,hfs_file_url.url))
                    _submit_sample_info(file_path,hfs_file_url.url,'LG')
                    try:
                        os.remove(file_path)
                    except Exception:
                        logger.error(traceback.format_exc())
                else:
                    update_hfs_host_url(hfs_file_url.url,0,tags)
        except Exception:
            logger.error(traceback.format_exc())

    def __call__(self):
        global lock
        try:
            host_id=get_host_id_by_host_port(self.host,self.port)
            url = "http://{0}:{1}/".format(self.host,self.port)
            print (url)
            lock.acquire()
            global _json
            global _lis
            _json={}
            _lis=[]
            _json['hfs_url']=url
            _json['hfs_info']=[]
            location,hfs_version,host_status = get_hfs_host_status(self.host,url)
            update_hfs_host(self.host,self.port,location,hfs_version,host_status,self.hfs_tag)
            version_info=False
            if 'HFS 2.3' in hfs_version:
                if 'beta' not in hfs_version:
                    if host_status:
                        try:
                            result = requests.get(url, timeout=20)
                            file_info=get_hfs23(url)
                            logger.info(file_info)
                            version_info=True
                            print (file_info)
                            time.sleep(5)
                        except Exception:
                            logger.error(traceback.format_exc())
                else:
                    if host_status:
                        try:
                            result = requests.get(url, timeout=20)
                            file_info=get_hfs23beta(url)
                            logger.info(file_info)
                            version_info=True
                            print (file_info)
                            time.sleep(5)
                        except Exception:
                            logger.error(traceback.format_exc())
            elif 'HFS 2.0' in hfs_version:
                if host_status:
                    try:
                        result = requests.get(url, timeout=20)
                        file_info=get_hfs20(url[:-1])
                        logger.info(file_info)
                        version_info=True
                        print (file_info)
                        time.sleep(5)
                    except Exception:
                        logger.error(traceback.format_exc())
            elif 'HFS 2.1' in hfs_version or 'HFS 2.2' in hfs_version:
                if host_status:
                    try:
                        result = requests.get(url, timeout=20)
                        file_info=get_hfs2122(url)
                        logger.info(file_info)
                        version_info=True
                        print (file_info)
                        time.sleep(5)
                    except Exception:
                        logger.error(traceback.format_exc())
            if version_info:
                if file_info['hfs_info']!=[]:
                    for i in file_info['hfs_info']:
                        hfs_file_url=i['hfs_file_url']
                        hfs_file_size=i['hfs_file_size'].replace(' ','')
                        if hfs_file_size!='':
                            byte_size=convert_size_to_bytes(hfs_file_size)
                            if byte_size<32*1024*1024:
                                insert_hfs_host_url(host_id,hfs_file_url,1)
                    self.download_and_submit_files_by_host_id(host_id)
            lock.release()
        except Exception:
            logger.error(traceback.format_exc())

    def interrupt(self):
        self.interrupt_requested = True

def start_work_with_timeout(host,port,tag,time_out):
    with ThreadPoolExecutor(max_workers=1) as execute_downloader:
        task=get_hfs_down_file_url(host,port,tag)
        future=execute_downloader.submit(task)
        try:
            future.result(timeout=time_out)
        except concurrent.futures.TimeoutError:
            task.interrupt()

def hfs_db_query():
    try:
        _host_port_lst=[]
        current_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session = Session()
        hfs_host_all = session.query(hfs_host).all()
        Session.remove()
        for hfs_host_date in hfs_host_all:
            startTime=hfs_host_date.last_crawl_time
            endTime=current_time
            host=hfs_host_date.host_name
            port=hfs_host_date.port
            if startTime!='':
                loop_time=hfs_host_date.crawl_interval
                if time_calc(startTime,endTime)>=loop_time:  
                    _host_port_lst.append([host,port])
            else:
                _host_port_lst.append([host,port])
        executor = ThreadPoolExecutor(max_workers=3)
        for host,port in _host_port_lst:
            executor.submit(start_work_with_timeout,host,port,'hfs_down',1200)
        executor.shutdown(wait=False)
    except Exception:
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    while True:
        hfs_db_query()
        time.sleep(3600)