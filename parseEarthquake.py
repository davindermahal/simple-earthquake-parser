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

        ###
        # New Tables
        ###

        # cursor.execute(''' DROP TABLE earthquakes ''')
        # cursor.execute('''
        #     CREATE TABLE earthquakes(
        #     id INTEGER PRIMARY KEY,
        #     earthquake_id TEXT UNIQUE,
        #     title TEXT,
        #     magnitude REAL,
        #     source TEXT,
        #     url TEXT,
        #     data TEXT,
        #     feed_generated_time TEXT,
        #     created_at INTEGER)
        # ''')
        #
        # cursor.execute(''' DROP TABLE metadata ''')
        # cursor.execute('''
        #     CREATE TABLE metadata(
        #     id INTEGER PRIMARY KEY,
        #     generated TEXT UNIQUE,
        #     created_at INTEGER)
        #     ''')

        decoded_json_data = json.loads(response.data.decode('utf-8'))
        generated_at = json.dumps(decoded_json_data['metadata']['generated'])

        # Compare metadata generated with the value in the database
        cursor = db.execute(''' SELECT * FROM metadata ORDER BY id ASC''')

        row = cursor.fetchone()
        if row[1] == generated_at:
            print("Feed generation time is the same")
        else:
            print("Last recorded feed generated:", row[1])
            print("Feed generated:", generated_at)

            cursor = db.cursor()
            cursor.execute(''' INSERT INTO metadata(generated, created_at) values (?,?)''', (generated_at, datetime.datetime.utcnow()))

            earthquakes = []
            database_insert = {}
            earthquake_ids = []

            print("Parsing earthquake feed")

            for key, earthquakes_data in decoded_json_data.items():
                if key == 'features':
                    # features contain the individual earthquakes
                    for earthquake_data in earthquakes_data:

                        earthquake = Earthquake(earthquake_data)
                        earthquakes.append(earthquake)

                        earthquake_ids.append(earthquake.get_attribute('id'))

                        new_row = (earthquake.get_attribute('id'),
                                   earthquake.get_property('title'),
                                   earthquake.get_property('mag'),
                                   earthquake.get_property('type'),
                                   earthquake.get_property('url'),
                                   json.dumps(earthquake.get_raw()),
                                   generated_at,
                                   datetime.datetime.utcnow(),
                                   )
                        database_insert[earthquake.get_attribute('id')] = new_row

            print(len(database_insert), "earthquakes recorded in the feed")
            print("Checking earthquakes in the database")

            parameters = ",".join(("?")*len(earthquake_ids))

            sql_query = "SELECT id, earthquake_id from earthquakes WHERE earthquake_id IN ({})".format(parameters)
            cursor = db.execute(sql_query, earthquake_ids)
            number_of_earthquakes_removed = 0;
            for row in cursor:
                del database_insert[row[1]]
                number_of_earthquakes_removed += 1

            print(number_of_earthquakes_removed, "were removed from the database insert list")
            print(len(database_insert), "earthquakes to be added to the database")

            if len(database_insert) > 0:
                cursor.executemany(''' INSERT INTO earthquakes(
                    earthquake_id, title, magnitude, source, url, data, feed_generated_time, created_at)
                values(?,?,?,?,?,?,?,?)''', database_insert.values())
                db.commit()

            db.close()

    else:
        print("Error: Request failed. Status:", response.status)


if __name__ == "__main__" : main()

