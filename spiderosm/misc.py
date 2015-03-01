'''
Miscellaneous shared code for spiderosm
'''

import gzip
import os
import StringIO
import sys
import tempfile
import time
import urllib
import urllib2
import zipfile

def percent(num,of):
    '''compute percent, avoiding divide by zero, round to integer'''
    if of==0: return 0
    return round((100.0*num)/of)

def module_loaded_q(mod_name):
    return mod_name in sys.modules.keys()

# print immediately (no buffering)
def print_now(s, noNewLine=False):
    if noNewLine:
        print s,
    else:
        print s
    sys.stdout.flush()

def date_ymd():
    return time.strftime("%Y%m%d")         

def date_ymdhms():
    return time.strftime("%Y%m%d_%H%M%S")  

def unzip(Filename):
    zfile = zipfile.ZipFile(Filename)
    (zipDir,zipFile) = os.path.split(Filename)
    for name in zfile.namelist():
        (subDir, filename) = os.path.split(name)
        dirname = os.path.join(zipDir,subDir)
        # paranoid about escaping from current dir with '..'
        assert not '..' in dirname
        assert not '//' in dirname
        assert not '\\' in dirname
        if dirname=='': dirname='.'
        print "Decompressing " + filename + " on " + dirname
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        zfile.extract(name, dirname)

def gunzip(data_gz):
    buf = StringIO.StringIO(data_gz)
    f = gzip.GzipFile(fileobj=buf)
    data = f.read()
    return data

def url_size(url,parms=None):
    if parms:
        url_parms = urllib.urlencode(url_parms)
        url = url + '?' + url_parms
    response = urllib2.urlopen(url)
    size = response.info().get('content-length')
    return int(size)

# if info set to dictionary, response headers will be added to it.
def get_url(url,parms=None,gzip=False, info=None):
    if parms:
        url_parms = urllib.urlencode(parms)
        url = url + '?' + url_parms
    request = urllib2.Request(url)
    if gzip: request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)
    data = response.read()
    #print 'DEB get_url info:', response.info()
    if response.info().get('Content-Encoding') == 'gzip': data = gunzip(data)

    if info!=None: info.update(response.info())
    return data

# create directories in path (if needed)
def create_dirs(pathname):
    if not pathname: return
    dirs = os.path.dirname(pathname)
    if len(dirs)>0 and not os.path.exists(dirs): os.makedirs(dirs)

# fetch url to file
def retrieve_url(url,filename=None, suffix='', gzip=False):
    # if no filename, create temp file.
    if not filename:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            filename = temp.name

    create_dirs(filename)

    response_headers = {}
    data = get_url(url,gzip=gzip,info=response_headers)

    with open(filename,'w') as f:
        f.write(data)

    return (filename, response_headers)

def update_file_from_url(filename,url,gzip=False):
    create_dirs(filename)

    # get current file size
    file_size = None
    if os.path.exists(filename):
        file_size = os.stat(filename).st_size

    # get size of url content
    url_size1 = url_size(url)

    print 'file_size', file_size
    print 'url_size', url_size1
    if file_size != url_size1:
        print 'Downloading: %s to %s' % (url,filename)
        retrieve_url(url,filename,gzip=gzip)

def _test_percent():
    assert percent(5,10)==50.0
    assert percent(5,0)==0.0

def _test_dates():
    print 'date_ymd:', date_ymd()
    print 'date_ymdhms:', date_ymdhms()

def _test_print_now():
    print_now('a',noNewLine=True)
    time.sleep(2)
    print_now('b',noNewLine=True)
    time.sleep(2)
    print_now('c')
    time.sleep(5)
    print_now('d')

def _test_module_loaded_q():
    assert module_loaded_q('sys')
    assert module_loaded_q('time')
    assert not module_loaded_q('foobar')

def _test_gunzip():
    data = 'hello\n'
    data_gz = '\x1f\x8b\x08\x00\xf4\xe6\xf0T\x00\x03\xcbH\xcd\xc9\xc9\xe7\x02\x00 0:6\x06\x00\x00\x00'

    result = gunzip(data_gz)
    assert result == data

def _test_url_size():
    #print 'url_size:', url_size('http://spiderosm.org')
    assert url_size('http://spiderosm.org') > 0

def _test_update_file_from_url():
    update_file_from_url('spiderosm.html','http://spiderosm.org')

def _test_retrieve_url():
    retrieve_url('http://spiderosm.org','data/s2.html')
    print 'gzipped?:', retrieve_url('http://spiderosm.org','data/gzip_test/s2.html',gzip=True)
    print 'tempfile:', retrieve_url('http://spiderosm.org')
    print 'tempfile:', retrieve_url('http://spiderosm.org',suffix='.html')

def test():
    _test_module_loaded_q()
    _test_percent()
    _test_gunzip()
    _test_url_size()
    _test_retrieve_url()
    #_test_update_file_from_url()
    #_test_dates()
    #_test_print_now()
    print 'misc PASS'

#doit
if __name__ == "__main__":
    test()
