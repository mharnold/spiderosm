'''
Miscellaneous shared code for spiderosm
'''

import os
import urllib
import sys
import time
import zipfile

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

def update_file_from_url(filename,url):
    if not os.path.exists(os.path.dirname(filename)): os.makedirs(os.path.dirname(filename))

    # get current file size
    file_size = None
    if os.path.exists(filename):
        file_size = os.stat(filename).st_size

    # get size of url content
    url_size = None
    f = urllib.urlopen(url)
    i = f.info()
    url_size = int(i.getheader('content-length'))
    f.close()

    print 'file_size', file_size
    print 'url_size', url_size
    if file_size != url_size:
        print 'Downloading: %s to %s' % (url,filename)
        urllib.urlretrieve(url,filename)

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

def test(all_=False):
    if all_: _test_dates()
    if all_: _test_print_now()
    print 'misc PASS'

#doit
test()
#test(all_=True)
