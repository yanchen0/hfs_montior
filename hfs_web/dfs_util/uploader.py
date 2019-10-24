import ftputil
import requests


class Uploader:

    _weedfs_base_url = 'http://193.168.15.135:8888/Samples'

    def __init__(self, host, user=None, pwd=None):
        self.temp_dfs_host = host
        self.temp_dfs_user = user
        self.temp_dfs_pwd = pwd

    def upload_to_gfs(self, md5, f):
        with ftputil.FTPHost(self.temp_dfs_host, self.temp_dfs_user, self.temp_dfs_pwd) as ftp_host:
            dest_dir = '/Samples/{}/{}'.format(md5[:2], md5[2:4])
            if ftp_host.path.isdir(dest_dir):
                ftp_host.upload_if_newer(f, ftp_host.path.join(dest_dir, md5 + '.RS'))
            else:
                return False

    def upload_to_weedfs(self, md5, f):
        if not md5 or not f:
            return False
        url = '{}/{}/{}/{}.RS'.format(self._weedfs_base_url, md5[0:2], md5[2:4], md5)
        
        files = {
            'file': (md5 + '.RS', open(f, 'rb'), 'application/binary')
        }
        resp = requests.post(url, files=files, timeout=120)
        if 300 > resp.status_code >= 200:
            return True
        return False
