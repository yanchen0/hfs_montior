import pika,time,json,logging,os
import utils,time,datetime
from lxml import etree
import traceback
import utils
from hfs_model import *
import requests
import re
from query_ip_db import CzIp
logger = utils.init_logger('hfs_auto_import')
cz = CzIp()
white_list=[]
if os.path.exists('white_list.txt'):
    try:
        with open ('white_list.txt','r') as fp:
            for i in fp:
                white_list.append(i.strip())
    except:
        logger.error(traceback.format_exc())

def update_and_insert_hfs_host(host,port,location,crawl_interval):
    try:
        _time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session = Session()
        query = session.query(hfs_host)
        objs = query.filter(hfs_host.host_name == host,hfs_host.port == port).first()
        if objs!=None:
            query.filter(hfs_host.host_name == host,hfs_host.port == port).update({\
                hfs_host.status:1})
            print ('host,port found ,update data: host:%s port:%s location:%s,status:1'%(host ,port, location))
            logger.info('host,port found ,update data: host:%s port:%s location:%s,status:1'%(host ,port, location))
        else: 
            session.add(hfs_host(\
                host_name=host,\
                port=port,\
                location=location,\
                add_time=_time,\
                last_crawl_time='',\
                crawl_interval=crawl_interval,\
                version='',\
                status=1))        
            print ('host,port not found ,add data: host:%s port:%s location:%s add_time:%s crawl_interval:%s _version:'' status:1'%(host ,port, location,_time,crawl_interval))
            logger.info('host,port not found ,add data: host:%s port:%s location:%s add_time:%s crawl_interval:%s _version:'' status:1'%(host ,port, location,_time,crawl_interval))
        session.commit()
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()

def time_calc(startTime, endTime):
    try:
        startTime2 = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
        endTime2 = datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
        seconds = (endTime2 - startTime2).seconds
        total_seconds = (endTime2 - startTime2).total_seconds()
        hours = total_seconds / 3600
    except Exception:
        logger.error(traceback.format_exc())
    return int(hours)

def check_port_scan_interval(host):
    try:
        _result=False
        _time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session = Session()
        query = session.query(hfs_host_scan)
        objs = query.filter(hfs_host_scan.host == host).first()
        loop_time=24
        if objs==None:
            session.add(hfs_host_scan(\
            host=host,\
            last_scan_time=_time,\
            )) 
            _result=True     
        else:
            startTime=objs.last_scan_time
            if time_calc(startTime,_time)>=loop_time:  
                query.filter(hfs_host_scan.host == host).update({\
                    hfs_host_scan.last_scan_time:_time})
                _result=True
            else:
                _result=False
        session.commit()
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        Session.remove()
    return _result

def get_host_port_from_url(url):
    try:
        port = 80
        ipPorts = re.findall("^https?://(.*?)/.*", url)
        ipPort = ipPorts[0]
        result = ipPort.split(':')
        if len(result) == 2:
            port = int(result[1])
        host = result[0]
        return host,port
    except Exception:
        logger.error(traceback.format_exc())

def submit_json(body):
    try:
        parameters = pika.URLParameters('amqp://rabbit:rabbit@193.168.15.156/netscan')
        connection = pika.BlockingConnection(parameters)    
        channel = connection.channel()      
        channel.basic_publish(exchange='amq.direct',routing_key='ip_list',body=body,properties=pika.BasicProperties(delivery_mode=2))
        connection.close()  
    except Exception: 
        logger.error(traceback.format_exc())

def hfs_crawl(rabbituri,queue_name):
    while (True):
        try:
            conn = pika.BlockingConnection(pika.URLParameters(rabbituri))
            channel = conn.channel()
            while (True):
                (getok, properties, body) = channel.basic_get(queue_name, no_ack=True)
                if not body:
                    print ('no tasks...')
                    time.sleep(1)
                    continue
                obj = None
                try:
                    obj = json.loads(body.decode())
                except:
                    logger.error('invalid msg,{0}'.format(body.decode))
                if obj:
                    try:
                        if 'url' in obj:
                            hfs_url = obj['url']
                            if 'additional_info' in obj:
                                if 'Response headers' in obj['additional_info']:
                                    if 'server' in obj['additional_info']['Response headers']:
                                        hfs_server = obj['additional_info']['Response headers']['server']
                                        if hfs_server.strip().find('HFS') == 0:
                                            logger.info('tasks: {0}'.format(obj))
                                            host,port = get_host_port_from_url(hfs_url)
                                            #{"ip": "193.168.15.51", "cmd": "-n --open", "tag": "normal"}
                                            location=''
                                            try:
                                                if re.match(r"\d+\.\d+\.\d+\.\d+", host):
                                                    result=cz.get_addr_by_ip(host)
                                                    if result!='未找到该IP的地址':
                                                        location=result.split(' ')[0]
                                            except Exception:
                                                logger.error(traceback.format_exc())
                                            crawl_interval=24
                                            host_and_port=host+':'+str(port)
                                            if host_and_port not in white_list:
                                                update_and_insert_hfs_host(host,port,location,crawl_interval) 
                                                if check_port_scan_interval(host):
                                                    net_scan_dict={}
                                                    net_scan_dict['ip']=host
                                                    net_scan_dict['cmd']='-n --open'
                                                    net_scan_dict['tag']='hfs_url'
                                                    submit_json(json.dumps(net_scan_dict))                       
                    except Exception:
                        logger.error(traceback.format_exc())
        except Exception:
            logging.error(traceback.print_exc())
            time.sleep(3)

if __name__ == '__main__':
    rabbituri = 'amqp://rabbit:rabbit@193.168.15.156/uri'
    queue_name = "vt-url-hfs"
    hfs_crawl(rabbituri,queue_name)
    
#{"host":"193.168,15.1","port":"80"}