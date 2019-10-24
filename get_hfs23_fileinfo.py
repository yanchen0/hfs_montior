import traceback
import requests
from lxml import etree
_json={}
_lis=[]
import utils
logger = utils.init_logger('get_hfs23')
def get_hfs23(url):
    try:
        result = requests.get(url, timeout=20)
        html = etree.HTML(result.content)
        html_data = html.xpath('//*[@id="files"]//tr[@class or @class="even"]')
        for td in  html_data:
            _list=td.xpath('td[@class="nosize"]')
            #folder
            if _list!=[]:
                dirname_list=td.xpath('td/a/@href')
                for dirname in dirname_list:
                    new_url=url+dirname.encode('utf-8').decode("utf-8")
                    get_hfs23(new_url)
            #file
            else:
                ist={}
                if not td.xpath('td/img/@src'):
                    file_list=td.xpath('td/a/@href')
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