from google.cloud import translate_v2
import os

from pydub import AudioSegment, effects
from pydub.playback import _play_with_ffplay
import io
import threading
import sys
import contextlib

client = translate_v2.Client()

def translate_text(text: str):
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = client.translate(text, source_language="ja-JP",
                              target_language="en-US", 
                              model="nmt")

    return result['translatedText']
    
# translate_text("こんにちは")