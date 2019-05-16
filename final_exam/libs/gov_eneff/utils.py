import requests
import time

class Geocoder():

    """
    Yandex Geocoder: https://tech.yandex.ru/maps/doc/geocoder/
    """

    def __init__(self, type='yandex'):

        self.geocoder_type = 'yandex'

    def by_address(self, address):

        r = requests.get('https://geocode-maps.yandex.ru/1.x',
                         params={'apikey': rt.config['yandex']['geocoder_key'],
                                 'geocode': address,
                                 'format': 'json'})
        time.sleep(.2)

        return (r.json())


def print_full(x):

    pd.set_option('display.max_rows', len(x))
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.2f}'.format)
    pd.set_option('display.max_colwidth', -1)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')