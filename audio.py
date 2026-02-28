from google.cloud import texttospeech
import os

from pydub import AudioSegment, effects
from pydub.playback import _play_with_ffplay
import io
import threading
import sys
import contextlib

client = texttospeech.TextToSpeechClient(client_options={"api_key": os.environ.get("TTS_KEY")})

def play_text(text: str):
    thread = threading.Thread(target=_play_text, args=(text,))
    thread.start()

def _play_text(text: str): 
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP", name="ja-JP-Standard-A"
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    response.audio_content
    with open(os.devnull, 'w') as null, \
     contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
        s = io.BytesIO(response.audio_content)
        song = effects.normalize(AudioSegment.from_file(s)) - 2
        _play_with_ffplay(song)
    
# # Create a thread object
# thread = threading.Thread(target=play_text, args=("こんにちは",))

# # Start the thread
# thread.start()