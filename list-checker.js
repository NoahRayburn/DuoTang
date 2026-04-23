// List Checker
// Input letters + one or more word lists → for each list, show which words can be made
// and a count, using canMakeWord from app.js.

let listCheckerState = {
    lists: [],
    nextId: 1,
    initialized: false
};

function listCheckerAddList() {
    const id = listCheckerState.nextId++;
    listCheckerState.lists.push({ id, name: `List ${id}`, words: '' });
    listCheckerRenderLists();
    listCheckerUpdateAll();
}

function listCheckerRemoveList(id) {
    listCheckerState.lists = listCheckerState.lists.filter(l => l.id !== id);
    if (listCheckerState.lists.length === 0) {
        listCheckerAddList();
        return;
    }
    listCheckerRenderLists();
    listCheckerUpdateAll();
}

function listCheckerHandleNameChange(id, name) {
    const list = listCheckerState.lists.find(l => l.id === id);
    if (list) list.name = name;
}

function listCheckerHandleWordsChange(id, words) {
    const list = listCheckerState.lists.find(l => l.id === id);
    if (list) list.words = words;
    listCheckerUpdateResults(id);
    listCheckerUpdateOverallSummary();
}

function listCheckerRenderLists() {
    const container = document.getElementById('list-checker-lists');
    if (!container) return;
    container.innerHTML = listCheckerState.lists.map(list => `
        <div class="list-checker-card" id="list-card-${list.id}">
            <div class="list-checker-card-header">
                <input type="text" value="${lcEscapeAttr(list.name)}"
                    oninput="listCheckerHandleNameChange(${list.id}, this.value)"
                    placeholder="List name"
                    class="list-checker-name-input">
                <button class="btn btn-secondary btn-small" onclick="listCheckerRemoveList(${list.id})" style="padding: 4px 12px;">Remove</button>
            </div>
            <textarea placeholder="Enter words separated by commas, spaces, or new lines..."
                oninput="listCheckerHandleWordsChange(${list.id}, this.value)"
                class="list-checker-words-input">${lcEscapeHtml(list.words)}</textarea>
            <div id="list-results-${list.id}" class="list-checker-results"></div>
        </div>
    `).join('');

    for (const list of listCheckerState.lists) {
        listCheckerUpdateResults(list.id);
    }
}

function listCheckerGetLetters() {
    const input = document.getElementById('list-checker-letters');
    if (!input) return '';
    return input.value.trim().toLowerCase().replace(/[^a-z]/g, '');
}

function listCheckerUpdateAll() {
    const letters = listCheckerGetLetters();
    listCheckerUpdateLetterSummary(letters);
    for (const list of listCheckerState.lists) {
        listCheckerUpdateResults(list.id);
    }
    listCheckerUpdateOverallSummary();
}

function listCheckerUpdateLetterSummary(letters) {
    const summary = document.getElementById('list-checker-letter-summary');
    if (!summary) return;
    if (!letters) {
        summary.style.display = 'none';
        return;
    }
    summary.style.display = 'block';
    const counts = {};
    for (const c of letters) counts[c] = (counts[c] || 0) + 1;
    const lettersList = Object.entries(counts)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([l, c]) => `${l.toUpperCase()}×${c}`)
        .join('  ');
    summary.innerHTML = `
        Available letters: <strong>${letters.toUpperCase()}</strong> (${letters.length} total)<br>
        <span style="font-size: 12px; color: #888;">${lettersList}</span>
    `;
}

function listCheckerUpdateResults(id) {
    const list = listCheckerState.lists.find(l => l.id === id);
    if (!list) return;
    const div = document.getElementById(`list-results-${id}`);
    if (!div) return;

    const letters = listCheckerGetLetters();
    const words = listCheckerParseWords(list.words);

    if (words.length === 0) {
        div.innerHTML = '<div class="list-checker-empty">No words in this list yet.</div>';
        return;
    }

    if (!letters) {
        div.innerHTML = `<div class="list-checker-empty">${words.length} word${words.length !== 1 ? 's' : ''} — enter letters above to check matches.</div>`;
        return;
    }

    const matches = words.filter(w => canMakeWord(w, letters));
    const pct = words.length > 0 ? Math.round((matches.length / words.length) * 100) : 0;

    div.innerHTML = `
        <div class="list-checker-count">
            <strong>${matches.length}</strong> of <strong>${words.length}</strong> words can be made <span style="color: #888; font-weight: 500;">(${pct}%)</span>
        </div>
        <div class="list-checker-matches">
            ${matches.length === 0
                ? '<span class="list-checker-empty">No words from this list can be made.</span>'
                : matches.map(w => `<span class="list-checker-chip">${lcEscapeHtml(w)}</span>`).join('')}
        </div>
    `;
}

function listCheckerUpdateOverallSummary() {
    const summary = document.getElementById('list-checker-overall');
    if (!summary) return;
    const letters = listCheckerGetLetters();

    if (!letters || listCheckerState.lists.length === 0) {
        summary.style.display = 'none';
        return;
    }

    let totalWords = 0;
    let totalMatches = 0;
    const perList = [];
    for (const list of listCheckerState.lists) {
        const words = listCheckerParseWords(list.words);
        const matches = words.filter(w => canMakeWord(w, letters));
        totalWords += words.length;
        totalMatches += matches.length;
        if (words.length > 0) {
            perList.push({ name: list.name, matches: matches.length, total: words.length });
        }
    }

    if (totalWords === 0) {
        summary.style.display = 'none';
        return;
    }

    const pct = Math.round((totalMatches / totalWords) * 100);
    const perListHtml = perList.map(p => {
        const pctList = Math.round((p.matches / p.total) * 100);
        return `<span class="list-checker-overall-chip"><strong>${lcEscapeHtml(p.name)}:</strong> ${p.matches}/${p.total} (${pctList}%)</span>`;
    }).join('');

    summary.style.display = 'block';
    summary.innerHTML = `
        <div style="margin-bottom: 6px;">Overall: <strong>${totalMatches}</strong> of <strong>${totalWords}</strong> words can be made (${pct}%)</div>
        <div class="list-checker-overall-chips">${perListHtml}</div>
    `;
}

function listCheckerParseWords(text) {
    const seen = new Set();
    const out = [];
    for (const raw of text.split(/[\n,;\s]+/)) {
        const w = raw.trim().toLowerCase().replace(/[^a-z]/g, '');
        if (!w || seen.has(w)) continue;
        seen.add(w);
        out.push(w);
    }
    return out;
}

function lcEscapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function lcEscapeAttr(s) {
    return lcEscapeHtml(s);
}

function listCheckerOnLettersInput() {
    listCheckerUpdateAll();
}

function initListChecker() {
    if (listCheckerState.initialized) return;
    listCheckerState.initialized = true;
    if (listCheckerState.lists.length === 0) {
        listCheckerAddList();
    } else {
        listCheckerRenderLists();
    }
}
