
from django.conf.urls import url
import views


urlpatterns = [
    url(r'^$', views.home),
    url(r'^landing/$', views.landing),
    url(r'^dummy/$', views.dummy),
    url(r'^song/$', views.get_song_list),
    url(r'^feedback/$', views.provide_feedback),
    url(r'^dummy_feedback/$', views.dummy_feedback),
    url(r'^suggest/$', views.suggest_new_songs),
]
