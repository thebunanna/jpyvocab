# jpyvocab - Japanese Vocabulary Learning System

## Project Overview
Terminal-based Japanese vocabulary learning app using spaced repetition (FSRS algorithm). Users type Japanese sentences word-by-word, then review vocab with detailed breakdowns, translations, and audio playback.

## Architecture

### Core Components
- **[engine.py](engine.py)**: FSRS card scheduler, sentence generation via DeepSeek API, Japanese parsing (fugashi/nagisa), dictionary lookups (jamdict/jisho.org)
- **[main.py](main.py)**: Curses-based UI loop - word-by-word typing interface, vocab review with arrow navigation, rating system (0-3)
- **[audio.py](audio.py)**: Google Cloud TTS integration (threaded playback via ffplay)
- **[translate.py](translate.py)**: Google Cloud Translate wrapper for Japanese→English
- **[import.py](import.py)**: Database initialization from CSV (`n5_randomized.csv`)

### Database Schema (SQLite: jpy.db)
```sql
vocab(id, word, hira, translated)           -- Japanese words with hiragana/translations
card(id, due, stability, difficulty, ...)   -- FSRS spaced repetition cards
sentence(id, sentence, word_id)             -- Generated example sentences per vocab
```

## Critical Patterns

### State Management
- `Engine` maintains singleton state: `redo` set (failed reviews), `banned` words, `visited` vocab IDs
- Cards linked to vocab via `vocab_id` foreign key
- Curses UI runs in event loop with stateful input buffer

### Japanese Text Processing
```python
# Always parse with fugashi for tokenization
get_parsed_str(text) → ([katakana, hiragana], wakati_tokenized)

# Dictionary lookup cascade: jamdict → jisho.org fallback
# Results cached via @lru_cache(maxsize=128) on get_parsed_str
```

### Sentence Generation
- DeepSeek API generates contextual Japanese sentences containing target vocab
- System prompt enforces: no punctuation, grammatically correct Japanese
- Previously generated sentences stored to avoid repetition

### Review Flow
1. Fetch next due card (FSRS scheduler)
2. Generate/retrieve sentence with target vocab
3. User types sentence word-by-word (space-separated)
4. Arrow keys navigate vocab breakdown (dictionary entries from jamdict/jisho)
5. Rate 0-3 (Again/Hard/Good/Easy) → updates FSRS card

## Environment Setup

### Required .env Variables
```bash
OPENAI_API_KEY=...      # Not used (commented out)
DEEP_API_KEY=...        # DeepSeek API key (actual LLM)
TTS_KEY=...             # Google Cloud TTS API key
# Google Cloud credentials via default ADC for translate_v2
```

### Initialization Workflow
```bash
# 1. Activate venv
source vvv/bin/activate

# 2. Initialize database (run ONCE)
python import.py  # Creates jpy.db from n5_randomized.csv

# 3. Run app
python main.py    # Launches curses UI
```

### CSV Format (n5_randomized.csv)
```
word,hira,translation
こんにちは,こんにちは,hello
```

## UI Keybindings
- **Typing Phase**: Type words, Enter to submit (must match word count), Backspace/ESC
- **Review Phase**:
  - `←/→`: Navigate between words in sentence
  - `r`: Replay audio (threaded via [audio.py](audio.py))
  - `b`: Toggle ban word (excluded from future sentence generation)
  - `0-3`: Rate card (Again/Hard/Good/Easy)
  - `ESC`: Skip to next card

## Dependencies
- **Japanese NLP**: `fugashi` (MeCab wrapper), `nagisa`, `pykakasi`, `jamdict`
- **APIs**: `openai` (DeepSeek), `google-cloud-texttospeech`, `google-cloud-translate`
- **Audio**: `pydub` (requires ffplay installed)
- **FSRS**: `fsrs` package (spaced repetition algorithm)
- **UI**: `curses` (stdlib)

## Gotchas
- `fsrs_card.csv` is ignored but may exist as legacy export
- `logs/` directory exists but not actively used in current code
- Virtual environment is `vvv/` not `venv/` 
- Curses color pairs initialized dynamically (1-256)
- Audio playback redirects stdout/stderr to suppress ffplay logs
- Database connection is module-level singleton (`con` in [engine.py](engine.py))
- `get_parsed_str()` uses LRU cache - beware stale results if sentence regenerated
