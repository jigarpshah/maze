// a global variable that will hold a reference to the api swf once it has loaded
var apiswf = null;
var firstsong = null;

function getSuggestedTracks() {
  $.ajax({
    type: "GET",
    url: "/radio/suggest/",
    data: {
      date_range: $("#songlist").data('date_range'),
      language: $("#songlist").data('language'),
      mood: $("#songlist").data('mood'),
    },
    success: function(data) {
      var suggestions = $("#track-suggestions .suggestions");
      suggestions.html("");
      $.each(data['suggestions'], function(i, suggestion) {
        console.log(arguments);
        var node = $(
            "<div class=\"suggestion\">" +
              "<img src=\"" + suggestion['thumbnail'] + "\" />" +
              "<div>" + suggestion['artist'] + " - " + suggestion['song'] + "</div>" +
            "</div>");
        node.click(function() {
          apiswf.rdio_play(suggestion['key']);
        });
        suggestions.append(node);
      });
      if (data['suggestions'].length)
        $("#track-suggestions").show();
      else
        $("#track-suggestions").hide();
    }
  })
}

$(document).ready(function() {
  getSuggestedTracks();
  // on page load use SWFObject to load the API swf into div#apiswf
  var flashvars = {
    'playbackToken': 'FglWTcFm_____1RDTXEzbzQtME5xVHZkWGtvWFJwYndsb2NhbGhvc3T_XwPMbUN5TjHBFt0TI1uX', // from token.js
    'domain': 'localhost',                // from token.js
    'listener': 'callback_object'    // the global name of the object that will receive callbacks from the SWF
    };
  var params = {
    'allowScriptAccess': 'always'
  };
  var attributes = {};
  swfobject.embedSWF('http://www.rdio.com/api/swf/', // the location of the Rdio Playback API SWF
      'apiswf', // the ID of the element that will be replaced with the SWF
      1, 1, '9.0.0', 'expressInstall.swf', flashvars, params, attributes);

  var next = 2
  var song = document.getElementById('song1').getAttribute('value');
    firstsong = song
  $('#play').click(function() {
    apiswf.rdio_play(song);
    next = next+1;
  });
  $('#stop').click(function() { apiswf.rdio_stop(); });
  $('#pause').click(function() { apiswf.rdio_pause(); });
  $('#previous').click(function() { apiswf.rdio_previous(); });
 $('.mood_input').click(function() { 
    var mood = this.getAttribute('value');
    var trackId = document.getElementById('song'+(next-1)).getAttribute('value');
    var data = {'track': trackId,
              'mood': mood}
    $.ajax({
        type: "POST",
        url: "/radio/feedback/",
        data: data,
        success: function() {
          getSuggestedTracks(mood);
        }
      });
  
  });

  $('#next').click(function() { 
    var nextSong = 'song'+next;
    var song = document.getElementById(nextSong).getAttribute('value');
    apiswf.rdio_play(song); 
    next = next+1;});



});


// the global callback object
var callback_object = {};

callback_object.ready = function ready(user) {
  // Called once the API SWF has loaded and is ready to accept method calls.

  // find the embed/object element
  apiswf = $('#apiswf').get(0);

  apiswf.rdio_startFrequencyAnalyzer({
    frequencies: '10-band',
    period: 100
  });

  if (user == null) {
    $('#nobody').show();
  } else if (user.isSubscriber) {
    $('#subscriber').show();
  } else if (user.isTrial) {
    $('#trial').show();
  } else if (user.isFree) {
    $('#remaining').text(user.freeRemaining);
    $('#free').show();
  } else {
    $('#nobody').show();
  }
    apiswf.rdio_play(firstsong)
  console.log(user);
}

callback_object.freeRemainingChanged = function freeRemainingChanged(remaining) {
  $('#remaining').text(remaining);
}

callback_object.playStateChanged = function playStateChanged(playState) {
  // The playback state has changed.
  // The state can be: 0 - paused, 1 - playing, 2 - stopped, 3 - buffering or 4 - paused.
  $('#playState').text(playState);
}

callback_object.playingTrackChanged = function playingTrackChanged(playingTrack, sourcePosition) {
  // The currently playing track has changed.
  // Track metadata is provided as playingTrack and the position within the playing source as sourcePosition.
  if (playingTrack != null) {
    $('#track').text(playingTrack['name']);
    $('#album').text(playingTrack['album']);
    $('#artist').text(playingTrack['artist']);
    $('#art').attr('src', playingTrack['icon']);
  }
}

callback_object.playingSourceChanged = function playingSourceChanged(playingSource) {
  // The currently playing source changed.
  // The source metadata, including a track listing is inside playingSource.
}

callback_object.volumeChanged = function volumeChanged(volume) {
  // The volume changed to volume, a number between 0 and 1.
}

callback_object.muteChanged = function muteChanged(mute) {
  // Mute was changed. mute will either be true (for muting enabled) or false (for muting disabled).
}

callback_object.positionChanged = function positionChanged(position) {
  //The position within the track changed to position seconds.
  // This happens both in response to a seek and during playback.
  $('#position').text(position);
}

callback_object.queueChanged = function queueChanged(newQueue) {
  // The queue has changed to newQueue.
}

callback_object.shuffleChanged = function shuffleChanged(shuffle) {
  // The shuffle mode has changed.
  // shuffle is a boolean, true for shuffle, false for normal playback order.
}

callback_object.repeatChanged = function repeatChanged(repeatMode) {
  // The repeat mode change.
  // repeatMode will be one of: 0: no-repeat, 1: track-repeat or 2: whole-source-repeat.
}

callback_object.playingSomewhereElse = function playingSomewhereElse() {
  // An Rdio user can only play from one location at a time.
  // If playback begins somewhere else then playback will stop and this callback will be called.
}

callback_object.updateFrequencyData = function updateFrequencyData(arrayAsString) {
  // Called with frequency information after apiswf.rdio_startFrequencyAnalyzer(options) is called.
  // arrayAsString is a list of comma separated floats.

  var arr = arrayAsString.split(',');

  $('#freq div').each(function(i) {
    $(this).width(parseInt(parseFloat(arr[i])*500));
  })
}

