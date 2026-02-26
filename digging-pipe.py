"""
Digging Pipe — Multi-threaded SEO Optimizer for DiggingScriptures
=================================================================
Reads all MD articles across 5 content types, validates against
SEO-QC-GATES, auto-fixes what it can, and writes back.

Usage:
  python digging-pipe.py                 # optimize all
  python digging-pipe.py --slug NAME     # optimize one article
  python digging-pipe.py --dry-run       # show changes without writing
  python digging-pipe.py --diff          # show before/after diffs
  python digging-pipe.py --validate-only # just run validation, no writes
"""

import os, re, sys, json, yaml, argparse, io
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Force UTF-8 on Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_BASE = os.path.join(BASE_DIR, 'src', 'content')
SPEC_VERSION = '1.0.0'
SITE_URL = 'https://diggingscriptures.com'

CONTENT_TYPES = ['hubs', 'places', 'routes', 'stories', 'context']

# Expected Fragment slots per content type (layout-defined)
EXPECTED_SLOTS = {
    'hubs': [],  # hubs use default <slot />, plain markdown
    'places': ['history', 'culture', 'features', 'experience', 'related'],
    'routes': ['history', 'journey', 'places', 'modern', 'related'],
    'stories': ['narrative', 'context', 'legacy', 'related'],
    'context': [],  # context uses default slot + optional named slots
}

# Optional slots (present only when frontmatter flag is true)
CONDITIONAL_SLOTS = {
    'places': {'experience': 'hasExperienceSection'},
    'routes': {'modern': 'hasModernSection'},
}

# Required frontmatter fields per content type
REQUIRED_FM = {
    'hubs': ['title', 'description', 'draft'],
    'places': ['title', 'description', 'region', 'country', 'coordinates',
               'faithTraditions', 'placeType', 'parentHub', 'draft'],
    'routes': ['title', 'description', 'region', 'countries', 'distanceKm',
               'faithTraditions', 'difficulty', 'parentHub', 'draft'],
    'stories': ['title', 'description', 'storyType', 'faithTraditions',
                'timePeriod', 'draft'],
    'context': ['title', 'description', 'contextType', 'faithTraditions', 'draft'],
}

VALID_FAITH_TRADITIONS = [
    'Christianity', 'Islam', 'Judaism', 'Buddhism', 'Hinduism',
    'Jainism', 'Shinto', 'Sikhism',
    'Catholicism', 'Eastern Orthodoxy', 'Protestantism',
]

# Banned words/phrases (devotional language, AI-isms)
BANNED_WORDS = [
    'delve', 'realm', 'tapestry', 'furthermore', 'in conclusion',
    "it's important to note", "in today's world", 'unlock',
    'game-changer', 'dive in', 'landscape',  # when used metaphorically
    'embark on a journey', 'rich tapestry', 'nestled',
    'testament to', 'beacon of', 'bustling',
]

BANNED_REPLACEMENTS = {
    'delve': 'examine',
    'realm': 'domain',
    'tapestry': 'tradition',
    'furthermore': '',
    'in conclusion': '',
    "it's important to note": '',
    "in today's world": '',
    'unlock': 'access',
    'game-changer': 'significant development',
    'dive in': 'begin',
    'embark on a journey': 'set out',
    'rich tapestry': 'complex tradition',
    'nestled': 'located',
    'testament to': 'evidence of',
    'beacon of': 'center of',
    'bustling': 'busy',
}

FILLER_PHRASES = [
    "it's important to note", "it goes without saying",
    "at the end of the day", "in conclusion", "without further ado",
    "it should be noted", "needless to say", "as we all know",
    "the fact of the matter is", "at this point in time",
]

# Thread-safe print lock
print_lock = Lock()

# ============================================================
# UTILITIES
# ============================================================

def safe_print(*args, **kwargs):
    with print_lock:
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            text = ' '.join(str(a) for a in args)
            print(text.encode('ascii', 'replace').decode('ascii'), **kwargs)

def discover_articles():
    """Discover all articles across content types. Returns list of (ctype, slug, path)."""
    articles = []
    for ctype in CONTENT_TYPES:
        cdir = os.path.join(CONTENT_BASE, ctype)
        if not os.path.isdir(cdir):
            continue
        for fname in sorted(os.listdir(cdir)):
            if fname.endswith('.md'):
                slug = fname[:-3]
                path = os.path.join(cdir, fname)
                articles.append((ctype, slug, path))
    return articles

def load_md(path):
    """Load an MD file and return (fm_dict, fm_raw, body, raw)."""
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    m = re.match(r'^---\s*\n(.*?)\n---', raw, re.DOTALL)
    if not m:
        return {}, '', raw, raw
    fm_dict = yaml.safe_load(m.group(1)) or {}
    fm_raw = m.group(1)
    body = raw[m.end():]
    return fm_dict, fm_raw, body, raw

def save_md(path, fm_raw, body):
    """Write raw frontmatter string + body back to MD file."""
    out = f"---\n{fm_raw}\n---{body}"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)

def extract_prose(body):
    """Strip Fragment tags and HTML to get prose only."""
    text = re.sub(r'<Fragment[^>]*>', '', body)
    text = re.sub(r'</Fragment>', '', text)
    text = re.sub(r'<[^>]+/?>', '', text)
    return text

def count_words(body):
    """Count words in article body."""
    clean = extract_prose(body)
    clean = re.sub(r'[#*|`\[\]()-]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return len(clean.split())

def extract_fragment_slots(body):
    """Extract list of Fragment slot names used in the body."""
    return re.findall(r'<Fragment\s+slot="([^"]+)"', body)

def extract_internal_links(body):
    """Extract internal link targets from markdown links."""
    patterns = [
        r'\]\(/([^)"\'\s]+)',       # [text](/path)
        r'href="/([^"]+)"',         # href="/path"
    ]
    links = []
    for p in patterns:
        links.extend(re.findall(p, body))
    slugs = set()
    for link in links:
        link = link.rstrip('/').split('#')[0].split('?')[0]
        parts = link.split('/')
        if len(parts) >= 2:
            slug = parts[-1]
            if slug and not slug.startswith('.'):
                slugs.add(slug)
    return slugs

# ============================================================
# FIX PASSES
# ============================================================

def fix_frontmatter(fm_raw, fm, ctype, slug):
    """Fix frontmatter issues via surgical text edits on fm_raw."""
    changes = []
    # Ensure lastUpdated
    if 'lastUpdated' not in fm:
        today = datetime.now().strftime('%Y-%m-%d')
        fm_raw = fm_raw.rstrip() + f'\nlastUpdated: {today}'
        changes.append(f'+ lastUpdated: {today}')

    # Ensure draft: false
    if fm.get('draft') is True:
        fm_raw = fm_raw.replace('draft: true', 'draft: false')
        changes.append('~ draft: true -> false')

    # Ensure parentHub for spoke types
    if ctype in ('places', 'routes') and 'parentHub' not in fm:
        fm_raw = fm_raw.rstrip() + '\nparentHub: "faith-based-journeys"'
        changes.append('+ parentHub: faith-based-journeys (default)')

    return fm_raw, fm, changes

def fix_title_length(fm_raw, fm):
    """Warn if title > 65 chars (SEO best practice)."""
    changes = []
    title = fm.get('title', '').strip()
    if len(title) > 65:
        # Truncate at word boundary
        truncated = title[:62]
        last_space = truncated.rfind(' ')
        if last_space > 40:
            truncated = truncated[:last_space]
        new_title = truncated.rstrip() + '...'
        fm_raw = fm_raw.replace(title, new_title, 1)
        changes.append(f'~ title: {len(title)}c -> {len(new_title)}c')
    return fm_raw, fm, changes

def fix_description_length(fm_raw, fm):
    """Truncate description to 155 chars if over limit."""
    changes = []
    desc = fm.get('description', '').strip()
    if len(desc) > 160:
        truncated = desc[:157]
        last_space = truncated.rfind(' ')
        if last_space > 100:
            truncated = truncated[:last_space]
        new_desc = truncated.rstrip() + '...'
        fm_raw = fm_raw.replace(desc, new_desc, 1)
        changes.append(f'~ description: {len(desc)}c -> {len(new_desc)}c')
    return fm_raw, fm, changes

def fix_banned_words(body):
    """Remove/replace banned words from prose (not Fragment tags)."""
    changes = []
    lines = body.split('\n')
    fixed_lines = []
    fixes = 0

    for line in lines:
        stripped = line.strip()
        # Skip Fragment tags and HTML
        if stripped.startswith('<Fragment') or stripped.startswith('</Fragment'):
            fixed_lines.append(line)
            continue

        modified = line
        line_lower = modified.lower()

        for banned in BANNED_WORDS:
            if banned in line_lower:
                replacement = BANNED_REPLACEMENTS.get(banned, '')
                pattern = re.escape(banned)
                modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
                fixes += 1

        modified = re.sub(r'  +', ' ', modified)
        modified = re.sub(r'^\s*,\s*', '', modified)
        fixed_lines.append(modified)

    if fixes:
        changes.append(f'~ removed {fixes} banned word(s)')
    return '\n'.join(fixed_lines), changes

def fix_filler_phrases(body):
    """Remove filler phrases from prose."""
    changes = []
    lines = body.split('\n')
    fixed_lines = []
    fixes = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('<Fragment') or stripped.startswith('</Fragment'):
            fixed_lines.append(line)
            continue

        modified = line
        for filler in FILLER_PHRASES:
            if filler in modified.lower():
                pattern = re.escape(filler)
                modified = re.sub(r',?\s*' + pattern + r'\s*,?\s*', ' ',
                                  modified, flags=re.IGNORECASE)
                fixes += 1

        modified = re.sub(r'  +', ' ', modified)
        fixed_lines.append(modified)

    if fixes:
        changes.append(f'~ removed {fixes} filler phrase(s)')
    return '\n'.join(fixed_lines), changes

def fix_heading_whitespace(body):
    """Normalize heading whitespace."""
    changes = []
    fixed, count = re.subn(r'^[ \t]+(#{1,6} )', r'\1', body, flags=re.MULTILINE)
    if count:
        changes.append(f'~ fixed {count} heading(s) with leading whitespace')
    return fixed, changes

def fix_trailing_whitespace(body):
    """Remove trailing whitespace from lines."""
    changes = []
    fixed, count = re.subn(r'[ \t]+$', '', body, flags=re.MULTILINE)
    if count:
        changes.append(f'~ trimmed trailing whitespace ({count} lines)')
    return fixed, changes

# ============================================================
# VALIDATION (read-only checks)
# ============================================================

def validate_article(ctype, slug, fm, body, all_slugs):
    """Run validation checks, return (blocks, warns)."""
    blocks = []
    warns = []
    word_count = count_words(body)
    slots_used = extract_fragment_slots(body)
    internal_links = extract_internal_links(body)

    # --- Frontmatter checks ---
    title = fm.get('title', '').strip()
    if len(title) > 65:
        warns.append(f'Title long: {len(title)}c (target ≤65)')
    elif len(title) < 3:
        blocks.append(f'Title too short: {len(title)}c (min 3)')

    desc = fm.get('description', '').strip()
    if len(desc) > 160:
        warns.append(f'Description long: {len(desc)}c (target ≤160)')
    elif len(desc) < 50:
        warns.append(f'Description short: {len(desc)}c (target ≥50)')

    # Required fields
    for field in REQUIRED_FM.get(ctype, []):
        if field not in fm:
            blocks.append(f'Missing frontmatter: {field}')

    # Faith traditions validation (not required for hubs)
    traditions = fm.get('faithTraditions', [])
    if not traditions and ctype != 'hubs':
        blocks.append('Empty faithTraditions')
    for t in traditions:
        if t not in VALID_FAITH_TRADITIONS:
            warns.append(f"Unknown tradition: '{t}'")

    # --- Word count checks ---
    min_words = {
        'hubs': 1500, 'places': 1000, 'routes': 1000,
        'stories': 800, 'context': 800,
    }
    if word_count < min_words.get(ctype, 800):
        blocks.append(f'Thin content: {word_count}w (min {min_words[ctype]})')

    # --- Slot validation ---
    expected = set(EXPECTED_SLOTS.get(ctype, []))
    conditional = set(CONDITIONAL_SLOTS.get(ctype, []))
    slots_set = set(slots_used) if not isinstance(slots_used, set) else slots_used
    if expected:
        missing = expected - slots_set - conditional
        extra = slots_set - expected - conditional
        if missing:
            blocks.append(f'Missing slots: {", ".join(sorted(missing))}')
        if extra:
            warns.append(f'Unexpected slots: {", ".join(sorted(extra))}')
    elif ctype == 'hubs' and slots_set:
        warns.append(f'Hub should use plain markdown, found slots: {", ".join(sorted(slots_used))}')

    # --- Internal links ---
    for link in internal_links:
        parts = link.strip('/').split('/')
        if len(parts) >= 2:
            link_slug = parts[-1]
            link_ctype = parts[-2] if len(parts) >= 2 else ''
            if link_slug not in all_slugs:
                warns.append(f'Broken link: /{link}')

    # --- Banned words in body ---
    prose = extract_prose(body).lower()
    for word in BANNED_WORDS:
        if word.lower() in prose:
            warns.append(f'Banned word in body: "{word}"')

    # --- Heading checks ---
    h1_matches = re.findall(r'^# ', body, re.MULTILINE)
    if len(h1_matches) > 1:
        warns.append(f'Multiple H1 headings: {len(h1_matches)}')

    # --- Description in frontmatter ---
    if 'description' not in fm:
        blocks.append('Missing meta description')

    return blocks, warns


# ============================================================
# OPTIMIZE (orchestrates fix passes + validation)
# ============================================================

def optimize_article(ctype, slug, filepath, all_slugs, dry_run=False):
    """Run all fix passes then validate a single article.
    Returns dict with path, status, changes, blocks, warns."""
    result = {
        'path': str(filepath),
        'status': 'ok',
        'changes': [],
        'blocks': [],
        'warns': [],
    }

    fm, fm_raw, body, _raw = load_md(filepath)
    if not fm_raw and not fm:
        result['status'] = 'error'
        result['blocks'].append('Failed to parse frontmatter')
        return result

    original_fm = fm_raw
    original_body = body
    changes = []

    # --- Run fix passes on frontmatter ---
    fm_raw, fm, c = fix_frontmatter(fm_raw, fm, ctype, slug)
    changes.extend(c)

    fm_raw, fm, c = fix_title_length(fm_raw, fm)
    changes.extend(c)

    fm_raw, fm, c = fix_description_length(fm_raw, fm)
    changes.extend(c)

    # --- Run fix passes on body ---
    body, c = fix_banned_words(body)
    changes.extend(c)

    body, c = fix_filler_phrases(body)
    changes.extend(c)

    body, c = fix_heading_whitespace(body)
    changes.extend(c)

    body, c = fix_trailing_whitespace(body)
    changes.extend(c)

    # --- Save if changed ---
    if not dry_run and (fm_raw != original_fm or body != original_body):
        save_md(filepath, fm_raw, body)

    # --- Validate ---
    blocks, warns = validate_article(ctype, slug, fm, body, all_slugs)

    result['changes'] = changes
    result['blocks'] = blocks
    result['warns'] = warns
    if blocks:
        result['status'] = 'blocked'
    elif warns:
        result['status'] = 'warn'

    return result


# ============================================================
# PIPELINE RUNNER
# ============================================================

def run_pipeline(dry_run=False, workers=6):
    """Discover all articles, optimize in parallel, print summary."""
    safe_print('=' * 60)
    safe_print('DiggingScriptures SEO Pipeline')
    safe_print('=' * 60)

    if dry_run:
        safe_print('[DRY RUN] No files will be modified.\n')

    articles = discover_articles()
    if not articles:
        safe_print('No articles found. Check CONTENT_BASE path.')
        return

    # Build slug index for cross-link validation
    all_slugs = {slug for (_, slug, _) in articles}

    safe_print(f'Found {len(articles)} articles across {len(CONTENT_TYPES)} content types.\n')

    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(optimize_article, ctype, slug, path, all_slugs, dry_run): (ctype, slug, path)
            for (ctype, slug, path) in articles
        }
        for future in as_completed(futures):
            (ctype, slug, path) = futures[future]
            try:
                r = future.result()
                results.append(r)
            except Exception as exc:
                safe_print(f'  ERROR {slug}: {exc}')
                results.append({
                    'path': path, 'status': 'error',
                    'changes': [], 'blocks': [str(exc)], 'warns': [],
                })

    # --- Summary ---
    safe_print('\n' + '=' * 60)
    safe_print('PIPELINE SUMMARY')
    safe_print('=' * 60)

    ok = [r for r in results if r['status'] == 'ok']
    warned = [r for r in results if r['status'] == 'warn']
    blocked = [r for r in results if r['status'] == 'blocked']
    errored = [r for r in results if r['status'] == 'error']

    total_changes = sum(len(r['changes']) for r in results)
    safe_print(f'\n  Total articles: {len(results)}')
    safe_print(f'  ✓ OK:      {len(ok)}')
    safe_print(f'  ⚠ Warned:  {len(warned)}')
    safe_print(f'  ✗ Blocked: {len(blocked)}')
    safe_print(f'  ☠ Errors:  {len(errored)}')
    safe_print(f'  Fixes applied: {total_changes}')

    if warned:
        safe_print('\n--- WARNINGS ---')
        for r in sorted(warned, key=lambda x: x['path']):
            name = Path(r['path']).name
            safe_print(f'  {name}:')
            for w in r['warns']:
                safe_print(f'    ⚠ {w}')
            for c in r['changes']:
                safe_print(f'    ~ {c}')

    if blocked:
        safe_print('\n--- BLOCKERS ---')
        for r in sorted(blocked, key=lambda x: x['path']):
            name = Path(r['path']).name
            safe_print(f'  {name}:')
            for b in r['blocks']:
                safe_print(f'    ✗ {b}')
            for w in r['warns']:
                safe_print(f'    ⚠ {w}')

    if errored:
        safe_print('\n--- ERRORS ---')
        for r in sorted(errored, key=lambda x: x['path']):
            name = Path(r['path']).name
            safe_print(f'  {name}:')
            for b in r['blocks']:
                safe_print(f'    ☠ {b}')

    # --- Audit log ---
    log_path = os.path.join(BASE_DIR, 'digging-audit.jsonl')
    with open(log_path, 'w', encoding='utf-8') as f:
        for r in sorted(results, key=lambda x: x['path']):
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    safe_print(f'\nAudit log: {log_path}')

    if blocked or errored:
        safe_print('\n⚠ Pipeline finished with issues. Review blockers above.')
        return 1
    safe_print('\n✓ Pipeline complete — all articles passed.')
    return 0


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='DiggingScriptures SEO optimizer pipeline'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Validate only — do not modify files',
    )
    parser.add_argument(
        '--workers', type=int, default=6,
        help='Thread pool size (default: 6)',
    )
    args = parser.parse_args()
    code = run_pipeline(dry_run=args.dry_run, workers=args.workers)
    sys.exit(code or 0)
