import os
import cgi
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import re
import logging
logging.basicConfig(level=logging.DEBUG)

from htmlentitydefs import name2codepoint as n2cp

class CTVException(Exception):
    pass


def transform_stream_url(url, swf_url):
    match = re.match(r"rtmpe?://(?P<netloc>[\w\d\.]+)/(?P<live_od>(?:\w+))/(?P<path>[^\?]+)(?:\?(?P<querystring>.*))?", url)
    parts = dict(match.groupdict())
    if "." in parts['path']:
	parts['extension'] = parts['path'].rsplit(".",1)[-1].lower()
    else:
	parts['extension'] = ''
	
    parts['path'] = parts['path'].rsplit(".",1)[0]
    parts['swfurl'] = swf_url
    parts['amp'] = '&'
    parts['q'] = '?'
    
    if 'querystring' not in parts or not parts['querystring']:
	parts['querystring'] = ''	    
	parts['amp'] = ''
	parts['q'] = ''

    if parts['extension'] == 'mp4':
	res = "rtmpe://%(netloc)s/%(live_od)s?ovpfv=2.1.4%(amp)s%(querystring)s playpath=%(extension)s:%(path)s.%(extension)s swfurl=%(swfurl)s" % parts
    else:
	res = "rtmpe://%(netloc)s/%(live_od)s?ovpfv=2.1.4%(amp)s%(querystring)s playpath=%(path)s%(q)s%(querystring)s swfurl=%(swfurl)s" % parts		
    
    if parts['live_od'] == 'live':
	res += " live=true"
	
    return res


def qasplit(chars, sep=",", quote="'"):
    """ 
    Quote aware split 
    """
    if sep == quote:
	raise Exception("sep and quote cannot be the same character")
    
    can_split = True
    splitpoints = [-1]
    last_c = None
    for index, c in enumerate(chars):
        if c == quote and last_c != "\\":
	    can_split = not can_split
		
        elif c == sep and can_split:
            splitpoints.append(index)
	last_c = c
    if not can_split:
        raise ValueError("Unterminated quote")
    
    splitpoints.append(len(chars))

    slices = [chars[splitpoints[i]+1:splitpoints[i+1]] for i in range(len(splitpoints)-1)]
    return slices


def parse_bad_json(json):
    pairs = qasplit(json.lstrip(" {").rstrip("} "))
    data = {}
    for pair in pairs:
	key, value = [t.strip() for t in pair.split(":",1)]
	if value.isdigit():
	    value = int(value)
	elif "." in value:
	    try:
		value = float(value)
	    except (ValueError,TypeError):
		pass
	    
	elif value.startswith("'") and value.endswith("'"):
	    value = value[1:-1]
	elif value == 'true':
	    value = True
	elif value == 'false':
	    value = False
	elif value == 'null':
	    value = None	    
	
	if isinstance(value, basestring):
	    
	    value = decode_htmlentities(value).replace(r"\'", r"'")
	    
	data[key] = value
	
    return data
	
	              
    
    
def substitute_entity(match):
    ent = match.group(2)
    if match.group(1) == "#":
        return unichr(int(ent))
    else:
        cp = n2cp.get(ent)

        if cp:
            return unichr(cp)
        else:
            return match.group()

	
def decode_htmlentities(string):
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")
    return entity_re.subn(substitute_entity, string)[0]


def get_page(url):
    retries = 0
    while retries < 4:
        logging.debug("fetching %s" % (url,))
        try:
            return urllib2.urlopen(url)
        except (urllib2.HTTPError, urllib2.URLError), e:
            retries += 1
    raise CTVException("Failed to retrieve page: %s" %(url,))

def get_soup(url):
    return BeautifulSoup(get_page(url))


def urldecode(query):
    d = {}
    a = query.split('&')
    for s in a:
        if s.find('='):
            k,v = map(urllib.unquote_plus, s.split('='))
	    if v == 'None':
		v = None
	    d[k] = v
    return d

def get_classes(element):
        return re.split(r'\s+', element['class'])
    
if __name__ == "__main__":    
    print parse_bad_json(TEST_JS)