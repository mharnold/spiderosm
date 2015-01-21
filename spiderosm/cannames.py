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

# CHARACTER RESTRICTION
# allowed_chars are left unchanged
# ignored_chars are deleted
# characters that are neither in allowed_chars nor in ingored_chars are mapped to space (' ') 
allowed_chars = string.ascii_letters + string.digits + " "  
ignored_chars = "'"

# SINGLE WORD SUBSTITUTIONS 
# applied after words are mapped to all upper case
word_substitutions = {
        # directionals
        'NORTH':'N',
        'SOUTH':'S',
        'EAST':'E',
        'WEST':'W',
        'NORTHEAST':'NE',
        'NORTHWEST':'NW',
        'SOUTHEAST':'SE',
        'SOUTHWEST':'SW',

        # misc
        'JUNIOR':'JR',
        'SAINT':'ST',

        # street types 
        # USPS standard street types -> canonical postal abbreviations (as found int TIGER/Line)
        # Source: http://cpansearch.perl.org/src/SDERLE/Geo-Coder-US-0.21/US/Codes.pm
        'ALLEE':'ALY',
        'ALLEY':'ALY',
        'ALLY':'ALY',
        'ANEX':'ANX',
        'ANNEX':'ANX',
        'ANNX':'ANX',
        'ARCADE':'ARC',
        'AV':'AVE',
        'AVEN':'AVE',
        'AVENU':'AVE',
        'AVENUE':'AVE',
        'AVN':'AVE',
        'AVNUE':'AVE',
        'BAYOO':'BYU',
        'BAYOU':'BYU',
        'BEACH':'BCH',
        'BEND':'BND',
        'BLUF':'BLF',
        'BLUFF':'BLF',
        'BLUFFS':'BLFS',
        'BOT':'BTM',
        'BOTTM':'BTM',
        'BOTTOM':'BTM',
        'BOUL':'BLVD',
        'BOULEVARD':'BLVD',
        'BOULV':'BLVD',
        'BRANCH':'BR',
        'BRDGE':'BRG',
        'BRIDGE':'BRG',
        'BRNCH':'BR',
        'BROOK':'BRK',
        'BROOKS':'BRKS',
        'BURG':'BG',
        'BURGS':'BGS',
        'BYPA':'BYP',
        'BYPAS':'BYP',
        'BYPASS':'BYP',
        'BYPS':'BYP',
        'CAMP':'CP',
        'CANYN':'CYN',
        'CANYON':'CYN',
        'CAPE':'CPE',
        'CAUSEWAY':'CSWY',
        'CAUSWAY':'CSWY',
        'CEN':'CTR',
        'CENT':'CTR',
        'CENTER':'CTR',
        'CENTERS':'CTRS',
        'CENTR':'CTR',
        'CENTRE':'CTR',
        'CIRC':'CIR',
        'CIRCL':'CIR',
        'CIRCLE':'CIR',
        'CIRCLES':'CIRS',
        'CK':'CRK',
        'CLIFF':'CLF',
        'CLIFFS':'CLFS',
        'CLUB':'CLB',
        'CMP':'CP',
        'CNTER':'CTR',
        'CNTR':'CTR',
        'CNYN':'CYN',
        'COMMON':'CMN',
        'CORNER':'COR',
        'CORNERS':'CORS',
        'COURSE':'CRSE',
        'COURT':'CT',
        'COURTS':'CTS',
        'COVE':'CV',
        'COVES':'CVS',
        'CR':'CRK',
        'CRCL':'CIR',
        'CRCLE':'CIR',
        'CRECENT':'CRES',
        'CREEK':'CRK',
        'CRESCENT':'CRES',
        'CRESENT':'CRES',
        'CREST':'CRST',
        'CROSSING':'XING',
        'CROSSROAD':'XRD',
        'CRSCNT':'CRES',
        'CRSENT':'CRES',
        'CRSNT':'CRES',
        'CRSSING':'XING',
        'CRSSNG':'XING',
        'CRT':'CT',
        'CURVE':'CURV',
        'DALE':'DL',
        'DAM':'DM',
        'DIV':'DV',
        'DIVIDE':'DV',
        'DRIV':'DR',
        'DRIVE':'DR',
        'DRIVES':'DRS',
        'DRV':'DR',
        'DVD':'DV',
        'ESTATE':'EST',
        'ESTATES':'ESTS',
        'EXP':'EXPY',
        'EXPR':'EXPY',
        'EXPRESS':'EXPY',
        'EXPRESSWAY':'EXPY',
        'EXPW':'EXPY',
        'EXTENSION':'EXT',
        'EXTENSIONS':'EXTS',
        'EXTN':'EXT',
        'EXTNSN':'EXT',
        'FALLS':'FLS',
        'FERRY':'FRY',
        'FIELD':'FLD',
        'FIELDS':'FLDS',
        'FLAT':'FLT',
        'FLATS':'FLTS',
        'FORD':'FRD',
        'FORDS':'FRDS',
        'FOREST':'FRST',
        'FORESTS':'FRST',
        'FORG':'FRG',
        'FORGE':'FRG',
        'FORGES':'FRGS',
        'FORK':'FRK',
        'FORKS':'FRKS',
        'FORT':'FT',
        'FREEWAY':'FWY',
        'FREEWY':'FWY',
        'FRRY':'FRY',
        'FRT':'FT',
        'FRWAY':'FWY',
        'FRWY':'FWY',
        'GARDEN':'GDN',
        'GARDENS':'GDNS',
        'GARDN':'GDN',
        'GATEWAY':'GTWY',
        'GATEWY':'GTWY',
        'GATWAY':'GTWY',
        'GLEN':'GLN',
        'GLENS':'GLNS',
        'GRDEN':'GDN',
        'GRDN':'GDN',
        'GRDNS':'GDNS',
        'GREEN':'GRN',
        'GREENS':'GRNS',
        'GROV':'GRV',
        'GROVE':'GRV',
        'GROVES':'GRVS',
        'GTWAY':'GTWY',
        'HARB':'HBR',
        'HARBOR':'HBR',
        'HARBORS':'HBRS',
        'HARBR':'HBR',
        'HAVEN':'HVN',
        'HAVN':'HVN',
        'HEIGHT':'HTS',
        'HEIGHTS':'HTS',
        'HGTS':'HTS',
        'HIGHWAY':'HWY',
        'HIGHWY':'HWY',
        'HILL':'HL',
        'HILLS':'HLS',
        'HIWAY':'HWY',
        'HIWY':'HWY',
        'HLLW':'HOLW',
        'HOLLOW':'HOLW',
        'HOLLOWS':'HOLW',
        'HOLWS':'HOLW',
        'HRBOR':'HBR',
        'HT':'HTS',
        'HWAY':'HWY',
        'INLET':'INLT',
        'ISLAND':'IS',
        'ISLANDS':'ISS',
        'ISLES':'ISLE',
        'ISLND':'IS',
        'ISLNDS':'ISS',
        'JCTION':'JCT',
        'JCTN':'JCT',
        'JCTNS':'JCTS',
        'JUNCTION':'JCT',
        'JUNCTIONS':'JCTS',
        'JUNCTN':'JCT',
        'JUNCTON':'JCT',
        'KEY':'KY',
        'KEYS':'KYS',
        'KNOL':'KNL',
        'KNOLL':'KNL',
        'KNOLLS':'KNLS',
        'LA':'LN',
        'LAKE':'LK',
        'LAKES':'LKS',
        'LANDING':'LNDG',
        'LANE':'LN',
        'LANES':'LN',
        'LDGE':'LDG',
        'LIGHT':'LGT',
        'LIGHTS':'LGTS',
        'LNDNG':'LNDG',
        'LOAF':'LF',
        'LOCK':'LCK',
        'LOCKS':'LCKS',
        'LODG':'LDG',
        'LODGE':'LDG',
        'LOOPS':'LOOP',
        'MANOR':'MNR',
        'MANORS':'MNRS',
        'MEADOW':'MDW',
        'MEADOWS':'MDWS',
        'MEDOWS':'MDWS',
        'MILL':'ML',
        'MILLS':'MLS',
        'MISSION':'MSN',
        'MISSN':'MSN',
        'MNT':'MT',
        'MNTAIN':'MTN',
        'MNTN':'MTN',
        'MNTNS':'MTNS',
        'MOTORWAY':'MTWY',
        'MOUNT':'MT',
        'MOUNTAIN':'MTN',
        'MOUNTAINS':'MTNS',
        'MOUNTIN':'MTN',
        'MSSN':'MSN',
        'MTIN':'MTN',
        'NECK':'NCK',
        'ORCHARD':'ORCH',
        'ORCHRD':'ORCH',
        'OVERPASS':'OPAS',
        'OVL':'OVAL',
        'PARKS':'PARK',
        'PARKWAY':'PKWY',
        'PARKWAYS':'PKWY',
        'PARKWY':'PKWY',
        'PASSAGE':'PSGE',
        'PATHS':'PATH',
        'PIKES':'PIKE',
        'PINE':'PNE',
        'PINES':'PNES',
        'PK':'PARK',
        'PKWAY':'PKWY',
        'PKWYS':'PKWY',
        'PKY':'PKWY',
        'PLACE':'PL',
        'PLAIN':'PLN',
        'PLAINES':'PLNS',
        'PLAINS':'PLNS',
        'PLAZA':'PLZ',
        'PLZA':'PLZ',
        'POINT':'PT',
        'POINTS':'PTS',
        'PORT':'PRT',
        'PORTS':'PRTS',
        'PRAIRIE':'PR',
        'PRARIE':'PR',
        'PRK':'PARK',
        'PRR':'PR',
        'RAD':'RADL',
        'RADIAL':'RADL',
        'RADIEL':'RADL',
        'RANCH':'RNCH',
        'RANCHES':'RNCH',
        'RAPID':'RPD',
        'RAPIDS':'RPDS',
        'RDGE':'RDG',
        'REST':'RST',
        'RIDGE':'RDG',
        'RIDGES':'RDGS',
        'RIVER':'RIV',
        'RIVR':'RIV',
        'RNCHS':'RNCH',
        'ROAD':'RD',
        'ROADS':'RDS',
        'ROUTE':'RTE',
        'RVR':'RIV',
        'SHOAL':'SHL',
        'SHOALS':'SHLS',
        'SHOAR':'SHR',
        'SHOARS':'SHRS',
        'SHORE':'SHR',
        'SHORES':'SHRS',
        'SKYWAY':'SKWY',
        'SPNG':'SPG',
        'SPNGS':'SPGS',
        'SPRING':'SPG',
        'SPRINGS':'SPGS',
        'SPRNG':'SPG',
        'SPRNGS':'SPGS',
        'SPURS':'SPUR',
        'SQR':'SQ',
        'SQRE':'SQ',
        'SQRS':'SQS',
        'SQU':'SQ',
        'SQUARE':'SQ',
        'SQUARES':'SQS',
        'STATION':'STA',
        'STATN':'STA',
        'STN':'STA',
        'STR':'ST',
        'STRAV':'STRA',
        'STRAVE':'STRA',
        'STRAVEN':'STRA',
        'STRAVENUE':'STRA',
        'STRAVN':'STRA',
        'STREAM':'STRM',
        'STREET':'ST',
        'STREETS':'STS',
        'STREME':'STRM',
        'STRT':'ST',
        'STRVN':'STRA',
        'STRVNUE':'STRA',
        'SUMIT':'SMT',
        'SUMITT':'SMT',
        'SUMMIT':'SMT',
        'TERR':'TER',
        'TERRACE':'TER',
        'THROUGHWAY':'TRWY',
        'TPK':'TPKE',
        'TR':'TRL',
        'TRACE':'TRCE',
        'TRACES':'TRCE',
        'TRACK':'TRAK',
        'TRACKS':'TRAK',
        'TRAFFICWAY':'TRFY',
        'TRAIL':'TRL',
        'TRAILS':'TRL',
        'TRK':'TRAK',
        'TRKS':'TRAK',
        'TRLS':'TRL',
        'TRNPK':'TPKE',
        'TRPK':'TPKE',
        'TUNEL':'TUNL',
        'TUNLS':'TUNL',
        'TUNNEL':'TUNL',
        'TUNNELS':'TUNL',
        'TUNNL':'TUNL',
        'TURNPIKE':'TPKE',
        'TURNPK':'TPKE',
        'UNDERPASS':'UPAS',
        'UNION':'UN',
        'UNIONS':'UNS',
        'VALLEY':'VLY',
        'VALLEYS':'VLYS',
        'VALLY':'VLY',
        'VDCT':'VIA',
        'VIADCT':'VIA',
        'VIADUCT':'VIA',
        'VIEW':'VW',
        'VIEWS':'VWS',
        'VILL':'VLG',
        'VILLAG':'VLG',
        'VILLAGE':'VLG',
        'VILLAGES':'VLGS',
        'VILLE':'VL',
        'VILLG':'VLG',
        'VILLIAGE':'VLG',
        'VIST':'VIS',
        'VISTA':'VIS',
        'VLLY':'VLY',
        'VST':'VIS',
        'VSTA':'VIS',
        'WALKS':'WALK',
        'WELL':'WL',
        'WELLS':'WLS',
        'WY':'WAY',
                        }

def restrict_chars(name):
    global allowed_chars, ingored_chars
    out = []
    for c in name:
        if c in allowed_chars: 
            out.append(c) 
        else:
            if c not in ignored_chars: out.append(' ')
    return ''.join(out)

def canonical_street_name(name):
    '''
    Regularizes street name to facilitate comparison.  
    Converts to all caps and applies standard abbreviations.
    '''
    global word_substitutions

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

    # word substitutions
    new_words = []
    for word in words:
            if word_substitutions.has_key(word):
                    new=word_substitutions[word]
                    if len(new)>0: new_words.append(new)
                    continue
            if len(word)>1 and word[0]=='I' and word[1:].isdigit(): 
                    new_words.append('I')
                    new_words.append(word[1:])
                    continue
            new_words.append(word)
    words = new_words

    # delete 'FWY'
    new_words = []
    for word in words:
        if word == 'FWY': continue
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
        if words[i] == 'TRANSIT' and words[i+1] == 'CTR':
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
if __name__ == "__main__":
    test()
