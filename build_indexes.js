#!/usr/bin/env node
/**
 * Build optimized indexes for word lists.
 * Generates three parallel lists — FILTERED (concrete-ish original),
 * EXPANDED (includes abstract), and CONCRETE (new strict concrete list
 * from generate_concrete.py) — each with a signature index and a
 * first-letter+length index.
 */

const fs = require('fs');

function loadWordList() {
    const content = fs.readFileSync('words.js', 'utf8');

    const match1 = content.match(/const WORD_LIST = (\[[\s\S]*?\]);/);
    const wordList = match1 ? JSON.parse(match1[1]) : [];

    const match2 = content.match(/const WORD_LIST_EXPANDED = (\[[\s\S]*?\]);/);
    const wordListExpanded = match2 ? JSON.parse(match2[1]) : [];

    return { wordList, wordListExpanded };
}

function loadConcreteList() {
    // Produced by generate_concrete.py
    try {
        const raw = fs.readFileSync('concrete_nouns.json', 'utf8');
        return JSON.parse(raw).slice().sort();
    } catch (e) {
        console.warn('concrete_nouns.json not found; run generate_concrete.py first.');
        return [];
    }
}

function sortString(str) {
    return str.toLowerCase().split('').sort().join('');
}

function buildLetterSignatureIndex(wordList) {
    const index = {};
    for (const word of wordList) {
        const signature = sortString(word);
        if (!index[signature]) index[signature] = [];
        index[signature].push(word);
    }
    return index;
}

function buildFirstLetterLengthIndex(wordList) {
    const index = {};
    for (const word of wordList) {
        const firstLetter = word[0].toLowerCase();
        const length = word.length;
        if (!index[firstLetter]) index[firstLetter] = {};
        if (!index[firstLetter][length]) index[firstLetter][length] = [];
        index[firstLetter][length].push(word);
    }
    return index;
}

function main() {
    console.log('Loading word lists from words.js...');
    const { wordList, wordListExpanded } = loadWordList();

    console.log('Loading concrete noun list from concrete_nouns.json...');
    const wordListConcrete = loadConcreteList();

    console.log(`Filtered list: ${wordList.length} words`);
    console.log(`Expanded list: ${wordListExpanded.length} words`);
    console.log(`Concrete list: ${wordListConcrete.length} words`);

    console.log('\nBuilding indexes for filtered list...');
    const signatureIndex = buildLetterSignatureIndex(wordList);
    const firstLetterLengthIndex = buildFirstLetterLengthIndex(wordList);

    console.log('Building indexes for expanded list...');
    const signatureIndexExpanded = buildLetterSignatureIndex(wordListExpanded);
    const firstLetterLengthIndexExpanded = buildFirstLetterLengthIndex(wordListExpanded);

    console.log('Building indexes for concrete list...');
    const signatureIndexConcrete = buildLetterSignatureIndex(wordListConcrete);
    const firstLetterLengthIndexConcrete = buildFirstLetterLengthIndex(wordListConcrete);

    console.log('\nIndex statistics:');
    console.log(`  Signature index entries: ${Object.keys(signatureIndex).length} filtered / ${Object.keys(signatureIndexExpanded).length} expanded / ${Object.keys(signatureIndexConcrete).length} concrete`);
    console.log(`  First-letter index entries: ${Object.keys(firstLetterLengthIndex).length} filtered / ${Object.keys(firstLetterLengthIndexExpanded).length} expanded / ${Object.keys(firstLetterLengthIndexConcrete).length} concrete`);

    const jsContent = `// Comprehensive list of English nouns
// Source: The Great Noun List (desiquintans.com/nounlist) + NLTK WordNet

// Filtered list (concrete nouns only, ~${wordList.length} words)
const WORD_LIST = ${JSON.stringify(wordList, null, 2)};

// Original expanded list (~${wordListExpanded.length} words)
const WORD_LIST_EXPANDED = ${JSON.stringify(wordListExpanded, null, 2)};

// Massive concrete-only list (WordNet + curated, ~${wordListConcrete.length} words).
// Contains every English word whose primary WordNet sense is a physical
// object, living thing, substance, location, or body part. No abstract
// concepts, events, processes, states, qualities, times, or relations.
const WORD_LIST_CONCRETE = ${JSON.stringify(wordListConcrete, null, 2)};

// Convert arrays to sets for faster lookups
const WORD_SET = new Set(WORD_LIST);
const WORD_SET_EXPANDED = new Set(WORD_LIST_EXPANDED);
const WORD_SET_CONCRETE = new Set(WORD_LIST_CONCRETE);

// ============================================================================
// OPTIMIZED INDEXES
// ============================================================================

// Letter Signature Index - for exact anagram lookups (O(1) instead of O(n))
// Maps sorted letters to words with those letters
// Example: "abss" -> ["bass", "sabs"]
const SIGNATURE_INDEX = ${JSON.stringify(signatureIndex)};
const SIGNATURE_INDEX_EXPANDED = ${JSON.stringify(signatureIndexExpanded)};
const SIGNATURE_INDEX_CONCRETE = ${JSON.stringify(signatureIndexConcrete)};

// First Letter + Length Index - for fast combination search
// Maps first letter -> length -> words
// Example: {"b": {"4": ["bass", "ball", "bean", ...]}}
const FIRST_LETTER_LENGTH_INDEX = ${JSON.stringify(firstLetterLengthIndex)};
const FIRST_LETTER_LENGTH_INDEX_EXPANDED = ${JSON.stringify(firstLetterLengthIndexExpanded)};
const FIRST_LETTER_LENGTH_INDEX_CONCRETE = ${JSON.stringify(firstLetterLengthIndexConcrete)};

// ============================================================================
// DYNAMIC WORD LIST SWITCHING
// ============================================================================

// Supported list names: 'expanded', 'filtered', 'concrete'.
// Default to expanded (matches previous behavior).
let currentWordList = WORD_LIST_EXPANDED;
let currentWordSet = WORD_SET_EXPANDED;
let currentSignatureIndex = SIGNATURE_INDEX_EXPANDED;
let currentFirstLetterLengthIndex = FIRST_LETTER_LENGTH_INDEX_EXPANDED;

function setWordList(name) {
  if (name === 'concrete') {
    currentWordList = WORD_LIST_CONCRETE;
    currentWordSet = WORD_SET_CONCRETE;
    currentSignatureIndex = SIGNATURE_INDEX_CONCRETE;
    currentFirstLetterLengthIndex = FIRST_LETTER_LENGTH_INDEX_CONCRETE;
  } else if (name === 'filtered') {
    currentWordList = WORD_LIST;
    currentWordSet = WORD_SET;
    currentSignatureIndex = SIGNATURE_INDEX;
    currentFirstLetterLengthIndex = FIRST_LETTER_LENGTH_INDEX;
  } else {
    // default: expanded
    currentWordList = WORD_LIST_EXPANDED;
    currentWordSet = WORD_SET_EXPANDED;
    currentSignatureIndex = SIGNATURE_INDEX_EXPANDED;
    currentFirstLetterLengthIndex = FIRST_LETTER_LENGTH_INDEX_EXPANDED;
  }
}

// Back-compat shim: old callers used a boolean useExpandedWordList().
function useExpandedWordList(useExpanded) {
  setWordList(useExpanded ? 'expanded' : 'filtered');
}
`;

    fs.writeFileSync('words.js', jsContent);
    console.log('\nWrote words.js');
}

main();
