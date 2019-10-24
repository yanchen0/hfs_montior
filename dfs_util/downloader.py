import ftputil
import requests
import logging
import hashlib

class Downloader:
    _logger = logging.getLogger('dfs_util.Downloader')
    def __init__(self, weedfs_url, tfs_host, tfs_user=None, tfs_pwd=None):
        self._ftp_host = None
        self.tempdfs_host = tfs_host
        self.tempdfs_user = tfs_user
        self.tempdfs_pwd = tfs_pwd
        self.weedfs_url = weedfs_url

    def download(self, md5, f, from_tempfs=True):
        success, err = self._download_from_weedfs(md5, f)
        if success and self._check_md5(md5, f):
            return success, err
        if from_tempfs:
            self._init_ftp_host()
            success, err = self._download_from_temp_dfs(md5, f)
            if not success:
                return success, err
            return self._check_md5(md5, f)
        return success, err

    def close(self):
        try:
            if self._ftp_host and not self._ftp_host.closed:
                self._ftp_host.close()
        except Exception as ex:
            self._logger.warning(ex)

    def _download_from_temp_dfs(self, md5, f):
        ftp_host = self._ftp_host
        src = '/Samples/{}/{}/{}.RS'.format(md5[:2], md5[2:4], md5)
        print (src)
        if ftp_host.path.isfile(src):
            ftp_host.download(src, f)
            self._logger.debug('download from tempdfs[{}, {}] success'.format(self.tempdfs_host, src))
            return True, None
        else:
            self._logger.info('download from tempdfs[{}, {}] failed, not exist or permission denied'.format(self.tempdfs_host, src))
            return False, 'not exist or permission denied'

    def _download_from_weedfs(self, md5, f):
        url = '{}/{}/{}/{}.RS'.format(self.weedfs_url.rstrip('/'), md5[:2], md5[2:4], md5)
        print (url)
        resp = requests.get(url)
        if resp.status_code != 200:
            self._logger.info('download from weedfs[{}] failed, status_code: {}'.format(url, resp.status_code))
            return False, 'download failed[{0}]'.format(resp.status_code)
        chunk_size = 64 * 1024
        if isinstance(f, (str, bytes)):
            with open(f, 'wb') as fp:
                for chunk in resp.iter_content(chunk_size):
                    fp.write(chunk)
        else:
            for chunk in resp.iter_content(chunk_size):
                f.write(chunk)
        self._logger.debug('download from weedfs[{}] success'.format(url))
        return True, None

    def _check_md5(self, md5, f):
        m = hashlib.md5()
        if isinstance(f, (str, bytes)):
            with open(f, 'rb') as fp:
                m.update(fp.read())
        else:
            m.update(f.read())
        real_md5 = m.hexdigest().upper()
        return md5.upper() == real_md5

    def _init_ftp_host(self):
        if self._ftp_host is None or self._ftp_host.closed:
            self._ftp_host = ftputil.FTPHost(self.tempdfs_host, self.tempdfs_user, self.tempdfs_pwd)
        return self._ftp_host
