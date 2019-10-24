# NetScan		

分布式多线程全网扫描		 

  		  
![Alt text](https://github.com/yanchen0/hfs_montior/blob/master/1.jpg)

  		  
![Alt text](https://github.com/yanchen0/hfs_montior/blob/master/2.jpg)


实现功能：		
hfs_auto_import.py 
队列拿数据（server==HFS）
ip = obj['host']
port = obj['port']
location='' （从离线数据库获取）
###################################################
hfs_host数据库操作：
如果：IP and port存在：更新状态 status==0 or status==1
否则添加:
（ip,port,location,add_time=当前时间,last_crawl_time='' （空）,crawl_interval=24（默认）,version='',status=1)
###################################################
hfs_down功能：
循环查询/1小时，并下载 hfs_host数据 （开3个线程池）
if last_crawl_time='' （空）
    url抓取+下载流程
else：
    if 现在时间 - last_crawl_time >=crawl_interval ：
        url抓取+下载流程

细分流程：
1）url抓取+下载流程：
更新 hfs_host.last_crawl_time
访问页面：如果存活（ststus==200）：更新 version status=1
否则更新 status=0 并 退出流程

2）获取url信息
对获取到的每个条目都进行数据库插入操作（hfs_host_url.status=1）

3）保存当前时间
从数据库里取出这个host的所有url，更新它的hfs_host_url.last_crawl_time（使用之前保存的时间），然后逐个下载

4）对于单个url
if 下载成功
	hfs_host_url.status=1
	向hfs_file_info插入一条新数据（download_time使用之前保存的时间）
else
	status=0

###################################
if 查询host的所有url存在:
	更新（last_crawl_time）
else：
	入库

update_hfs_host_url(hfs_file_url,1)