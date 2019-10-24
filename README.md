# hfs_moitor

HFS服务器监控平台	 

  		  
![Alt text](https://github.com/yanchen0/hfs_montior/blob/master/1.jpg)

  		  
![Alt text](https://github.com/yanchen0/hfs_montior/blob/master/2.jpg)


实现功能：		
hfs_auto_import.py<br>     
队列拿数据（server==HFS
ip = obj['host']<br> 
port = obj['port']<br> 
location='' （从离线数据库获取）<br> 
###################################################<br> 
hfs_host数据库操作：<br> 
如果：IP and port存在：更新状态 status==0 or status==1<br> 
否则添加:<br> 
（ip,port,location,add_time=当前时间,last_crawl_time='' （空）,crawl_interval=24（默认）,version='',status=1)<br> 
###################################################<br> 
hfs_down功能：<br> 
循环查询/1小时，并下载 hfs_host数据 （开3个线程池）<br> 
if last_crawl_time='' （空）<br> 
    url抓取+下载流程<br> 
else：<br> 
    if 现在时间 - last_crawl_time >=crawl_interval ：<br> 
        url抓取+下载流程<br> 

细分流程：<br> 
1）url抓取+下载流程：<br> 
更新 hfs_host.last_crawl_time<br> 
访问页面：如果存活（ststus==200）：更新 version status=1<br> 
否则更新 status=0 并 退出流程<br> 

2）获取url信息<br> 
对获取到的每个条目都进行数据库插入操作（hfs_host_url.status=1）<br> 

3）保存当前时间<br> 
从数据库里取出这个host的所有url，更新它的hfs_host_url.last_crawl_time（使用之前保存的时间），然后逐个下载<br> 

4）对于单个url<br> 
if 下载成功<br> 
	hfs_host_url.status=1<br> 
	向hfs_file_info插入一条新数据（download_time使用之前保存的时间）<br> 
else<br> 
	status=0<br> 

###################################<br> 
if 查询host的所有url存在:<br> 
	更新（last_crawl_time）<br> 
else：<br> 
	入库<br> 

update_hfs_host_url(hfs_file_url,1)<br> 