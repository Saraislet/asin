import os, datetime, urllib
import hashlib, hmac, base64
import requests
import xmltodict

# Test Amazon MWS API at https://mws.amazonservices.com/scratchpad/index.html
# See Amazon MWS Documentation at https://docs.developer.amazonservices.com/en_US/dev_guide/DG_IfNew.html


# ************* REQUEST VALUES *************
method = 'POST'
service = 'mws'
host = 'mws.amazonservices.com'
region = 'us-east-1'
endpoint = 'https://mws.amazonservices.com'
content_type = 'text/xml'
path = '/Products/2011-10-01'

# Time string format (must be in UTC): 2017-11-19T20:47:19Z
t = datetime.datetime.utcnow()
amz_date = t.strftime('%Y-%m-%dT%H:%M:%SZ')
amz_date_encoded = t.strftime('%Y-%m-%dT%H%%3A%M%%3A%SZ')

url = endpoint + path
access_key = os.environ['AWSAccessKeyId']
secret_key = os.environ['SecretKey']
secret = bytes(secret_key, 'utf-8')


def sign(key, msg):
    hash = hmac.new(key, msg, hashlib.sha256)
    return base64.b64encode(hash.digest())


def get_marketplace_id(domain):
    # Return the appropriate MarketplaceId for the domain (default is *.com).
    return{
            'com': os.environ['MarketplaceId_com'],
            'ca': os.environ['MarketplaceId_ca'],
            'com.mx': os.environ['MarketplaceId_com_mx']
            }.get(domain, os.environ['MarketplaceId_com'])


def parse_response(xml):
    # Given xml response, return dictionary of needed values.
    response = xmltodict.parse(xml.text)
    return response


def lookup_asin(asin, domain):
    # Look up app details from Amazon MWS, return dictionary with details.
    
    # Use the appropriate MarketplaceID for the domain.
    MarketplaceId = get_marketplace_id(domain)
    
    # Construct request parameters:
    payload = {'AWSAccessKeyId': os.environ['AWSAccessKeyId'], 
               'Action': 'GetMatchingProduct', 
               'SellerId': os.environ['SellerId'], 
               'MWSAuthToken': os.environ['MWSAuthToken'], 
               'SignatureVersion': '2', 
               'Timestamp': amz_date, 
               'Version': '2011-10-01', 
               'SignatureMethod': 'HmacSHA256', 
               'MarketplaceId': MarketplaceId,
               'ASINList.ASIN.1': asin}

    request_parameters = 'ASINList.ASIN.1=' + payload['ASINList.ASIN.1']
    request_parameters += '&AWSAccessKeyId=' + payload['AWSAccessKeyId']
    request_parameters += '&Action=' + payload['Action']
    request_parameters += '&MWSAuthToken=' + payload['MWSAuthToken']
    request_parameters += '&MarketplaceId=' + payload['MarketplaceId']
    request_parameters += '&SellerId=' + payload['SellerId']
    request_parameters += '&SignatureMethod=' + payload['SignatureMethod']
    request_parameters += '&SignatureVersion=' + payload['SignatureVersion']
    request_parameters += '&Timestamp=' + urllib.parse.quote(payload['Timestamp'])
    request_parameters += '&Version=' + payload['Version']
        

    # Construct message to sign, usign request parameters:
    msg = method + '\n'
    msg += host + '\n'
    msg += path + '\n'
    msg += request_parameters
    
    # Sign the message
    print('Message to sign: ' + msg)
    signature = sign(secret, bytes(msg, 'utf-8'))
    print('Signature: ' + str(signature))
    
    payload['Signature'] = signature
    r = requests.post(url, params=payload)
    
    print(r.text)
    
    response = parse_response(r)
    app_info = {}
    
    if 'ErrorResponse' in response:
        error_message = response['ErrorResponse']['Error']['Message']
        error_message += '\n\n' + 'Query string:\n' + msg
        raise OSError('Error retrieving data from Amazon App Store: ' + error_message)
        return
    elif 'GetMatchingProductResponse' in response:
        app_info['app_name'] = response['GetMatchingProductResponse']['GetMatchingProductResult']['Product']['AttributeSets']['ns2:ItemAttributes']['ns2:Label']
        app_info['release_date'] = response['GetMatchingProductResponse']['GetMatchingProductResult']['Product']['AttributeSets']['ns2:ItemAttributes']['ns2:ReleaseDate']
        app_info['change_notes'] = '' 
        return app_info
    else:
        raise OSError('Error retrieving data from Amazon App Store: ' + str(response))
        return