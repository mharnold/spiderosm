'''
Miscellaneous shared code for spiderosm
'''

import os
import urllib
import sys
import time

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

def test():
    print 'date_ymd:', date_ymd()
    print 'date_ymdhms:', date_ymdhms()

    print_now('a',noNewLine=True)
    time.sleep(2)
    print_now('b',noNewLine=True)
    time.sleep(2)
    print_now('c')
    time.sleep(5)
    print_now('d')

if __name__ == '__main__':
    test()
