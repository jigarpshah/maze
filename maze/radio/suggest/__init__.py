from __future__ import unicode_literals
from datetime import datetime
from random import shuffle
from rdio import api as rdio_api
from pandora import api as pandora_api
from language import detect_language

class SeedsNotFound(BaseException):
    pass

def track_generator(languages, emotion, seeds, year_range, recreate=False):
    station = Pandora_Station.get_or_create(languages, emotion, seeds, recreate)
    for track in station.get_playlist():
        try:
            artist, song_name = track['artistName'], track['songName']
        except KeyError:
            continue
        detected_language = detect_language(song_name)
        if detected_language in languages:
            rdio_track = Rdio_Track.search(artist, song_name)
            if rdio_track is not None:
                release_year = rdio_track.get_release_date().year
                if release_year in year_range:
                    print u"Found {}".format(rdio_track)
                    yield rdio_track
                else:
                    print u"Release year {} outside range for {}".format(release_year, song_name)
            else:
                print u"No rdio version of {}".format(song_name)
        else:
            print u"Wrong language {} for {}".format(detected_language, song_name)
    if not recreate:
        for rdio_track in track_generator(languages, emotion, seeds, year_range, recreate=True):
            yield rdio_track

class Rdio_Track(object):

    def __init__(self, _data):
        self._data = _data

    @staticmethod
    def search(artist, song_name):
        response = rdio_api().search(query=song_name, types="Track")
        for result in response['results']:
            if result.get('artist') == artist and result.get('name') == song_name:
                return Rdio_Track(result)

    def get_release_date(self):
        key = self._data.get('albumKey')
        response = rdio_api().get(keys=key)
        for album_key, album_data in response.iteritems():
            if album_key == key:
                return datetime.strptime(album_data.get('releaseDate'), "%Y-%m-%d")

    def __unicode__(self):
        return u"{artist} - {song_name} ({key})".format(artist=self._data.get('artist'),
            song_name=self._data.get('name'), key=self._data.get('key'))

    def __str__(self):
        return self.__unicode__()

    def __getitem__(self, item):
        try:
            return self._data[item]
        except:
            return object.__getitem__(self, item)

class Pandora_Track(object):

    def __init__(self, _data):
        self._data = _data

    @staticmethod
    def search(artist, song_name, include=None):
        if include is None:
            include = [song_name, artist]
        response = pandora_api().search(' '.join(include))
        found_songs = response['songs']
        backup, backup_confidence = None, 0
        for result in found_songs:
            if result['songName'] == song_name and result['artistName'] == artist:
                    return Pandora_Track(result)
            else:
                confidence = result.get('score', 0)
                if confidence > backup_confidence:
                    backup = Pandora_Track(result)
                    backup_confidence = confidence
        if backup is None:
            include.pop()
            if len(include):
                return Pandora_Track.search(artist, song_name, include)
            else:
                print u"Failed to match {} - {}".format(artist, song_name)
                return None
        else:
            print u"Matched {} - {} to backup {} with confidence {}".format(
                artist, song_name, backup, backup_confidence)
            return backup

    @staticmethod
    def make_key(seed_track):
        return u"track_{}_{}".format(
            seed_track.get('artist', seed_track.get('artistName')),
            seed_track.get('song', seed_track.get('songName'))
        )

    def get_music_token(self):
        return self._data.get('musicToken')

__track_map_cache__ = {}
class Pandora_Track_Map(object):

    def __init__(self, seed_tracks):
        self.seed_tracks = seed_tracks
        self.fetched = {}
        self.key_map = {} # {make_key(pandora seed): make_key(local seed track)}
        self._fetch_all_tracks()

    def _fetch_all_tracks(self):
        global __track_map_cache__
        tracks = []
        for track in self.seed_tracks:
            try:
                key = Pandora_Track.make_key(track)
                if key not in self.fetched:
                    if key in __track_map_cache__:
                        self.fetched[key] = __track_map_cache__[key]
                    else:
                        self.fetched[key] = Pandora_Track.search(track['artist'], track['song'])
                        __track_map_cache__[key] = self.fetched[key]
                if self.fetched.get(key) is not None:
                    pandora_key = Pandora_Track.make_key(self.fetched[key]._data)
                    self.key_map[pandora_key] = key
                    tracks.append(self.fetched[key])
            except UnicodeEncodeError:
                print "Failed encoding track, skipping..."
                print track
        return tracks

    def is_still_valid(self, active_seed):
        key = Pandora_Track.make_key(active_seed)
        if key in self.key_map:
            return True
        return False

    def __iter__(self):
        for key, track in self.fetched.iteritems():
            if track:
                yield track

    def get_one(self):
        for track in self.__iter__():
            return track

class Pandora_Station(object):

    def __init__(self, _data, _track_map):
        self._data = _data
        self._track_map = _track_map
        self._sync_seeds()

    @staticmethod
    def get_or_create(languages, emotion, seed_tracks, recreate=False):
        station_name = u"Maze_{}_{}".format(''.join(languages), emotion)
        pandora_station = None

        response = pandora_api().get_station_list()
        for station in response.get('stations', []):
            if station.get('stationName') == station_name:
                pandora_station = station
                break

        if recreate:
            pandora_api().delete_station(pandora_station.get('stationToken'))
            pandora_station = None

        track_map = Pandora_Track_Map(seed_tracks)
        if pandora_station is None:
            seed_track = track_map.get_one()
            if not seed_track:
                raise SeedsNotFound("This stations seeds could not be found on Pandora")
            pandora_station = pandora_api().create_station(musicToken=seed_track.get_music_token())
            pandora_api().rename_station(pandora_station.get('stationToken'), station_name)

        data = pandora_api().get_station(pandora_station.get('stationToken'))
        return Pandora_Station(data, track_map)

    def _sync_seeds(self):
        existing_seeds = []
        for current_seed in self._data['music'].get('songs', []):
            key = Pandora_Track.make_key(current_seed)
            if not self._track_map.is_still_valid(current_seed):
                print u"Removing seed: {}".format(key)
                pandora_api().remove_seed(current_seed['seedId'])
            else:
                existing_seeds.append(key)
        for new_seed in self._track_map:
            key = Pandora_Track.make_key(new_seed._data)
            if key not in existing_seeds:
                print u"Adding seed: {}".format(key)
                pandora_api().add_seed(self._data.get('stationToken'), new_seed._data['musicToken'])
            else:
                #print "Keeping seed: {}".format(key)
                continue

    def get_playlist(self):
        response = pandora_api().get_playlist(self._data.get('stationToken'))
        return response.get('items', [])

def test_en_love():
    sample_seeds = [
        {'artist': 'Queen', 'song': 'Bohemian Rhapsody'},
        {'artist': 'Queen', 'song': 'Another One Bites the Dust'},
        {'artist': 'Queen', 'song': 'Bicycle'},
    ]
    gen = track_generator('en', 'love', sample_seeds, xrange(1990, 2010))
    while True:
        track = gen.next()
        if not track:
            break
        print u"Loaded: {} (released {})".format(track, track.get_release_date())

def test_hi_romantic():
    sample_seeds = [
        {'artist': 'Shankar Mahadevan, Sunidhi Chauhan, Vishal Dadlani', 'song': 'Desi Girl'},
        {'artist': 'Sarwanand Thakur', 'song': 'Bhare Bhare Maare Pichkari Balam'},
        {'artist': 'Nakash Aziz & KM Sufi Ensemble', 'song': 'Afreen'},
        {'artist': 'Sunidhi Chauhan & Vishal Dadlani', 'song': 'Sheila Ki Jawani'},
        {'artist': 'Mamta Sharma, Aishwarya Nigam', 'song': 'Munni Badnaam Hui'},
        {'artist': 'Daler Mehndi, Richa Sharma', 'song': 'Zor Ka Jhatka'},
        {'artist': 'Akon, Hamsika Iyer', 'song': 'chammak challo'},
        {'artist': 'Mika Singh, Amrita Kak', 'song': 'dhinka chika'},
        {'artist': 'Aditi Singh Sharma', 'song': 'Dhoom Machale Dhoom'},
        {'artist': 'Shreya Ghoshal, Osman Mir', 'song': 'Nagada Sang Dhol'},
        {'artist': 'Sachin Jigar, Vishal Dadlani, Anushka Manchanda', 'song': 'Dance Basanti'},
        {'artist': 'Vishal & Shekhar, Benny Dayal, Neeti Mohan', 'song': 'Bang Bang'},
    ]
    gen = track_generator('hi', 'romantic', sample_seeds, xrange(1990, 1999))
    while True:
        track = gen.next()
        if not track:
            break
        print u"Loaded: {} (released {})".format(track, track.get_release_date())

if __name__ == "__main__":
    #test_en_love()
    test_hi_romantic()