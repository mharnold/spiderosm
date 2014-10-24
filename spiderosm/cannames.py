'''
Canonical street names!
(To allow name matching between OSM and Portland City DB.)
'''
import string

import pylev

# ratio of edit distance between strings to string length (= max number of edits possible)
def levenshtein_ratio(s1, s2):
    assert len(s1) > 0 and len(s2) > 0
    return pylev.levenshtein(s1, s2) / float(max(len(s1),len(s2)))

# guess at probability names refer to the same street
def match_probability(names1, names2):
    assert len(names1) > 0 and len(names2) > 0
    p = 0

    for name1 in names1:
        can1 = canonical_street_name(name1)
        for name2 in names2:
            can2 = canonical_street_name(name2)
            #print 'DEBUG', name1, name2, can1, can2, pylev.levenshtein(can1,can2)
            #print 'DEBUG ratio:', levenshtein_ratio(can1,can2)
            p = max(p, 1-levenshtein_ratio(can1,can2))

    return p

# rate name match on scale of 0 to 100
def match_score(names1,names2):
    return round(100*match_probability(names1,names2))

# TODO: consider adding USPS canonical abbreviations for street types
# http://cpansearch.perl.org/src/SDERLE/Geo-Coder-US-0.21/US/Codes.pm
# cped to portland_peds/Codes.pm.txt 
rewrites = {
		'NORTH':'N',
		'SOUTH':'S',
		'EAST':'E',
		'WEST':'W',
		'NORTHEAST':'NE',
		'NORTHWEST':'NW',
		'SOUTHEAST':'SE',
		'SOUTHWEST':'SW',
	
		'AVENUE':'AVE',
                'BRIDGE':'BRG',
		'BOULEVARD':'BLVD',
		'CIRCLE':'CIR',
		'COURT':'CT',
		'DRIVE':'DR',
                'FREEWAY':'',
                'FWY':'',
		'HIGHWAY':'HWY',
                'JUNIOR':'JR',
		'LANE':'LN',
		'MOUNT':'MT',
		'PARKWAY':'PKWY',
		'PLACE':'PL',
		'ROAD':'RD',
		'SAINT':'ST',
		'STREET':'ST',
                'SUMMIT':'SMT',
		'TERRACE':'TER',
                'TRAIL':'TRL'
 		}

def restrict_chars(name):
    ALLOWED_CHARS = string.ascii_letters + string.digits + " "  # others get mapped to ' '
    IGNORE_CHARS = "'"
    out = []
    for c in name:
        if c in ALLOWED_CHARS: 
            out.append(c) 
        else:
            if c not in IGNORE_CHARS: out.append(' ')
    return ''.join(out)

def canonical_street_name(name):
    '''
    Regularizes street name to facilitate comparison.  
    Converts to all caps and applies standard abbreviations.
    '''
    if name is None: return None;

    #print "DEBUG name in: ", name
    space = ' ' 

    # restrict character set: simplicity, security
    name = restrict_chars(name)

    # all caps
    name = name.upper()

    # words
    words=name.strip().split(space)
    words = [w for w in words if w != '']
    #print "DEBUG words: ", words

    # rewrites
    new_words = []
    for word in words:
            if rewrites.has_key(word):
                    new=rewrites[word]
                    if len(new)>0: new_words.append(new)
                    continue
            if len(word)>1 and word[0]=='I' and word[1:].isdigit(): 
                    new_words.append('I')
                    new_words.append(word[1:])
                    continue
            new_words.append(word)
    words = new_words

    # two word rewrites
    new_words = []
    skip=False
    for i in range(len(words)):
        if skip:
            skip=False
            continue
        if i == len(words)-1:
            #last word
            new_words.append(words[i])
            continue
        if words[i] == 'TRANSIT' and words[i+1] == 'CENTER':
            new_words.append('TC')
            skip=True
            continue
        if words[i] == 'UNITED' and words[i+1] == 'STATES':
            new_words.append('US')
            skip=True
            continue
        if words[i+1].isdigit() and words[i] in ['HWY','US','OR']:
            new_words.append('HWY')
            new_words.append(words[i+1])
            skip=True
            continue
        if words[i] == 'MC':
            new_words.append('MC' + words[i+1])
            skip=True
            continue
        if words[i] == 'LE':
            new_words.append('LE' + words[i+1])
            skip=True
            continue
        new_words.append(words[i])
    words = new_words

    # single spaces between words
    out = ' '.join(words).strip()

    return out

def test_can(name1,name2=None):
    can1 = canonical_street_name(name1)
    #print "test_can, name1: '%s'  can1: '%s'" % (name1, can1) 
    assert can1 == canonical_street_name(can1)

    if name2:	
	can2 = canonical_street_name(name2)
	#print "test_can, name2: '%s'  can2: '%s'" % (name2, can2) 
	assert can2 == canonical_street_name(can2)
	assert can1 == can2
		
def test():
	test_can("Southeast Sunburst Lane","SE SUNBURST LN")
	test_can("Northeast Saint George Street","NE ST GEORGE ST")
	test_can("NE HALSEY ST FRONTAGE RD","Northeast Halsey Street Frontage Road")
        test_can("I84 FWY","I 84")
        test_can(" 13133","13133")
        test_can("US BANCORP COLUMBIA CENTER TC","UNITED STATES BANCORP COLUMBIA CENTER TRANSIT CENTER")
        test_can("COEUR DALENE DR", "COEUR D'ALENE DR")
        test_can("BURNSIDE BRG", "BURNSIDE BRIDGE")
        test_can("BLAZER TRL","BLAZER TRAIL")
        test_can("HWY 30","US 30")
        test_can("MARTIN LUTHER KING  JUNIOR BLVD","MARTIN LUTHER KING JR BLVD")
        test_can("Mc Gee Street", "McGee Street")
        test_can("Saint Alban's Road", "ST ALBANS RD")
        test_can("Le Roy Avenue", "LeRoy Avenue")

        # 'fuzzy matching' (edit distance)
        assert match_score(['A St'],['B Street']) == 75.0


	print 'cannames PASS'
#doit
test()
