#!/usr/bin/env python

import urllib3, json


class Earthquake:
    def __init__(self, item):
        self.id = item['id']
        self.properties = item['properties']
        self.geomatry = item['geometry']
        self.type = item['type']



def main():
    http = urllib3.PoolManager()
    hourlyUSGSFeed = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson'
    response = http.request('GET', hourlyUSGSFeed)

    if (response.status == 200):
        decodedJsonData = json.loads(response.data.decode('utf-8'))
        for key, earthquakes in decodedJsonData.items():
            if key == 'features':
                for earthquakeData in earthquakes:
                    earthquake = Earthquake(earthquakeData)
                    print(earthquake.id, earthquake.properties.keys(), earthquake.geomatry)


    else:
        print("Error: Request to", hourlyUSGSFeed, " Status:", response.status)


if __name__ == "__main__" : main()

