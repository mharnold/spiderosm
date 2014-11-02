from setuptools import setup

setup(name='spiderosm',
      version='0.3.0',
      description='GIS conflation tool for matching street networks.',
      long_description='GIS conflation tool: matches segments in one path network (e.g. streets and trails) to corresponding segments in another, based on geography and network connectivity.  Useful, among other things, for combining jurisdictional centerline data with Open Street Maps data.',
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: GIS'
      ], 
      keywords='GIS conflation OSM OpenStreetMaps centerline jurisdictional street network matcher',
      url='http://spiderosm.org',
      author='Michael Arnold',
      author_email='mha@spiderosm.com',
      license='MIT',
      packages=['spiderosm'],
      install_requires=[
          'pyproj',
          'shapely', #requires geos library, on Mac: "%brew install geos"  
          'pylev',
          'geojson >= 1.0.9',
          'pyshp' 
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
