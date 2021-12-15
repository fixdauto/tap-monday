#!/usr/bin/python

import os

api_key = os.getenv('MONDAY_API_KEY')

if api_key == None:
  print('Please set MONDAY_API_KEY')
else:
  print(api_key)
