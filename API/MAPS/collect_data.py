import requests
import pandas as pd
import time

print ("Pulling crash data from NYC Open Data...")
url = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"
params = {
    "$limit": 50000,
    "$offset":0,
    "$select": "crash_date, crash_time, latitude, longitude, number_of_persons_injured, number_of_persons_killed",
    "$where": "latitude IS NOT NULL AND longitude IS NOT NULL"
}

response = requests.get(url, params=params, timeout=30)
data = response.json()
df = pd.DataFrame(data)
df.to_csv("crashes.csv", index=False)
print(f"Done - saved {len(df)} records to crashes.csv")
print (df.head())