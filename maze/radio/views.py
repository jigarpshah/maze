from json import dumps
from datetime import datetime
from traceback import print_exc
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from models import Song
from suggest import track_generator, SeedsNotFound, rdio

# Create your views here.

@csrf_exempt
def get_song_list(request):
    print request.POST
    params = request.POST
    dates = params['date_range'].split('-')
    start_year = dates[0].strip()
    end_year = dates[1].strip()
    emotions = params.getlist('mood')
    language = params['language']

    # get list of songs where year>=start and year<=end and emotions-->trait
    kwargs = {
        'year__gte': start_year,
        'year__lte': end_year,
        'language': language,
    }

    for emotion in emotions:
        kwargs[emotion+'__gt'] = 0

    result_set = Song.objects.filter(**kwargs).extra(
        select = {'score': 'CAST(%s AS FLOAT) / CAST((total_responses * %d) AS FLOAT)' % (__format_field_sum(emotions), len(emotions)),},
        order_by = ['-score','-total_responses'],
    )
    for result in result_set:
        print result.title, result.score

    return render(request, 'maze.html', {
        'keys': [result.rdio_key for result in result_set],
        'language': language,
        'date_range': params['date_range'],
        'mood': ','.join(emotions),
    })

def suggest_new_songs(request):
    params = request.GET
    print params
    start_year, end_year = [int(x.strip()) for x in params['date_range'].split('-')]
    emotions = params.get('mood').split(",")
    kwargs = {
        'year__gte': start_year,
        'year__lte': end_year,
        'language': params['language'],
    }
    result_set = Song.objects.filter(**kwargs).extra(
        select = {'score': "({})".format('+'.join(emotions))},
        order_by = ['-score',],
    )
    seeds = [{'artist': x.artist, 'song': x.title} for x in result_set[0:5]]
    print "Using seeds"
    print seeds

    try:
        language_codes = settings.TRANSLATE_LANG_CODE_MAP.get(params['language'], [])
        suggestor = track_generator(languages=language_codes,
            emotion=''.join([e[0:2] for e in emotions]),
            seeds=seeds,
            year_range=xrange(start_year, end_year))
        suggested_tracks = []
        for x in xrange(5):
            try:
                suggestion = suggestor.next()
                suggested_tracks.append({
                    'artist': suggestion['artist'],
                    'song': suggestion['name'],
                    'key': suggestion['key'],
                    'year': suggestion.get_release_date().year,
                    'thumbnail': suggestion['icon'],
                })
            except StopIteration:
                break
        return HttpResponse(dumps({
            'language': params['language'],
            'suggestions': suggested_tracks,
        }), "application/json")
    except SeedsNotFound:
        return HttpResponse(dumps({
            'error': 'Seeds not found in Pandora',
            'seeds': seeds
        }), "application/json")

def __format_field_sum(fields):
    s = '('
    for i in range(len(fields)-1):
        field = fields[i]
        s = s + field + ' + '
    s = s + fields[len(fields)-1] + ')'
    return s

@csrf_exempt
def provide_feedback(request):
    print request.POST
    params = request.POST
    mood = params['mood']
    track = params['track']
    song, created = Song.objects.get_or_create(rdio_key=track)
    if created:
        try:
            # load track information from Rdio API
            results = rdio.api().get(keys=track)
            if track in results:
                info = results[track]
                song.title = info['name']
                song.artist = info['artist']
                song.language = params['language']
                results = rdio.api().get(keys=info['albumKey'])
                if info['albumKey'] in results:
                    album_info = results[info['albumKey']]
                    song.year = datetime.strptime(album_info['releaseDate'], "%Y-%m-%d").year
            pass
        except KeyError:
            print_exc()
    song.incr_score(mood, save=True)
    return HttpResponse()

def dummy_feedback(request):
    return render(request, 'dummy_feedback.html')

def dummy(request):
    return render(request, 'dummy_page.html')

def home(request):
    return render(request, 'maze.html')

def landing(request):
    return render(request, 'initial_view.html')
