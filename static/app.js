// Global state
let currentData = null;
let currentWordIndex = 0;
let userInput = [];
let audio = null;

// API base URL
const API_BASE = '/api';

// Initialize app
async function init() {
    await loadNext();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    const wordInput = document.getElementById('word-input');
    
    // Handle word input
    wordInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const words = wordInput.value.trim().split(/\s+/).filter(w => w);
            if (words.length >= currentData.words.length) {
                userInput = words;
                await showReviewPhase();
            }
        } else if (e.key === 'Escape') {
            await loadNext();
        }
    });

    // Handle typing display update
    wordInput.addEventListener('input', (e) => {
        updateTypingDisplay(e.target.value);
    });

    // Navigation buttons
    document.getElementById('prev-word').addEventListener('click', () => {
        if (currentWordIndex > 0) {
            currentWordIndex--;
            updateWordDisplay();
        }
    });

    document.getElementById('next-word').addEventListener('click', () => {
        if (currentWordIndex < currentData.words.length - 1) {
            currentWordIndex++;
            updateWordDisplay();
        }
    });

    // Audio replay
    document.getElementById('replay-audio').addEventListener('click', async () => {
        await playAudio(currentData.text);
    });

    // Ban word
    document.getElementById('ban-word').addEventListener('click', async () => {
        const word = currentData.words[currentWordIndex];
        await banWord(word);
    });

    // Rating buttons
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rating = parseInt(btn.dataset.rating);
            await submitReview(rating);
        });
    });

    // Arrow keys for navigation
    document.addEventListener('keydown', (e) => {
        if (document.getElementById('review-phase').classList.contains('hidden')) {
            return;
        }

        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            if (currentWordIndex > 0) {
                currentWordIndex--;
                updateWordDisplay();
            }
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            if (currentWordIndex < currentData.words.length - 1) {
                currentWordIndex++;
                updateWordDisplay();
            }
        } else if (e.key === 'r') {
            e.preventDefault();
            playAudio(currentData.text);
        } else if (e.key === 'b') {
            e.preventDefault();
            const word = currentData.words[currentWordIndex];
            banWord(word);
        } else if (e.key >= '0' && e.key <= '3') {
            e.preventDefault();
            submitReview(parseInt(e.key));
        } else if (e.key === 'Escape') {
            e.preventDefault();
            loadNext();
        }
    });
}

// Load next card
async function loadNext() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/next`);
        currentData = await response.json();
        
        currentWordIndex = 0;
        userInput = [];
        
        // Update vocab display
        document.getElementById('vocab-word').textContent = currentData.vocab.word;
        document.getElementById('vocab-translation').textContent = currentData.vocab.translated;
        
        // Reset and show typing phase
        document.getElementById('word-input').value = '';
        document.getElementById('typing-phase').classList.remove('hidden');
        document.getElementById('review-phase').classList.add('hidden');
        
        // Hide vocab info during typing
        document.getElementById('vocab-word').classList.add('hidden');
        document.getElementById('vocab-translation').classList.add('hidden');
        
        updateTypingDisplay('');
        document.getElementById('word-input').focus();
        
    } catch (error) {
        console.error('Error loading next card:', error);
        alert('Error loading next card. Check console for details.');
    } finally {
        showLoading(false);
    }
}

// Update typing display
function updateTypingDisplay(input) {
    const display = document.getElementById('sentence-display');
    const hasTrailingSpace = input.endsWith(' ') && input.trim().length > 0;
    const inputWords = input.trim().split(/\s+/).filter(w => w);
    
    let html = '';
    
    if (hasTrailingSpace && inputWords.length < currentData.words.length) {
        // After space: show all typed words as green, next word as yellow
        for (let i = 0; i < inputWords.length && i < currentData.words.length; i++) {
            html += `<span class="word px-4 py-2 rounded-lg font-medium bg-green-600 text-white">${currentData.words[i]}</span>`;
        }
        
        // Show next word as yellow (current target)
        if (inputWords.length < currentData.words.length) {
            html += `<span class="word current px-4 py-2 rounded-lg font-bold bg-yellow-500 text-gray-900">${currentData.words[inputWords.length]}</span>`;
        }
        
        // Remaining words (gray)
        for (let i = inputWords.length + 1; i < currentData.words.length; i++) {
            html += `<span class="word px-4 py-2 rounded-lg font-medium bg-gray-600 text-gray-300">${currentData.words[i]}</span>`;
        }
    } else {
        // While typing: show completed words as green, current word as yellow
        for (let i = 0; i < inputWords.length - 1 && i < currentData.words.length; i++) {
            html += `<span class="word px-4 py-2 rounded-lg font-medium bg-green-600 text-white">${currentData.words[i]}</span>`;
        }
        
        // Current word being typed (yellow)
        if (inputWords.length > 0 && inputWords.length <= currentData.words.length) {
            html += `<span class="word current px-4 py-2 rounded-lg font-bold bg-yellow-500 text-gray-900">${currentData.words[inputWords.length - 1]}</span>`;
        }
        
        // Remaining words (gray)
        for (let i = inputWords.length; i < currentData.words.length; i++) {
            html += `<span class="word px-4 py-2 rounded-lg font-medium bg-gray-600 text-gray-300">${currentData.words[i]}</span>`;
        }
    }
    
    display.innerHTML = html;
}

// Show review phase
async function showReviewPhase() {
    document.getElementById('typing-phase').classList.add('hidden');
    document.getElementById('review-phase').classList.remove('hidden');
    
    // Show vocab info
    document.getElementById('vocab-word').classList.remove('hidden');
    document.getElementById('vocab-translation').classList.remove('hidden');
    
    // Get translation
    const translationResponse = await fetch(`${API_BASE}/translate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: currentData.text})
    });
    const translationData = await translationResponse.json();
    
    // Auto-play audio
    await playAudio(currentData.text);

    currentData.translation = translationData.translated;
    
    updateWordDisplay();
}

// Update word display in review phase
function updateWordDisplay() {
    // Update word navigation display
    const wordsHtml = currentData.words.map((word, idx) => {
        const classes = idx === currentWordIndex 
            ? 'word current px-4 py-2 rounded-lg font-bold bg-yellow-500 text-gray-900 cursor-pointer'
            : 'word px-4 py-2 rounded-lg font-medium bg-gray-600 text-gray-200 cursor-pointer hover:-translate-y-0.5 hover:bg-gray-500';
        return `<span class="${classes}" data-word-index="${idx}">${word}</span>`;
    }).join('');
    document.getElementById('sentence-words').innerHTML = wordsHtml;
    
    // Add click listeners to words
    document.querySelectorAll('#sentence-words .word').forEach(wordSpan => {
        wordSpan.addEventListener('click', () => {
            const idx = parseInt(wordSpan.dataset.wordIndex);
            currentWordIndex = idx;
            updateWordDisplay();
        });
    });
    
    // Update word details
    const details = currentData.detailed[currentWordIndex];
    let detailHtml = '<div class="space-y-2 leading-relaxed">';
    if (details && details.length > 0) {
        detailHtml += details.map(line => `<div>${escapeHtml(line)}</div>`).join('');
    } else {
        detailHtml += '<div>No dictionary entry found</div>';
    }
    detailHtml += '</div>';
    document.getElementById('word-detail').innerHTML = detailHtml;
    
    // Update sentence info
    document.getElementById('sentence-full').textContent = `Sentence: ${currentData.text}`;
    document.getElementById('sentence-translation').textContent = `Translation: ${currentData.translation || '...'}`;
    
    if (userInput.length > currentWordIndex) {
        document.getElementById('input-comparison').innerHTML = `
            <strong class="text-indigo-400">Your input:</strong> ${userInput[currentWordIndex]}<br>
            <strong class="text-indigo-400">Hiragana:</strong> ${currentData.hiragana[currentWordIndex]}<br>
            <strong class="text-indigo-400">Katakana:</strong> ${currentData.katakana[currentWordIndex]}
        `;
    }
    
    // Ban status (check if currently banned)
    const word = currentData.words[currentWordIndex];
    
    // Vocab and card info
    document.getElementById('vocab-info').innerHTML = `
        <strong class="text-indigo-400">Vocab:</strong> ${currentData.vocab.word} (${currentData.vocab.hira}) - ${currentData.vocab.translated}
    `;
    document.getElementById('card-info').innerHTML = `
        <strong class="text-indigo-400">Card:</strong> Scheduled: ${currentData.card.scheduled_days} days | State: ${currentData.card.state} | Reps: ${currentData.card.reps}
    `;
}

// Play audio
async function playAudio(text) {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/audio`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });
        const data = await response.json();
        
        // Play audio from base64
        if (audio) {
            audio.pause();
        }
        audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
        await audio.play();
    } catch (error) {
        console.error('Error playing audio:', error);
    } finally {
        showLoading(false);
    }
}

// Ban word
async function banWord(word) {
    try {
        const response = await fetch(`${API_BASE}/ban-word`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({word})
        });
        const data = await response.json();
        
        document.getElementById('ban-status').textContent = `Banned: ${data.banned ? 'Yes' : 'No'}`;
    } catch (error) {
        console.error('Error banning word:', error);
    }
}

// Submit review
async function submitReview(rating) {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                rating,
                card: currentData.card_dict,
                vocab_id: currentData.vocab.id
            })
        });
        
        if (response.ok) {
            await loadNext();
        } else {
            alert('Error submitting review');
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        alert('Error submitting review');
    } finally {
        showLoading(false);
    }
}

// Show/hide loading indicator
function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Decode HTML entities
function decodeHtml(html) {
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

// Start the app
init();
