import json

with open("venues.json","r") as f:
    data = json.load(f)
no_coordinates = 0
for key, item in data.items():
    if 'latitude' not in item:
        print(item["name"], key)
        coord_string = input("paste in coordinates from Google")
        latitude, longitude = coord_string.split(",")
        item["latitude"] = float(latitude)
        item["longitude"] = float(longitude)
        with open("venues.json","w") as f:
            json.dump(data, f, indent=2)
