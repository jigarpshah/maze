#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from apiclient import discovery

GOOGLE_API_KEY = "AIzaSyACyQuJQhVHE4uM6CpYImrwA5Vh0023e-Y"

def detect_language(song_title):
    service = discovery.build('translate', 'v2', developerKey=GOOGLE_API_KEY)
    results = service.detections().list(q=song_title).execute()

    language, confidence = (None, 0)
    for detection in results.get('detections', []):
        for language_info in detection:
            if language_info['confidence'] > confidence:
                language = language_info['language']
                confidence = language_info['confidence']

    return language

if __name__ == "__main__":
    print detect_language("Les Yeux Ouverts")
    print detect_language("Jardin D'hiver")
    print detect_language("Das Boot")
    print detect_language(u'Τι Να Το Κάνεις Το Κορμί')