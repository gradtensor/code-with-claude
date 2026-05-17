# Budget 2026 fixture

The Union Budget 2026-27 speech delivered by the Finance Minister of India. Publicly available document, used as the recurring exercise input across the series.

## Files

- `budget_speech.docx` - the original document, as released by the Ministry of Finance.
- `budget_speech.txt` - a clean plain-text extraction of the same content. Regenerated when the .docx changes. See the "Regenerating" section below.

## Why this document

The capstone uses two kinds of input:

- `capstone/v1-prompt/sample_input.txt` - a short synthetic business memo. Designed to be small, controllable, and easy to reason about while teaching.
- `fixtures/budget-2026/budget_speech.txt` - a real, long, mixed-register government document. Designed to stress the analyst with the kind of content it would actually face in production.

The Budget speech is the harder of the two. It mixes prose with itemised lists, includes named schemes and allocations across many domains (agriculture, infrastructure, taxation, social welfare), and uses Indian fiscal vocabulary that may not appear in the model's most-frequent vocabulary. Surfacing entities, key points, and risks from this document is a meaningfully different task from doing so on the synthetic memo.

Each day's exercises will use this fixture to demonstrate the day's new capability on a real-world input.

## Framing rule

When using this fixture in exercises, posts, or training material:

**Extract and analyse what the source says. Do not editorialise about whether the Budget is good policy.**

The analyst's job is to surface what the document contains: announcements, allocations, named schemes, stated objectives, and items the document itself flags as risks or constraints. The analyst's job is not to evaluate fiscal policy, take a position on the government, or comment on whether announced measures will succeed.

This is a teaching point, not a political stance. Treating a real public document as raw input - and grounding every output in what the document actually says - is the same discipline the analyst should apply to a corporate report, a vendor contract, or a regulatory filing. Models that drift into opinion when handed political content are a liability in production. Practising the discipline on a politically charged document makes the discipline stick.

If a workshop participant produces an output that includes value judgements about the Budget, that is a finding worth discussing: it is the model failing the grounding test, and the fix is in the prompt, not in the choice of document.

## Regenerating budget_speech.txt

The .txt file is a derived artefact. Regenerate it whenever the .docx changes. Three steps: install the tool, extract, verify. The extraction should be clean: paragraphs preserved with blank lines between them, list items flattened to plain text prefixed with `-`, all Word-bold and italic markup stripped, and no XML residue.

Run all commands from the repo root.

### Step 1: Install pandoc (one-time)

**macOS:**

```
brew install pandoc
```

**Ubuntu or Debian:**

```
sudo apt install pandoc
```

**Other platforms:** see https://pandoc.org/installing.html

Verify the install:

```
pandoc --version
```

Version 3.0 or later is recommended. If pandoc is unavailable in your environment, see "Without pandoc" at the end of this section.

### Step 2: Extract .docx to .txt

```
pandoc -f docx -t plain --wrap=preserve \
  fixtures/budget-2026/budget_speech.docx \
  -o fixtures/budget-2026/budget_speech.txt
```

Pandoc emits list items prefixed with `*`. Normalise them to `-` to match the convention used elsewhere in the repo:

```
sed -i '' 's/^\* /- /' fixtures/budget-2026/budget_speech.txt
```

On Linux, drop the empty `''` after `-i`:

```
sed -i 's/^\* /- /' fixtures/budget-2026/budget_speech.txt
```

### Step 3: Verify the extraction

Copy and paste the entire block below into a terminal. It runs five checks and reports OK or FAIL for each:

```
F=fixtures/budget-2026/budget_speech.txt

echo "1. Header present"
head -7 "$F" | grep -qE "Budget|Sitharaman|February" && echo "   OK" || echo "   FAIL: speech header missing"

echo "2. Paragraph separation"
B=$(awk 'NF==0{c++} END{print c+0}' "$F")
[ "$B" -ge 200 ] && echo "   OK ($B blank lines)" || echo "   FAIL ($B blank lines, expected 200+)"

echo "3. List items prefixed with '- '"
L=$(grep -c "^- " "$F")
[ "$L" -ge 20 ] && echo "   OK ($L list items)" || echo "   FAIL ($L list items, expected 20+)"

echo "4. No XML residue"
grep -qE '<w:|</w:|<\?xml' "$F" && echo "   FAIL: XML residue found" || echo "   OK"

echo "5. No paired Word-bold markup"
BOLD=$(grep -nE '\*\*[^*[:space:]][^*]*[^*[:space:]]\*\*' "$F" | head -5)
[ -z "$BOLD" ] && echo "   OK" || { echo "   FAIL: paired **bold** patterns found:"; echo "$BOLD"; }
```

**What each check covers:**

1. Speech metadata at the top survived the extraction.
2. Paragraphs are separated, not run together.
3. Itemised announcements rendered as plain-text list items.
4. Pandoc did not leak Word's internal XML into the output.
5. No `**bold**` markup leaked through. **Lone trailing or leading asterisks (e.g. `modules**`, `***effective`) are footnote markers from the original Budget document and are preserved deliberately.** The check ignores these by matching only paired `**...**` patterns.

If every check prints OK, the extraction is good. Commit both files.

### Without pandoc

If pandoc cannot be installed, use `python-docx` ephemerally through `uv`. This does not add `python-docx` as a project dependency:

```
uv run --with python-docx python -c "
from docx import Document
doc = Document('fixtures/budget-2026/budget_speech.docx')
out = []
for p in doc.paragraphs:
    text = p.text.strip()
    if not text:
        out.append('')
        continue
    style = (p.style.name or '').lower()
    if 'list' in style or 'bullet' in style:
        out.append('- ' + text)
    else:
        out.append(text)
print('\n'.join(out))
" > fixtures/budget-2026/budget_speech.txt
```

Then run the verification script from Step 3 above. Note that python-docx does not extract tables or images, so the output will be slightly less complete than the pandoc version.

## Source

The .docx is the publicly released speech document from the Ministry of Finance. Treat it as a snapshot of the version that landed in this repository; if the ministry republishes a revised speech, update the .docx and regenerate the .txt.
