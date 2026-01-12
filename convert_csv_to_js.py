
import csv
import json
import os

csv_path = '/Users/noahrayburn/DuoTang/CuratedWords.csv'
js_path = '/Users/noahrayburn/DuoTang/curated_words.js'

words = []
try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        # It seems the CSV is just a list of words, one per line.
        # Checking for header? The first line looked like 'man', so probably no header.
        # But I should double check if it's actually CSV or just text.
        # The file content showed just words.
        for line in f:
            word = line.strip()
            if word:
                words.append(word)

    # Dedup and sort just in case, though the file seemed sorted-ish or grouped.
    # Actually, let's keep original order if possible, or just alphabetical?
    # The existing generator logic might rely on randomness so order doesn't strictly matter.
    # But let's just keep them as is to be safe.
    
    # Write to JS
    js_content = f"const CURATED_COMMON_NOUNS = {json.dumps(words, indent=4)};\n"
    
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Successfully converted {len(words)} words to {js_path}")

except Exception as e:
    print(f"Error: {e}")
