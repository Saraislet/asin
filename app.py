import re
from flask import Flask, request, render_template
import lookup

app = Flask(__name__)


@app.route('/')
def main():
    return render_template("app.html")


@app.route('/search', methods=['POST'])
def search():
    # Look up the app entered with Amazon MWS API, and return details.
    
    # Retrieve string entered in "Amazon App Store URL" input.
    url = request.form['url']
    print("Searching for app at " + url)
    
    try:
        # Identify the domain of the URL to use the appropriate MarketplaceId.
        domain = get_domain_from_url(url)
        
        # Identify the ASIN from an Amazon URL.
        asin = get_asin_from_url(url)
        
        # Lookup ASIN in Amazon MWS.
        print("Searching Amazon MWS for ASIN \'" + asin + "\'.")
        app_info = lookup.lookup_asin(asin, domain)
        app_name = app_info['app_name']
        release_date = app_info['release_date']
        change_notes = app_info['change_notes']
        
        show_result = True
        return render_template('app.html', **locals())
    
    except ValueError as e:
        show_error = True
        error_msg = "Could not identify app from URL."
        error_msg += " Please enter an Amazon app store URL from amazon.com, amazon.ca, or amazon.com.mx."
        return render_template('app.html', **locals())
    
    except BaseException as e:
        show_error = True
        error_msg = e
        print("Error in lookup():", e)   
        return render_template('app.html', **locals())


def get_asin_from_url(string):
    # Match ASIN from Amazon URL and return ASIN string.
    # string should look like http://www.amazon.com/Facebook/dp/B0094BB4TW
    try: 
        asin = re.sub(r'https?://www\.amazon\.[^/]{2,6}/[^/]*/[^/]*/([a-zA-Z0-9_]{10}).*', r'\1', string)
        return asin

    except BaseException as e:
        print("Error in get_asin_from_url():", e)
        raise ValueError("Cannot find ASIN in URL.")
        return


def get_domain_from_url(string):
    # Match domain from Amazon URL and return URL string COM/CA/MX.
    # string should look like http://www.amazon.com/Facebook/dp/B0094BB4TW
    try: 
        domain = re.sub(r'https?://www\.amazon\.(com|ca|com\.mx)/.*', r'\1', string)
        return domain

    except BaseException as e:
        print("Error in get_domain_from_url():", e)
        raise ValueError("Cannot find domain in URL.")
        return


if __name__ == '__main__':
    app.run()