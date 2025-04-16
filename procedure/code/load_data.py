import requests
import time
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


RESOURCE_ID = "595b402d-4192-401c-b740-5cb7e4ceab10"
SQL_URL = "http://data.ctdata.org/api/3/action/datastore_search_sql"

def fetch_total_count():
    query = f'SELECT COUNT(*) FROM "{RESOURCE_ID}"'
    response = requests.get(SQL_URL, params={"sql": query})
    response.raise_for_status()
    return int(response.json()['result']['records'][0]['count'])

def fetch_batch(offset, limit):
    query = f'SELECT * FROM "{RESOURCE_ID}" OFFSET {offset} LIMIT {limit}'
    session = requests.Session()
    retries = Retry(
        total=5,             # total retries
        backoff_factor=1,    # wait 1s, then 2s, then 4s, etc.
        status_forcelist=[500, 502, 503, 504],
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    response = session.get(SQL_URL, params={"sql": query}, timeout=60)
    response.raise_for_status()
    return response.json()['result']['records']

def main():
    print("Fetching total record count...")
    total = fetch_total_count()
    print(f"Total records: {total}")

    all_records = []
    limit = 50
    for offset in range(0, total, limit):
        print(f"Fetching rows {offset} to {offset + limit}...")
        try:
            batch = fetch_batch(offset, limit)
            if not batch:
                print("Empty batch, stopping.")
                break
            all_records.extend(batch)
            time.sleep(0.5)  # polite pause
        except Exception as e:
            print(f"Failed at offset {offset}: {e}")
            break

    if all_records:
        print(f"Saving {len(all_records)} records to CSV...")
        df = pd.DataFrame(all_records)
        df.to_csv("/Users/dermotmcmillan/Desktop/GitHub/RPr-CT-crime/data/raw/public/ct_crime_data.csv", index=False)
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()
