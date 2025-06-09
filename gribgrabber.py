import numpy as np
import pygrib

LAT = 38.6374
LON = -90.2375

grib_messages = pygrib.open('gribs/nam.t00z.conusnest.hiresf06.tm00.grib2')

print("Selecting conditions from dataset...")
conditions = {
    "visibility": grib_messages.select(shortName='vis', typeOfLevel='surface')[0],
    "gust": grib_messages.select(shortName='gust', typeOfLevel='surface')[0],
    "relative_humidity_hybrid": grib_messages.select(shortName='r', typeOfLevel='hybrid', level=1)[0]
}
print("Done!")


def find_nearest_point(lat_in, lon_in):
    step = .015
    lat, lon = np.array([]), np.array([])
    # Gradually increase bounding box until a point is found
    while not lat.any():
        value, lat, lon = grib_messages.message(1).data(lat1=lat_in - step, lat2=lat_in + step, lon1=lon_in - step, lon2=lon_in + step)  # 6x6 km search box
        step += .01
    min_distance = -1
    min_distance_idx = 0
    for i in range(len(lat)):
        distance = (lat_in - lat[i])**2 + (lon_in - lon[i])**2
        if min_distance == -1 or distance < min_distance:
            min_distance = distance
            min_distance_idx = i
    return lat[min_distance_idx], lon[min_distance_idx]


station_lat, station_lon = find_nearest_point(LAT, LON)


# for msg in grib_messages:
#     value, lat, lon = msg.data(lat1=station_lat, lat2=station_lat, lon1=station_lon, lon2=station_lon)
#     lat = lat[0]
#     lon = lon[0]
#     value = value[0]
#     print(f"[{msg.shortName}] {msg.name} at {msg.level} {msg.typeOfLevel} @ {lat}, {lon}: {value}")


for data_name, grb in conditions.items():
    value, lat, lon = grb.data(lat1=station_lat, lat2=station_lat, lon1=station_lon, lon2=station_lon)
    lat = lat[0]
    lon = lon[0]
    value = value[0]
    print(f"[{data_name}] {grb.name} at {grb.level} {grb.typeOfLevel} @ {lat}, {lon}: {value}")
