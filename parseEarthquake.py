#!/usr/bin/env python

import urllib3
import json
import datetime
from datetime import date
import sqlite3


class USGSFeed:

    _feedDuration = ('hour', 'day', 'week', 'month')

    _feedSize = ('significant', '4.5', '2.5', '1.0', 'all')

    _feedUrl = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{}_{}.geojson'

    def get(self, duration, size='all'):
        if (duration in self._feedDuration) & (size in self._feedSize):
            return self._feedUrl.format(size, duration)
        else:
            raise LookupError



class Earthquake:
    def __init__(self, item):
        self._vars = {
            'id':item['id'],
            'geometry': item['geometry'],
            'properties': item['properties'],
            'raw': item,
        }

    def get_properties(self):
        return self._vars['properties']

    def get_property(self, name):
        try:
            return self._vars['properties'][name]
        except BaseException:
            print("Key", name, "does not exist.")

    def get_attribute(self, name):
        return self._vars[name]

    def get_geometry(self):
        return self._vars['geometry']

    def get_raw(self):
        return self._vars['raw']



def main():
    http = urllib3.PoolManager()
    usgs = USGSFeed()
    feed = usgs.get('day', 'all');
    response = http.request('GET', feed)

    if response.status == 200:
        db = sqlite3.connect('earthquakes.db')
        cursor = db.cursor()
        cursor.execute(''' DROP TABLE earthquakes ''')
        cursor.execute('''
            CREATE TABLE earthquakes(id INTEGER PRIMARY KEY, earthquake_id TEXT UNIQUE, title TEXT,
            magnitude REAL, type TEXT, url TEXT, data TEXT, created_at INTEGER)''')

        earthquakes = []
        database_insert = []
        decoded_json_data = json.loads(response.data.decode('utf-8'))


        #set up the metadata table
        cursor.execute(''' DROP TABLE metadata ''')
        cursor.execute('''
            CREATE TABLE metadata(id INTEGER PRIMARY KEY, generated TEXT UNIQUE, created_at INTEGER)''')
        metadata = json.dumps(decoded_json_data['metadata']['generated'])

        cursor.execute(''' INSERT INTO metadata(generated, created_at) values (?,?)''', (metadata,datetime.datetime.utcnow()))
        # print(decoded_json_data)
        ''' look at the rest of the data feed.
        I would need to store that.
        How do I convert the Dict back to a string so it can be inserted into the database
        '''

        for key, earthquakes_data in decoded_json_data.items():
            if key == 'features':
                for earthquake_data in earthquakes_data:

                    earthquake = Earthquake(earthquake_data)
                    earthquakes.append(earthquake)
                    raw_data = json.dumps(earthquake.get_raw())
                    #print(raw_data)

                    new_row = (earthquake.get_attribute('id'), 
                        earthquake.get_property('title'), 
                        earthquake.get_property('mag'),
                        earthquake.get_property('type'),
                        earthquake.get_property('url'),
                        raw_data,
                        datetime.datetime.utcnow(),
                    )

                    database_insert.append(new_row)

        print("Adding to database")
        cursor.executemany(''' INSERT INTO earthquakes(
            earthquake_id, title, magnitude, type, url, data, created_at)
        values(?,?,?,?,?,?,?)''', database_insert)
        db.commit()
    else:
        print("Error: Request to", hourlyUSGSFeed, " Status:", response.status)


if __name__ == "__main__" : main()

