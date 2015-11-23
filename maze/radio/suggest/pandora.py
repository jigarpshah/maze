import os
import codecs
import urllib
import time
import base64
import xmlrpclib
import sys
from Crypto.Cipher import Blowfish

#
# Developer Specific Properties (Please Fill In)
#
REQUEST_KEY='PANDORAHACKATHON'
SYNC_TIME_KEY='PANDORAHACKATHON'
PARTNER_USERNAME='hackathon'
PARTNER_PASSWORD='hackathon-fall-2015'
DEVICE_MODEL='fall2015'
#PANDORA_USERNAME='hackathon@pandora.com'
#PANDORA_PASSWORD='Hack2015!'
PANDORA_USERNAME='gzavitz+1@pandora.com'
PANDORA_PASSWORD='betabeta'

def nullPad(s):
    """Pad the input string with nulls so it is an even multiple of the
    blowfish cipher block size"""
    padding = chr(0) * (Blowfish.block_size - (len(s) % Blowfish.block_size))
    if padding:
        return s + padding
    else:
        return s

def encodeHex(s):
    """Return hex encoded string for binary string s"""
    encoder = codecs.getencoder('hex_codec')
    hex, length = encoder(s)
    assert len(s) == length, "Hex encoding incomplete"
    return hex

def decodeHex(hex):
    """Return binary string for hex encoded string"""
    decoder = codecs.getdecoder('hex_codec')
    decoded, length = decoder(hex)
    assert len(hex) == length, "Hex decoding incomplete"
    return decoded

def stripPadding(s):
    """Remove trailing padding bytes from s

    The expected padding is byte values equal to the number of padding bytes.
    This function will also work will null padding as well
    """
    if s and ord(s[-1]) <= Blowfish.block_size:
        return s.rstrip(s[-1])
    else:
        return s

class PandoraServer(xmlrpclib.ServerProxy):
    """Proxy for the Pandora Public api.
    Use as a drop-in replacement for the standard xmlrpclib.ServerProxy class.
    """

    _sync = None
    _requestCipher = None
    _partnerId = None
    _userId = None
    _authToken = None

    def encodeRequest(self, request_data):
        """Helper function to encrypt and encode request data. Returns hex encoded
        encrypted data.
        """
        return encodeHex(self._requestCipher.encrypt(nullPad(request_data)))

    def __init__(self, uri, x509=None, Transport=None):
        """
        x509 param allows you to specify the values for the httplib.HTTPS x509 parameters.
        an example usage could be: {"key_file" : <keyfilePath>, "cert_file" : <certfilePath>}
        """
        xmlrpclib.ServerProxy.__init__(self, uri, transport=Transport)
        self.x509 = x509

    def _ServerProxy__request(self, methodname, params):
        """call a method on the remote server

        Holy name mangling Batman!
        """

        paddedHandler = self._ServerProxy__handler

        # add on the methodName
        sep = '&'
        if '?' not in paddedHandler:
            sep = '?'
        paddedHandler = paddedHandler + "%smethod=%s" % (sep, methodname)
        sep = '&'

        # add on the auth token
        if self._authToken:
            paddedHandler = paddedHandler + "%sauth_token=%s" % (sep, urllib.quote_plus(self._authToken))

        # add on the partnerId
        if self._partnerId:
            paddedHandler = paddedHandler + "%spartner_id=%s" % (sep, self._partnerId)

        # add on the userId
        if self._userId:
            paddedHandler = paddedHandler + "%suser_id=%s" % (sep, self._userId)

        EXCLUDED_PAYLOAD_CALLS = ([
            "auth.partnerLogin",
            "test.",
            "debug.",
            "testability."
        ])
        encryptRequest = True
        if self._requestCipher:
            for excludedMethodPattern in EXCLUDED_PAYLOAD_CALLS:
                if methodname.startswith(excludedMethodPattern):
                    encryptRequest = False
                    break
        else:
            encryptRequest = False

        # add the syncTime request
        if encryptRequest and self._sync:
            server_value, sync_time = self._sync
            params[0]['syncTime'] = server_value + int(time.time()) - sync_time

        request = xmlrpclib.dumps(params, methodname,
            encoding=self._ServerProxy__encoding,
            allow_none=self._ServerProxy__allow_none)

        #print "------- XML REQUEST --------"
        #print request

        if encryptRequest:
            request = self.encodeRequest(request)

        if self.x509:
            response = self._ServerProxy__transport.request(
                (self._ServerProxy__host, self.x509),
                paddedHandler,
                request,
                verbose=self._ServerProxy__verbose
                )
        else:
            response = self._ServerProxy__transport.request(
                self._ServerProxy__host,
                paddedHandler,
                request,
                verbose=self._ServerProxy__verbose
                )

        if len(response) == 1:
            response = response[0]

        #print "------ RESPONSE ------"
        #print response

        return response

def pandora_api(username, password):
    secureServer = PandoraServer('https://device-tuner-beta.savagebeast.com/services/xmlrpc/')
    server = PandoraServer('http://device-tuner-beta.savagebeast.com/services/xmlrpc/')

    #print "\n==> Checking IP-based licensing\n"
    licensingResult = server.test.checkLicensing({
        })['result']
    if not licensingResult['isAllowed']:
        print "Client not licensed to use Pandora"
        sys.exit(1)

    # partner login
    print "\n==> Logging in the partner: %s \n" % (PARTNER_USERNAME)
    partnerResult = secureServer.auth.partnerLogin({
        'username': PARTNER_USERNAME,
        'password': PARTNER_PASSWORD,
        'deviceModel': DEVICE_MODEL,
        'version': '4'
        })['result']

    secureServer._partnerId = partnerResult['partnerId']
    server._partnerId = partnerResult['partnerId']
    secureServer._authToken = partnerResult['partnerAuthToken']
    server._authToken = partnerResult['partnerAuthToken']

    # decode the syncTime (using the syncTimeKey provided by Pandora)
    syncCipher = Blowfish.new(SYNC_TIME_KEY, Blowfish.MODE_ECB)
    syncTimeHexValue = partnerResult['syncTime']
    # decode hex to bytes
    syncTimeBytes = decodeHex(syncTimeHexValue)
    # decrypt the bytes
    decryptedSyncTime = syncCipher.decrypt(syncTimeBytes)
    # throw away the first 4 bytes (these are random "salt" bytes added on by the Pandora server)
    decryptedSyncTime = decryptedSyncTime[4:]
    # remove the padding
    # the padding is filled with non-ascii values, set to the length of the padding
    syncTime = int(stripPadding(decryptedSyncTime))

    # save off the sync time for the xmlrpc handlers
    sync = (syncTime, int(time.time()))
    server._sync = sync
    secureServer._sync = sync

    # set the cipher to encrypt the request (using the requestKey provided by Pandora)
    encryptCipher = Blowfish.new(REQUEST_KEY, Blowfish.MODE_ECB)
    secureServer._requestCipher = encryptCipher
    server._requestCipher = encryptCipher

    # user login
    print "\n==> Logging in the user: %s " % (PANDORA_USERNAME)
    userResult = secureServer.auth.userLogin({
        'partnerAuthToken': partnerResult['partnerAuthToken'],
        'username': PANDORA_USERNAME,
        'password': PANDORA_PASSWORD,
        'loginType': 'user'
        })['result']

    # save off the userId and userAuthToken
    userAuthToken = userResult['userAuthToken']
    secureServer._userId = userResult['userId']
    server._userId = userResult['userId']
    secureServer._authToken = userAuthToken
    server._authToken = userAuthToken

    return PandoraAPI(secureServer, server, userAuthToken)

class PandoraAPI(object):
    def __init__(self, secureServer, server, userAuthToken):
        self.secureServer = secureServer
        self.server = server
        self.userAuthToken = userAuthToken

    def get_station_list(self):
        return self.server.user.getStationList({
            "userAuthToken": self.userAuthToken
        })['result']

    def get_playlist(self, stationToken):
        return self.secureServer.station.getPlaylist({
            'userAuthToken': self.userAuthToken,
            'stationToken': stationToken,
            })['result']

    def create_station(self, musicToken=None, trackToken=None):
        data = {
            'userAuthToken': self.userAuthToken,
            'musicType': 'song',
        }
        if musicToken:
            data['musicToken'] = musicToken
        elif trackToken:
            data['trackToken'] = trackToken
        else:
            raise Exception("A music or track token is needed")
        return self.secureServer.station.createStation(data)['result']

    def get_station(self, stationToken):
        return self.secureServer.station.getStation({
            'userAuthToken': self.userAuthToken,
            'stationToken': stationToken,
            'includeExtendedAttributes': True,
            })['result']

    def add_seed(self, stationToken, trackToken):
        return self.secureServer.station.addMusic({
            'userAuthToken': self.userAuthToken,
            'stationToken': stationToken,
            'musicToken': trackToken,
        })

    def remove_seed(self, seedId):
        return self.secureServer.station.deleteMusic({
            'userAuthToken': self.userAuthToken,
            'seedId': seedId,
        })

    def rename_station(self, stationToken, stationName):
        return self.secureServer.station.renameStation({
            'userAuthToken': self.userAuthToken,
            'stationToken': stationToken,
            'stationName': stationName,
            })['result']

    def delete_station(self, stationToken):
        return self.secureServer.station.deleteStation({
            'userAuthToken': self.userAuthToken,
            'stationToken': stationToken,
            })

    def search(self, text):
        return self.secureServer.music.search({
            'userAuthToken': self.userAuthToken,
            'searchText': text
            })['result']

__pandora_api__ = None
def api():
    global __pandora_api__
    if not __pandora_api__:
        __pandora_api__ = pandora_api(PANDORA_USERNAME, PANDORA_PASSWORD)
    return __pandora_api__

if __name__ == '__main__':
    # get station list
    print "\n==> Getting a list of stations %s \n" % (PANDORA_USERNAME)

    for station in api().get_station_list().get('stations', []):
        if "French" in station['stationName']:
            break
    else:
        print "Couldn't find any french stations"
        sys.exit(13)

    # retrieve a playlist
    print "\n==> Retrieving a playlist for %s \n" % station['stationName']
    playlistResult = api().get_playlist(station['stationToken'])

    print '\n'
    for item in playlistResult['items']:
        if item.has_key('trackToken'):
            print 'Track: "%s" by "%s"' % (item['songName'], item['artistName'])
            print item
            print api().add_seed(station['stationToken'], item['musicId'])

        if item.has_key('adToken'):
            print 'Ad: %s' % (item['adToken'])
    print '\n'


    sys.exit(0)
