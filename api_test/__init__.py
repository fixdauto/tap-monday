import requests
import json
import os
import sys

def run():
  api_key = os.getenv('MONDAY_API_KEY')

  if api_key == None:
    sys.exit('Please set MONDAY_API_KEY')

  api_url = "https://api.monday.com/v2"
  headers = {"Authorization" : api_key}

  # board id - from config
  # group ids - all for full import or latest for incremental

  data = {'query':"""
    {
      boards(ids: 1554079540) {
        groups(ids: new_group8875) {
          title
          position
          id
          items(limit: 5) {
            name
            created_at
            column_values() {
              title
              text
            }
          }
        }
      }
    }
  """}

  r = requests.post(url=api_url, json=data, headers=headers)
  resp = r.json()

  if "errors" in resp:
    exit(f'Error: {resp["errors"][0]}')

  items = resp["data"]["boards"][0]["groups"][0]["items"]
  for i, item in enumerate(items): 
    print(f'#{i} - {item["name"]}')

    column_keys = [ # columns - from config
      "Product", 
      "Platform",
      "Type",
      "Owner",
      "Engineer",
      "Link",
      "Carry-Over Counter",
      "Unplanned",
      "Date Added"
    ]
    selected_columns = [ c for c in item["column_values"] if c["title"] in column_keys ]

    [ print(f'\t{c["title"]}: {c["text"]}') for c in selected_columns ]
