import requests
import traceback
import requests
from lxml import etree
_json={}
_lis=[]
import utils
logger = utils.init_logger('get_hfs23beta')
def get_hfs23beta(url):
	try:
		result = requests.get(url, timeout=20)
		html = etree.HTML(result.content)
		html_data = html.xpath('//*[@id="files"]//tr[@class="selectable " or @class="selectable even"]')
		for td in html_data:
			_list=td.xpath('td[@class="nosize"]')
			#folder
			if _list!=[]:
				dirname_list=td.xpath('td/a/@href')
				for dirname in dirname_list:
					if td.xpath('td/img')==[]:
						new_url=url+dirname
						get_hfs23beta(new_url)
			#file
			else:
				ist={}
				file_list=td.xpath('td/a/@href')
				if td.xpath('td/img')==[]:
					ist['hfs_file_url']=url+file_list[0]
					file_info=[]
					file_list=td.xpath('td/text()')
					for i in file_list:
						file_info.append(i.replace('\t','').replace('\r','').replace('\n','').replace(' ',''))
					ist['hfs_file_size']=file_info[3]
					ist['hfs_file_download_times']=file_info[5]
					_lis.append(ist)
		_json['hfs_info']=_lis

	except Exception:
		logger.error(traceback.format_exc())
	return _json
