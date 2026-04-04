// Word Finder (Reverse Mode)
// Input letters/words → find all dictionary words that can be made from them

let wordFinderState = {
    inputLetters: '',
    currentResults: [],
    resultsShown: 0,
    initialized: false
};

function wordFinderSearch() {
    const input = document.getElementById('word-finder-input');
    const rawInput = input.value.trim().toLowerCase().replace(/[^a-z]/g, '');

    if (!rawInput) {
        document.getElementById('word-finder-summary').style.display = 'none';
        document.getElementById('word-finder-results').innerHTML = '<p style="padding: 12px; color: #999;">Enter some letters above to find words.</p>';
        return;
    }

    wordFinderState.inputLetters = rawInput;

    // Show letter summary
    const summaryDiv = document.getElementById('word-finder-summary');
    summaryDiv.style.display = 'block';
    const letterCounts = {};
    for (const char of rawInput) {
        letterCounts[char] = (letterCounts[char] || 0) + 1;
    }
    const lettersList = Object.entries(letterCounts)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([letter, count]) => `${letter.toUpperCase()}×${count}`)
        .join('  ');

    document.getElementById('word-finder-summary').innerHTML = `
        Available letters: <strong>${rawInput.toUpperCase()}</strong> (${rawInput.length} total)<br>
        <span style="font-size: 12px; color: #888;">${lettersList}</span>
    `;

    const resultsDiv = document.getElementById('word-finder-results');
    resultsDiv.innerHTML = '<p style="padding: 12px; color: #666;">Searching...</p>';

    // Defer to let the UI update
    setTimeout(() => {
        const minLength = parseInt(document.getElementById('wf-min-length').value) || 2;
        const maxLength = parseInt(document.getElementById('wf-max-length').value) || 20;
        const firstLetter = document.getElementById('wf-first-letter').value;
        const sortAlpha = document.getElementById('wf-sort-alpha').checked;
        const exactOnly = document.getElementById('wf-exact-match').checked;

        const results = [];
        const inputSorted = rawInput.split('').sort().join('');

        for (const word of currentWordList) {
            if (word.length < minLength || word.length > maxLength) continue;
            if (firstLetter && word[0] !== firstLetter) continue;

            if (exactOnly) {
                // Exact anagram — must use all letters
                if (word.length !== rawInput.length) continue;
                const wordSorted = word.split('').sort().join('');
                if (wordSorted === inputSorted) {
                    results.push(word);
                }
            } else {
                // Partial — word can use subset of letters
                if (canMakeWord(word, rawInput)) {
                    results.push(word);
                }
            }
        }

        if (sortAlpha) {
            results.sort();
        } else {
            // Shuffle results (Fisher-Yates) so you don't always see the same words
            for (let i = results.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [results[i], results[j]] = [results[j], results[i]];
            }
        }

        wordFinderState.currentResults = results;
        wordFinderState.resultsShown = 0;

        if (results.length === 0) {
            resultsDiv.innerHTML = '<p style="padding: 12px; color: #666;">No words found with these letters.</p>';
            return;
        }

        wordFinderRenderResults();
    }, 10);
}

function wordFinderRenderResults() {
    const resultsDiv = document.getElementById('word-finder-results');
    const results = wordFinderState.currentResults;
    const batchSize = 200;
    const startIndex = wordFinderState.resultsShown;
    const endIndex = Math.min(startIndex + batchSize, results.length);
    const batch = results.slice(startIndex, endIndex);

    const itemsHTML = batch.map(word => {
        return `<div class="suggestion-item" style="cursor: default;">${word}</div>`;
    }).join('');

    const hasMore = endIndex < results.length;
    const countText = `Showing ${endIndex} of ${results.length} words`;

    if (startIndex === 0) {
        resultsDiv.innerHTML = `
            <div class="word-finder-results-count">${results.length} word${results.length !== 1 ? 's' : ''} found</div>
            <div class="suggestions-list" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 4px;">
                <div id="wf-items" style="display: contents;">${itemsHTML}</div>
                ${hasMore ? `
                    <div id="wf-load-more" style="grid-column: 1/-1; margin-top: 8px; text-align: center;">
                        <p style="font-size: 11px; color: #666; margin-bottom: 8px;">${countText}</p>
                        <button class="btn btn-secondary btn-small" onclick="wordFinderLoadMore()" style="padding: 6px 16px;">Load More</button>
                    </div>
                ` : `
                    <p style="grid-column: 1/-1; margin-top: 8px; font-size: 11px; color: #666; text-align: center;">${countText}</p>
                `}
            </div>
        `;
    } else {
        const itemsContainer = document.getElementById('wf-items');
        itemsContainer.insertAdjacentHTML('beforeend', itemsHTML);

        const loadMoreContainer = document.getElementById('wf-load-more');
        if (hasMore) {
            loadMoreContainer.querySelector('p').textContent = countText;
        } else {
            loadMoreContainer.innerHTML = `<p style="font-size: 11px; color: #666; text-align: center;">${countText}</p>`;
        }
    }

    wordFinderState.resultsShown = endIndex;
}

function wordFinderLoadMore() {
    wordFinderRenderResults();
}

function wordFinderShuffle() {
    if (wordFinderState.currentResults.length === 0) return;
    const arr = wordFinderState.currentResults;
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    wordFinderState.resultsShown = 0;
    wordFinderRenderResults();
}

function wordFinderHandleKeypress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        wordFinderSearch();
    }
}

function initWordFinder() {
    if (wordFinderState.initialized) return;
    wordFinderState.initialized = true;
}
