// Slot Type Puzzle State
let slotPuzzleState = {
    sourceWords: [],
    extraLetter1: '',
    extraLetter2: '',
    targetWords: ['', '', '']
};

// Utility: Get letter counts from a string
function getSlotLetterCounts(str) {
    const counts = {};
    for (const char of str.toLowerCase()) {
        if (char >= 'a' && char <= 'z') {
            counts[char] = (counts[char] || 0) + 1;
        }
    }
    return counts;
}

// Utility: Check if a word can be made from available letters
function canMakeWordFromPool(word, letterPool) {
    const wordCounts = getSlotLetterCounts(word);
    const poolCounts = getSlotLetterCounts(letterPool);

    for (const [letter, count] of Object.entries(wordCounts)) {
        if (!poolCounts[letter] || poolCounts[letter] < count) {
            return false;
        }
    }
    return true;
}

// Utility: Check if word contains a specific letter
function wordContainsLetter(word, letter) {
    if (!word || !letter) return false;
    return word.toLowerCase().includes(letter.toLowerCase());
}

// Utility: Get base letter pool from source words only (no extra letters)
function getBaseLetterPool() {
    let pool = '';
    for (const word of slotPuzzleState.sourceWords) {
        pool += word.toLowerCase();
    }
    return pool;
}

// Utility: Get full letter pool including both extra letters
function getSlotLetterPool() {
    let pool = getBaseLetterPool();
    if (slotPuzzleState.extraLetter1) pool += slotPuzzleState.extraLetter1.toLowerCase();
    if (slotPuzzleState.extraLetter2) pool += slotPuzzleState.extraLetter2.toLowerCase();
    return pool;
}

// Utility: Check if word is in dictionary
function slotIsInDictionary(word) {
    if (typeof currentWordSet !== 'undefined') {
        return currentWordSet.has(word.toLowerCase());
    }
    return true;
}

// Handle Enter key on source word input
function slotHandleSourceWordKeypress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        slotAddSourceWord();
    }
}

// Add a new source word
function slotAddSourceWord() {
    const input = document.getElementById('new-source-word-input');
    const word = input.value.trim().toLowerCase();

    if (!word) return;

    slotPuzzleState.sourceWords.push(word);
    input.value = '';

    slotRenderSourceWords();
    slotRenderLetterPool();
    slotRenderTargetWords();
    slotUpdateSummary();
}

// Remove a source word
function slotRemoveSourceWord(index) {
    slotPuzzleState.sourceWords.splice(index, 1);
    slotRenderSourceWords();
    slotRenderLetterPool();
    slotRenderTargetWords();
    slotUpdateSummary();
}

// Update extra letter 1
function updateExtraLetter1() {
    const input = document.getElementById('extra-letter-1-input');
    const letter = input.value.replace(/[^a-zA-Z]/g, '').toLowerCase().charAt(0) || '';
    slotPuzzleState.extraLetter1 = letter;
    input.value = letter.toUpperCase();

    slotRenderExtraLetters();
    slotRenderLetterPool();
    slotRenderTargetWords();
    slotUpdateSummary();
}

// Update extra letter 2
function updateExtraLetter2() {
    const input = document.getElementById('extra-letter-2-input');
    const letter = input.value.replace(/[^a-zA-Z]/g, '').toLowerCase().charAt(0) || '';
    slotPuzzleState.extraLetter2 = letter;
    input.value = letter.toUpperCase();

    slotRenderExtraLetters();
    slotRenderLetterPool();
    slotRenderTargetWords();
    slotUpdateSummary();
}

// Update a target word
function updateSlotTargetWord(index, value) {
    slotPuzzleState.targetWords[index] = value.trim().toLowerCase();
    slotRenderTargetWords();
    slotUpdateSummary();
}

// Validate target word based on slot puzzle rules:
// - Target 1: must use extra letter 1
// - Target 2: must use extra letter 2
// - Target 3: must use BOTH extra letters
function slotValidateTargetWord(word, index) {
    if (!word) return { valid: null, icon: '', color: '#e0e0e0', message: '' };

    const basePool = getBaseLetterPool();
    const fullPool = getSlotLetterPool();
    const letter1 = slotPuzzleState.extraLetter1;
    const letter2 = slotPuzzleState.extraLetter2;
    const inDict = slotIsInDictionary(word);

    // First check: can the word be made from the full pool?
    const canMake = canMakeWordFromPool(word, fullPool);
    if (!canMake) {
        return {
            valid: false,
            icon: '❌',
            color: 'var(--burnt-sienna)',
            message: 'Cannot be made from available letters'
        };
    }

    // Check dictionary
    if (!inDict) {
        return {
            valid: false,
            icon: '⚠️',
            color: '#ffc107',
            message: 'Not in dictionary'
        };
    }

    // Now check slot-specific rules
    if (index === 0) {
        // Target 1: must require extra letter 1
        if (!letter1) {
            return { valid: false, icon: '⚠️', color: '#ffc107', message: 'Set Extra Letter 1 first' };
        }
        const poolWithoutLetter1 = basePool + letter2;
        const canMakeWithout = canMakeWordFromPool(word, poolWithoutLetter1);
        if (canMakeWithout) {
            return {
                valid: false,
                icon: '❌',
                color: 'var(--burnt-sienna)',
                message: `Must require letter "${letter1.toUpperCase()}" (can be made without it)`
            };
        }
        return { valid: true, icon: '✅', color: 'var(--persian-green)', message: `Uses "${letter1.toUpperCase()}" ✓` };
    }
    else if (index === 1) {
        // Target 2: must require extra letter 2
        if (!letter2) {
            return { valid: false, icon: '⚠️', color: '#ffc107', message: 'Set Extra Letter 2 first' };
        }
        const poolWithoutLetter2 = basePool + letter1;
        const canMakeWithout = canMakeWordFromPool(word, poolWithoutLetter2);
        if (canMakeWithout) {
            return {
                valid: false,
                icon: '❌',
                color: 'var(--burnt-sienna)',
                message: `Must require letter "${letter2.toUpperCase()}" (can be made without it)`
            };
        }
        return { valid: true, icon: '✅', color: 'var(--persian-green)', message: `Uses "${letter2.toUpperCase()}" ✓` };
    }
    else if (index === 2) {
        // Target 3: must require BOTH extra letters
        if (!letter1 || !letter2) {
            return { valid: false, icon: '⚠️', color: '#ffc107', message: 'Set both extra letters first' };
        }
        // Check that word can't be made without letter 1
        const poolWithoutLetter1 = basePool + letter2;
        const canMakeWithoutLetter1 = canMakeWordFromPool(word, poolWithoutLetter1);
        // Check that word can't be made without letter 2
        const poolWithoutLetter2 = basePool + letter1;
        const canMakeWithoutLetter2 = canMakeWordFromPool(word, poolWithoutLetter2);

        if (canMakeWithoutLetter1 && canMakeWithoutLetter2) {
            return {
                valid: false,
                icon: '❌',
                color: 'var(--burnt-sienna)',
                message: 'Must require BOTH extra letters'
            };
        }
        if (canMakeWithoutLetter1) {
            return {
                valid: false,
                icon: '❌',
                color: 'var(--burnt-sienna)',
                message: `Must also require "${letter1.toUpperCase()}" (only uses "${letter2.toUpperCase()}")`
            };
        }
        if (canMakeWithoutLetter2) {
            return {
                valid: false,
                icon: '❌',
                color: 'var(--burnt-sienna)',
                message: `Must also require "${letter2.toUpperCase()}" (only uses "${letter1.toUpperCase()}")`
            };
        }
        return { valid: true, icon: '✅', color: 'var(--persian-green)', message: `Uses both "${letter1.toUpperCase()}" and "${letter2.toUpperCase()}" ✓` };
    }

    return { valid: true, icon: '✅', color: 'var(--persian-green)', message: 'Valid!' };
}

// Render source words list
function slotRenderSourceWords() {
    const container = document.getElementById('source-words-list');
    if (!container) return;

    if (slotPuzzleState.sourceWords.length === 0) {
        container.innerHTML = '<p style="font-size: 12px; color: #999; font-style: italic;">No source words added yet</p>';
        return;
    }

    container.innerHTML = `
        <div class="selected-source-tags">
            ${slotPuzzleState.sourceWords.map((word, index) => {
        const inDict = slotIsInDictionary(word);
        return `
                    <div class="source-tag" style="background: ${inDict ? 'var(--persian-green)' : '#ffc107'}; color: ${inDict ? 'white' : '#333'};">
                        ${!inDict ? '⚠️ ' : ''}${word.toUpperCase()}
                        <span class="remove" onclick="slotRemoveSourceWord(${index})">&times;</span>
                    </div>
                `;
    }).join('')}
        </div>
    `;
}

// Render extra letters tiles
function slotRenderExtraLetters() {
    const container = document.getElementById('extra-letters-display');
    if (!container) return;
    const letters = [];

    if (slotPuzzleState.extraLetter1) {
        letters.push(`<span class="letter-tile" style="background: #ffc107; border-color: #e0a800;" title="Extra Letter 1">${slotPuzzleState.extraLetter1.toUpperCase()}</span>`);
    }
    if (slotPuzzleState.extraLetter2) {
        letters.push(`<span class="letter-tile" style="background: #ffc107; border-color: #e0a800;" title="Extra Letter 2">${slotPuzzleState.extraLetter2.toUpperCase()}</span>`);
    }

    container.innerHTML = letters.join('') || '<span style="font-size: 12px; color: #999;">Enter 2 extra letters above</span>';
}

// Render letter pool preview
function slotRenderLetterPool() {
    const container = document.getElementById('letter-pool-display');
    const statsContainer = document.getElementById('letter-pool-stats');
    if (!container || !statsContainer) return;
    const pool = getSlotLetterPool();

    if (!pool) {
        container.innerHTML = '<span style="font-size: 12px; color: #999;">Add source words or letters above...</span>';
        statsContainer.innerHTML = '';
        return;
    }

    const sortedLetters = pool.split('').sort();

    container.innerHTML = sortedLetters.map(letter =>
        `<span class="letter-tile">${letter.toUpperCase()}</span>`
    ).join('');

    const wordCount = slotPuzzleState.sourceWords.length;
    const extraCount = (slotPuzzleState.extraLetter1 ? 1 : 0) + (slotPuzzleState.extraLetter2 ? 1 : 0);
    statsContainer.innerHTML = `
        <strong>${pool.length}</strong> total letters 
        (${wordCount} word${wordCount !== 1 ? 's' : ''}, ${extraCount}/2 extra letters)
    `;
}

// Render target words with validation
function slotRenderTargetWords() {
    const container = document.getElementById('target-words-list');
    if (!container) return;
    const letter1 = slotPuzzleState.extraLetter1;
    const letter2 = slotPuzzleState.extraLetter2;

    const targetLabels = [
        `Target 1 (uses "${letter1 ? letter1.toUpperCase() : '?'}")`,
        `Target 2 (uses "${letter2 ? letter2.toUpperCase() : '?'}")`,
        `Target 3 (uses both "${letter1 ? letter1.toUpperCase() : '?'}" + "${letter2 ? letter2.toUpperCase() : '?'}")`
    ];

    container.innerHTML = slotPuzzleState.targetWords.map((word, index) => {
        const validation = slotValidateTargetWord(word, index);

        return `
            <div style="margin-bottom: 16px;">
                <div style="font-size: 12px; color: var(--charcoal); font-weight: 600; margin-bottom: 4px;">${targetLabels[index]}</div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-weight: 700; color: var(--charcoal); min-width: 24px;">${index + 1}.</span>
                    <input 
                        type="text" 
                        value="${word}" 
                        placeholder="Enter word..." 
                        style="flex: 1; padding: 8px 12px; font-size: 14px; border: 3px solid ${validation.color}; border-radius: 12px; font-weight: 600;"
                        oninput="updateSlotTargetWord(${index}, this.value)"
                    >
                    <span style="font-size: 20px; min-width: 28px; text-align: center;">${validation.icon}</span>
                </div>
                ${validation.message ? `<div style="font-size: 11px; color: ${validation.color === 'var(--persian-green)' ? 'var(--persian-green)' : validation.color}; margin-left: 32px; margin-top: 4px;">${validation.message}</div>` : ''}
            </div>
        `;
    }).join('');
}

// Update puzzle summary
function slotUpdateSummary() {
    const summaryPanel = document.getElementById('slot-puzzle-summary');
    const summaryContent = document.getElementById('slot-summary-content');
    if (!summaryPanel || !summaryContent) return;

    const filledTargets = slotPuzzleState.targetWords.filter(w => w.trim());
    const validTargets = slotPuzzleState.targetWords.map((w, i) => slotValidateTargetWord(w, i)).filter(v => v.valid === true);

    if (slotPuzzleState.sourceWords.length === 0 && !slotPuzzleState.extraLetter1 && !slotPuzzleState.extraLetter2) {
        summaryPanel.style.display = 'none';
        return;
    }

    summaryPanel.style.display = 'block';

    const letter1 = slotPuzzleState.extraLetter1;
    const letter2 = slotPuzzleState.extraLetter2;
    const isComplete = filledTargets.length === 3 && validTargets.length === 3 && letter1 && letter2;

    summaryContent.innerHTML = `
        <div style="display: grid; gap: 16px;">
            <div>
                <div style="font-weight: 700; color: var(--charcoal); margin-bottom: 8px;">Source Words:</div>
                <div class="letters">
                    ${slotPuzzleState.sourceWords.map(w =>
        `<span style="background: var(--saffron); color: var(--charcoal); padding: 4px 10px; border-radius: 12px; font-weight: 700; border: 2px solid #c9a854;">${w.toUpperCase()}</span>`
    ).join('') || '<span style="color: #999;">None</span>'}
                </div>
            </div>
            
            <div>
                <div style="font-weight: 700; color: var(--charcoal); margin-bottom: 8px;">Extra Letters:</div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    <span style="font-size: 12px; color: #666;">Letter 1:</span>
                    <span class="letter-tile" style="background: ${letter1 ? '#ffc107' : '#f5f5f5'}; border-color: ${letter1 ? '#e0a800' : '#ccc'}; ${!letter1 ? 'color: #999;' : ''}">${letter1 ? letter1.toUpperCase() : '?'}</span>
                    <span style="font-size: 12px; color: #666;">Letter 2:</span>
                    <span class="letter-tile" style="background: ${letter2 ? '#ffc107' : '#f5f5f5'}; border-color: ${letter2 ? '#e0a800' : '#ccc'}; ${!letter2 ? 'color: #999;' : ''}">${letter2 ? letter2.toUpperCase() : '?'}</span>
                </div>
            </div>
            
            <div>
                <div style="font-weight: 700; color: var(--charcoal); margin-bottom: 8px;">Target Words:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    ${slotPuzzleState.targetWords.map((w, i) => {
        if (!w) return `<span style="color: #999; background: #f5f5f5; padding: 4px 10px; border-radius: 12px; border: 2px dashed #ccc;">Target ${i + 1}</span>`;
        const validation = slotValidateTargetWord(w, i);
        return `<span style="background: ${validation.valid ? 'var(--persian-green)' : 'var(--burnt-sienna)'}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: 700; border: 2px solid ${validation.valid ? '#228276' : '#c05640'};">${w.toUpperCase()} ${validation.valid ? '✓' : '✗'}</span>`;
    }).join('')}
                </div>
            </div>
            
            <div style="padding: 12px; background: ${isComplete ? '#e8f4f2' : '#fff3cd'}; border-radius: 12px; border: 2px solid ${isComplete ? 'var(--persian-green)' : '#ffc107'};">
                <span style="font-weight: 700; color: ${isComplete ? 'var(--persian-green)' : '#856404'};">
                    ${isComplete ? '✅ Puzzle is complete and valid!' : `⚠️ ${3 - validTargets.length} target word${3 - validTargets.length !== 1 ? 's' : ''} need${3 - validTargets.length === 1 ? 's' : ''} attention`}
                </span>
            </div>
        </div>
    `;
}

// Initialize slot puzzle tab
function initSlotPuzzle() {
    slotRenderSourceWords();
    slotRenderExtraLetters();
    slotRenderLetterPool();
    slotRenderTargetWords();
    slotUpdateSummary();
}
