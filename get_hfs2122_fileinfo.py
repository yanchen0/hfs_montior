import traceback
import requests
from lxml import etree
_lis=[]
_json={}
import utils
logger = utils.init_logger('get_hfs2122')
def get_hfs2122(html):
	try:
		result = requests.get(html, timeout=20)
		new_html = etree.HTML(result.content)
		p=new_html.xpath('//table[@cellpadding="5"]//tr')
		if p:
			for td in p:
				#folder
				if td.xpath('td/a/img/@src')[0]=='/~img_folder':
					dir_url=html+td.xpath('td/a/@href')[0]
					try:
						result = requests.get(dir_url, timeout=20)
						if result.status_code!=401:
							get_hfs2122(dir_url)
					except Exception:
						logger.error(traceback.format_exc())
				else:
					ist={}
					#file
					file_url= html+td.xpath('td/a/@href')[0]
					try:
						result = requests.get(file_url, timeout=20)
						if result.status_code!=401:
							ist['hfs_file_url']=file_url
							ist['hfs_file_size']=td.xpath('td/text()')[1].replace('\t','').replace('\r','').replace('\n','').replace(' ','')
							ist['hfs_file_download_times']=td.xpath('td/text()')[3].replace('\t','').replace('\r','').replace('\n','').replace(' ','')
							_lis.append(ist)
					except Exception:
						logger.error(traceback.format_exc())
		_json['hfs_info']=_lis
	except Exception:
		logger.error(traceback.format_exc())
	return _json

