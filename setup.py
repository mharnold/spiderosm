import json
import os.path
import setuptools


# get package info from SPIDEROSM.json
with open(os.path.join('spiderosm','SPIDEROSM_INFO.json')) as fp:
    spiderosm_info = json.load(fp)

setuptools.setup(name='spiderosm',
      version=spiderosm_info['version'],
      description='GIS conflation tool for matching street networks.',
      long_description='GIS conflation tool: matches segments in one path network (e.g. streets and trails) to corresponding segments in another, based on geography and network connectivity.  Useful, among other things, for combining jurisdictional centerline data with Open Street Maps data.',
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: GIS'
      ], 
      keywords='GIS conflation OSM OpenStreetMaps centerline jurisdictional street network matcher',
      url=spiderosm_info['homepage'],
      author=spiderosm_info['author'],
      author_email=spiderosm_info['author_email'],
      license=spiderosm_info['license'],
      packages=['spiderosm'],
      install_requires=[
          'pyproj',
          'shapely', #requires geos library, on Mac: "%brew install geos"  
          'pylev',
          'geojson >= 1.0.9',
          'pyshp',
          ],
      extras_require={
          'spatialite' : ['pyspatialite >= 3.0.1'],
          'postgis' : 'psycopg2'

          #imposm.parser is now optional:
          #  DOES NOT WORK UNDER WINDOWS!
          #  needs protobuf / protoc, on Mac: "%brew install protobuf --with-python"
          #  needs tokyo-cabinet, on Mac: "%brew install tokyo-cabinet" ?
          },
      include_package_data=True,
      scripts=[
          'spiderosm/bin/spiderosm_test.py',
          'spiderosm/bin/spiderosm_berkeley.py',
          'spiderosm/bin/spiderosm_portland.py'
      ],
      zip_safe=False)
