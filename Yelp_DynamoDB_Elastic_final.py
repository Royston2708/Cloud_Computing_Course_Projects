import json
import boto3
import requests
from decimal import Decimal
import pandas as pd
from time import sleep
import datetime
import collections
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode



# Using the Yelp API along with our yelp API key
API_KEY= '************************************************************************************************************' # Removing API Key details.  


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

access_key = "*******************"
secret_key = "*********************************"

dynamodb = boto3.resource('dynamodb', region_name='us-west-2', aws_access_key_id=access_key,  aws_secret_access_key = secret_key)
table = dynamodb.Table('yelp-restaurants')

client = boto3.client('dynamodb', region_name='us-west-2', aws_access_key_id=access_key,  aws_secret_access_key = secret_key)
list_float=['rating', 'latitude', 'longitude', 'distance']

from decimal import Decimal
def convert_floats(item,list_float=list_float):
    for var in item:
        if var in list_float:
            item[var]=Decimal(str(item[var]))
    return item

# Creating the final list of dictionaries for the DynamoDB
cols = ['categories', 'id', 'name', 'address1', 'latitude', 'longitude', 'review_count', 'rating', 'zip_code']
final_list = []
cuisines = ['mediterranean', 'italian', 'indian', 'chinese', 'mexican', 'french', 'newamerican,tradamerican']
#cuisines_test = ['italian', 'indian', 'chinese', 'mexican' 'tradamerican']
for s in cuisines:
  # add a pause
  sleep(0.5)
  for o in range(0, 1000, 50):
    url_params = {
      'term': 'restaurants',
      'location': 'New York City',
      'categories': s,
      'offset': o,
      'limit': 50
    }
    print("Running for cuisine {} at offset {}".format(s,o))
    response = request(API_HOST, SEARCH_PATH, API_KEY, url_params=url_params).json().get("businesses")
    sleep(0.5)
    for x in response:
      data = flatten(x)
      data = convert_floats(data)
      data2 = { your_key: data[your_key] for your_key in cols }
      if s == 'newamerican,tradamerican':
        data2['categories'] = 'american'
      else:
        data2['categories'] = s
      data2['Timestamp'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
      final_list.append(data2)

# Inserting the final dictionaries into the DynamoDB table
i = 0
table = dynamodb.Table('yelp-restaurants')
for entry in final_list:
  response = table.put_item(Item = entry)
  i+=1
  if i %500 ==0:
    print(i)
    sleep(0.1)
  if ("UnprocessedItems" in response):
    print(response["UnprocessedItems"])
    break



# Forming the elaticsearch dictionary to upload to our Domain
es_list = []
for entry in final_list:
  r_name = entry.get("name")
  r_id = entry.get("id")
  r_cuisine = entry.get("categories")
  es_dict = {"cuisine":r_cuisine, "id":r_id}
  es_list.append(es_dict)


# Inserting into ElasticSearch DB
# Using Royston Credentials as he is the Master User
access_key = "************************"
secret_key = "*************************************"

host = "search-test-es-55h2alnoth4r7l4hkldymkn7m4.us-west-2.es.amazonaws.com"
region = 'us-west-2'
service = "es"
#credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(access_key, secret_key, region, service)

es = Elasticsearch(hosts = [{'host': host, 'port': 443}],
                   http_auth = awsauth, use_ssl = True,
                   verify_certs = True, connection_class = RequestsHttpConnection
                   )

for restaurant in es_list:
  response = es.index(index = "restaurants", body = restaurant)

# ElasticSearch Index populated.
# Now Querying the index for restaurant ID.

import random

res = es.search(index="restaurants", body={"query": {"match": {"cuisine": "american"}}})
candidates = []
for entry in res['hits']['hits']:
  candidates.append(entry["_source"])

ids = []
for i in candidates:
  ids.append(i.get("id"))

restaurant_suggestion = random.choice(ids)
