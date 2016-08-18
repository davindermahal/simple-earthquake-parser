#!/usr/bin/env python

import urllib3, json


class Earthquake:
    def __init__(self, item):
        self.id = item['id']
        self.properties = item['properties']
        self.geometry = item['geometry']
        self.type = item['type']
        self.title = self.properties['title']
        self.magnitude = self.properties['mag']
        self.time = self.properties['time']



def main():
    http = urllib3.PoolManager()
    hourlyUSGSFeed = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson'
    response = http.request('GET', hourlyUSGSFeed)

    if (response.status == 200):
        earthquakes = []

        decodedJsonData = json.loads(response.data.decode('utf-8'))
        for key, earthquakesData in decodedJsonData.items():
            if key == 'features':
                for earthquakeData in earthquakesData:
                    earthquake = Earthquake(earthquakeData)
                    earthquakes.append(earthquake)
                    #print(earthquake.properties)
        print(earthquakes)

    else:
        print("Error: Request to", hourlyUSGSFeed, " Status:", response.status)


if __name__ == "__main__" : main()

