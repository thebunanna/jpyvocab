from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from engine import Engine, get_parsed_str, get_detailed
from audio import play_text
from translate import translate_text
import os
import io
from google.cloud import texttospeech
from pydub import AudioSegment, effects
import base64

app = Flask(__name__)
CORS(app)

engine = Engine()
tts_client = texttospeech.TextToSpeechClient(client_options={"api_key": os.environ.get("TTS_KEY")})

@app.route('/api/next', methods=['GET'])
def get_next():
    """Get the next card and sentence to review"""
    text, card, vocab = engine.get_next()
    
    # Parse the text
    t_str, comp_str = get_parsed_str(text)
    hira_str, kata_str = t_str
    comp_str_split = comp_str.split(" ")
    
    # Get detailed info for all words
    detailed = get_detailed(text, 80)
    
    return jsonify({
        'text': text,
        'words': comp_str_split,
        'hiragana': hira_str.split(" "),
        'katakana': kata_str.split(" "),
        'vocab': {
            'id': vocab['id'],
            'word': vocab['word'],
            'hira': vocab['hira'],
            'translated': vocab['translated']
        },
        'card': {
            'scheduled_days': card.scheduled_days,
            'state': card.state.value,
            'reps': card.reps,
            'difficulty': card.difficulty
        },
        'card_dict': card.to_dict(),
        'detailed': detailed
    })

@app.route('/api/review', methods=['POST'])
def review_card():
    """Submit a rating for the current card"""
    data = request.json
    rating = data.get('rating')
    card_data = data.get('card')
    vocab_id = data.get('vocab_id')
    
    if rating is None or card_data is None or vocab_id is None:
        return jsonify({'error': 'Missing rating, card data, or vocab_id'}), 400
    
    # Rating: 0=Again, 1=Hard, 2=Good, 3=Easy (maps to FSRS Rating enum which is 1-4)
    from fsrs import Rating, Card
    rating_map = {0: Rating.Again, 1: Rating.Hard, 2: Rating.Good, 3: Rating.Easy}
    fsrs_rating = rating_map.get(rating)
    
    if fsrs_rating is None:
        return jsonify({'error': 'Invalid rating value'}), 400
    
    # Reconstruct Card object from data
    card = Card.from_dict(card_data)
    
    updated_card = engine.review_card(
        card, 
        vocab_id, 
        fsrs_rating
    )
    
    return jsonify({
        'success': True,
        'card': {
            'scheduled_days': updated_card.scheduled_days,
            'state': updated_card.state.value,
            'reps': updated_card.reps
        }
    })

@app.route('/api/ban-word', methods=['POST'])
def ban_word():
    """Toggle ban status for a word"""
    data = request.json
    word = data.get('word')
    
    if not word:
        return jsonify({'error': 'No word provided'}), 400
    
    engine.ban_word(word)
    is_banned = word in engine.banned
    
    return jsonify({
        'success': True,
        'word': word,
        'banned': is_banned
    })

@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate Japanese text to English"""
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    translated = translate_text(text)
    
    return jsonify({
        'original': text,
        'translated': translated
    })

@app.route('/api/audio', methods=['POST'])
def get_audio():
    """Generate and return audio for Japanese text"""
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Generate audio using Google Cloud TTS
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP", name="ja-JP-Standard-A"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    # Normalize audio
    s = io.BytesIO(response.audio_content)
    song = effects.normalize(AudioSegment.from_file(s)) - 2
    
    # Export to bytes
    audio_bytes = io.BytesIO()
    song.export(audio_bytes, format='mp3')
    audio_bytes.seek(0)
    
    # Return as base64 for easy embedding
    audio_b64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
    
    return jsonify({
        'audio': audio_b64
    })

@app.route('/api/parse', methods=['POST'])
def parse_text():
    """Parse Japanese text and return detailed information"""
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    t_str, comp_str = get_parsed_str(text)
    hira_str, kata_str = t_str
    detailed = get_detailed(text, 80)
    
    return jsonify({
        'words': comp_str.split(" "),
        'hiragana': hira_str.split(" "),
        'katakana': kata_str.split(" "),
        'detailed': detailed
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about current session"""
    return jsonify({
        'redo_count': len(engine.redo),
        'visited_count': len(engine.visted),
        'banned_count': len(engine.banned)
    })

@app.route('/')
def index():
    """Serve the main page"""
    return send_file('templates/index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
