from rdioapi import Rdio

__rdio__ = None
__rdio_state__ = {'device_code': u'LC6KLA',
    'access_token_expires': 1448002236.732884,
    'access_token': u'AAAAAWEAAAAAAAqp1AAAAIBWThn8Vk7CvAAAABp1NGxlbm5sbmRqaHZmbml0Zm50bjNtY3Z6aRBO6AZJ-kM71bNxfVJ1MoP3awKgYg2Zyu9zFn5uov57',
    'token_type': u'bearer',
    'device_expires': 1447960824.323112,
    'refresh_token': u'AAAAAXIAAAAAAAqp1AAAAIBWThn8e-Yf_AAAABp1NGxlbm5sbmRqaHZmbml0Zm50bjNtY3Z6aW0wg5HXkwlThTodQd-Hr10lyUK1hOTfhH_HPdDXg4jO'}
def api():
    global __rdio__, __rdio_state__
    if not __rdio__:
        __rdio__ = Rdio("u4lennlndjhvfnitfntn3mcvzi", "YO2oHvLK5rOCQTnFJvNq-Q", __rdio_state__)
        if not __rdio_state__.get('device_code'):
            url, device_code = __rdio__.begin_authentication()
            raw_input('After entering the device code "{}" into {} press enter'.format(device_code, url))
            __rdio__.complete_authentication()
            print __rdio_state__
    return __rdio__

if __name__ == "__main__":
    print api().search(query='Bohemian Rhapsody', types='Track')