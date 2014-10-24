from setuptools import setup

'''
% pip install pyproj
% pip install numpy
% pip install shapely
  shapely requires geos library, on Mac: "%brew install geos"  
% pip install pylev
% pip install geojson
% pip install imposm
  imposm loads psycopg2 (postgis interface!
  imposm needs protobuf / protoc, on Mac: "%brew install protobuf --with-python"
  impost needs tokyo-cabinet, on Mac: "%brew install tokyo-cabinet"
% pip install pyspatialite
  if trouble with this - spiderosm will install fine, but you will not be able
  to output in spaitialite formate.
% pip install pyshp
  for importing shapefiles
'''

setup(name='spiderosm',
      version='0.2.0',
      description='Matches street networks (e.g. jurisdictional centerline and OSM) allowing their attributes to be joined.',
      url='http://spiderosm.org',
      author='Michael Arnold',
      author_email='mha@spiderosm.com',
      license='MIT',
      packages=['spiderosm'],
      install_requires=[
          'pyproj',
          'shapely',
          'pylev',
          'geojson',
          'imposm',
          'pyshp'
      ],
      zip_safe=False)
