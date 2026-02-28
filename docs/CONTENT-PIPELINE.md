
# Hub Content Pipeline — Iterative Draft System

## Philosophy

Hub content is the SEO backbone of the site. It cannot be generated in a single pass.
Each hub goes through 5 layers, each producing a verifiable artifact:

```
L1  FRAMEWORK    →  section skeleton with targets     (JSON spec)
L2  SCHEMA       →  frontmatter + structure validated  (Astro build pass)
L3  HYDRATION    →  prose expanded per-section         (markdown draft)
L4  QC / SEO     →  automated quality gates            (pass/fail report)
L5  CORRECTION   →  targeted fixes from L4 failures    (final markdown)
```

No layer can run until the previous layer's output is verified.

---

## L1: FRAMEWORK

**Input:** Hub slug, spoke inventory, Viator product data
**Output:** `_pipeline/{slug}.framework.json`

Defines:
- Target total word count (2,000 minimum for hubs)
- H2 section list with:
  - heading text
  - target word count (250-400 per section)
  - editorial angle (what this section argues/covers)
  - required spoke links (which articles MUST be linked here)
- Required internal link inventory (all spokes + parent hubs)
- Viator product placements (which section, how many)

**Verification:** JSON schema validation. Every spoke in frontmatter must appear
in at least one section's `required_links`.

---

## L2: SCHEMA

**Input:** Framework JSON
**Output:** Frontmatter-only markdown file committed to `src/content/cities/{slug}.md`

Validates:
- Astro collection schema compliance (title ≤ 80, description ≤ 160, etc.)
- All spoke references resolve to existing collection entries
- Viator destination ID matches API lookup
- Image file exists on disk

**Verification:** `npx astro build` succeeds with the stub file.

---

## L3: HYDRATION

**Input:** Framework JSON + schema-validated stub
**Output:** Full prose draft in markdown

Rules:
- Write ONE section at a time
- Each section must hit its target word count (±10%)
- Every spoke link in the framework must appear as a contextual in-prose link
  (not a list, not a "see also" — woven into a sentence)
- No section can repeat factual claims from another section
- Intro (no H2) must establish the hub's unique angle
- Final section must naturally transition to the Viator experiences block
- Prose must be original, not paraphrased from spoke articles

**Verification:** Per-section word count check against framework targets.

---

## L4: QC / SEO

Automated quality gates. Each check produces PASS or FAIL:

### Content Quality
- [ ] Total words ≥ 2,000
- [ ] Every H2 section ≥ 200 words
- [ ] No H2 section > 500 words (split if over)
- [ ] Flesch-Kincaid readability 40-65 (educated general audience)
- [ ] No sentence > 45 words
- [ ] No paragraph > 150 words
- [ ] No duplicate H2 headings

### Internal Linking
- [ ] Every spoke in frontmatter linked in prose body
- [ ] Every link target exists (no broken links)
- [ ] Hub links to parent tradition hub (cross-silo)
- [ ] Hub links to ≥ 2 sibling city hubs
- [ ] No orphan links (all href targets resolve)

### SEO
- [ ] Title tag ≤ 80 chars, contains primary keyword
- [ ] Meta description ≤ 160 chars, contains primary keyword
- [ ] H1 matches title (rendered by layout)
- [ ] H2s contain secondary keywords
- [ ] Primary keyword in first 100 words of body
- [ ] Image has descriptive alt text (5+ words)
- [ ] No keyword stuffing (primary keyword density < 3%)

### Viator Integration
- [ ] Experiences section present
- [ ] ≥ 3 products with affiliate tracking URLs
- [ ] Product URLs contain pid=P00166886
- [ ] "Browse all" link present

### Structural Integrity
- [ ] Frontmatter valid against Astro schema
- [ ] `npx astro build` succeeds
- [ ] Page reachable from homepage (crawl test)
- [ ] Sibling nav renders with ≥ 4 siblings

---

## L5: CORRECTION

**Input:** QC report with specific failures
**Output:** Targeted edits to fix each failure

Rules:
- Fix ONLY what failed — don't rewrite passing sections
- Re-run L4 after each correction pass
- Maximum 3 correction passes before manual review
- Log all changes with before/after word counts

---

## Running the Pipeline

```bash
# Full pipeline for one hub:
python3 scripts/content-pipeline.py jerusalem --all

# Individual layers:
python3 scripts/content-pipeline.py jerusalem --framework
python3 scripts/content-pipeline.py jerusalem --schema
python3 scripts/content-pipeline.py jerusalem --hydrate
python3 scripts/content-pipeline.py jerusalem --qc
python3 scripts/content-pipeline.py jerusalem --correct

# QC-only pass on all hubs:
python3 scripts/content-pipeline.py --all --qc
```
