import subprocess
import json
import traceback
import random
import os
import logging
from hashlib import md5, sha1, sha256
from itertools import chain
from functools import partial

import requests

_some_chars = []
for i in chain(range(0x30, 0x3A), range(ord('A'), ord('Z') + 1), range(ord('a'), ord('z') + 1)):
    _some_chars.append(chr(i))


def exec_qga_command(vm_name, cmd, timeout=30):
    try:
        p = subprocess.Popen(['virsh', 'qemu-agent-command', vm_name, cmd], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=timeout)
        if p.returncode != 0:
            return False, err.decode(errors='ignore')
        return True, json.loads(out.decode())['return']
    except Exception as ex:
        traceback.print_exc()
        return False, str(ex)


def exec_vm_command(*args, timeout=30):
    return exec_command('virsh', *args, cwd=None, timeout=timeout)


def exec_command(exec_file, *args, cwd=None, timeout=30):
    try:
        p = subprocess.Popen([exec_file] + list(args), stdout=subprocess.PIPE,stderr=subprocess.PIPE, cwd=cwd)
        out, err = p.communicate(timeout=timeout)
        if p.returncode != 0:
            return False, err.decode(errors='ignore'), None
        return True, None, out.decode(errors='ignore')
    except Exception as ex:
        traceback.print_exc()
        return False, str(ex), None


def gen_some_str(len_=10):
    size = len(_some_chars)
    arr = []
    for _ in range(len_):
        arr.append(_some_chars[random.randint(0, size - 1)])
    return ''.join(arr)


def gen_mac():
    arr = []
    for _ in range(3):
        arr.append(random.randint(0, 255))
    return '52:54:00:' + ':'.join([format(byte, '02x') for byte in arr])


def calc_hash(input_, algo='md5'):
    if isinstance(input_, (bytes, bytearray)):
        pass
    elif isinstance(input_, str):
        input_ = input_.encode()
    elif isinstance(input_, dict):
        input_ = json.dumps(input_, separators=(',', ':'), sort_keys=True).encode()
    else:
        input_ = str(input_).encode()
    if not algo:
        raise ValueError('algo is empty or none')
    algo = algo.lower()
    if algo == 'md5':
        h = md5()
    elif algo == 'sha1':
        h = sha1()
    elif algo == 'sha256':
        h = sha256()
    else:
        raise ValueError('invalid algo: {}'.format(algo))
    h.update(input_)
    return h.hexdigest().upper()


def calc_file_hash(local_f, algo='md5'):
    algo = algo.lower()
    if algo == 'md5':
        h = md5()
    elif algo == 'sha1':
        h = sha1()
    elif algo == 'sha256':
        h = sha256()
    else:
        raise ValueError('invalid algo: {}'.format(algo))
    with open(local_f, 'rb') as fp:
        for chunk in iter(partial(fp.read, 4 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def get_file_formats(local_f):
    if not os.path.isfile(local_f):
        return None
    ffr_tool = os.path.join(os.path.split(os.path.abspath(__file__))[0], '../tools/ffr/ffr.out')
    if not os.path.isfile(ffr_tool):
        logger.warning('ffr tool not exists, {}'.format(ffr_tool))
        return None
    success, err_msg, out_msg = exec_command(ffr_tool, local_f, cwd=os.path.split(ffr_tool)[0], timeout=30)
    if not success or not out_msg:
        logger.warning('get file formats failed, {}, {}'.format(local_f, err_msg))
        return None
    idx_begin = out_msg.find('[')
    idx_end = out_msg.find(']')
    if idx_end > idx_begin >= 0:
        return json.loads(out_msg[idx_begin:idx_end + 1])
    return None


def download_file(down_url, f_path, hash_value=None):
    try:
        resp = requests.get(down_url, timeout=60, stream=True, allow_redirects=True)
        if resp.status_code < 200 or resp.status_code >= 300:
            return False, 'download file failed[{}]'.format(resp.status_code)
        with open(f_path, 'wb') as fp:
            for chunk in resp.iter_content(chunk_size=4 * 1024):
                fp.write(chunk)
    except Exception as ex:
        logger.error('download failed, {}, {}'.format(down_url, ex))
        return False, 'download file failed'

    if hash_value and hash_value.upper() != calc_file_hash(f_path):
        logger.warning('file hash value not equal, {}, {}'.format(f_path, hash_value))
        return False, 'check file hash failed'
    return True, None


def feedback_result(url, info):
    try:
        resp = requests.post(url, data=json.dumps(info).encode(),
                             headers={'Content-Type': 'application/json;charset=utf-8'}, timeout=10)
        if resp.status_code < 200 or resp.status_code >= 300:
            logger.error('feedback failed, {}, status_code: {}'.format(url, resp.status_code))
            return False
        return True
    except Exception as ex:
        logger.error('feedback failed, {}, {}'.format(url, ex))
        return False


def init_logger(name=None, log_file=None):
    from logging import Formatter
    from logging.handlers import RotatingFileHandler
    import sys

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not log_file:
        log_file = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], name + '.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
    logger.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.ERROR)
    stdout_handler.setFormatter(Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
    logger.addHandler(stdout_handler)

    return logger


logger = init_logger(__name__, os.path.join(os.path.split(os.path.abspath(__file__))[0], __name__ + '.log'))

# print(gen_some_str(100))
# print(gen_mac())
# print(get_file_formats('/home/rising/test/analyse.zip'))
