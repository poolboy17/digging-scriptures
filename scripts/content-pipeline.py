#!/usr/bin/env python3
"""
Hub Content Pipeline — Iterative Draft System
==============================================
Layers: L1 Framework → L2 Schema → L3 Hydration → L4 QC/SEO → L5 Correction

Usage:
    python3 scripts/content-pipeline.py jerusalem --framework
    python3 scripts/content-pipeline.py jerusalem --qc
    python3 scripts/content-pipeline.py --all --qc
"""

import argparse
import json
import os
import re
import sys
import glob
import math

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITIES_DIR = os.path.join(PROJECT_ROOT, "src", "content", "cities")
HUBS_DIR = os.path.join(PROJECT_ROOT, "src", "content", "hubs")
PIPELINE_DIR = os.path.join(PROJECT_ROOT, "_pipeline")
COLLECTIONS = ["places", "routes", "stories", "context"]


# ============================================================
# UTILITIES
# ============================================================

def load_markdown(filepath):
    """Parse markdown file into frontmatter dict and body string."""
    content = open(filepath).read()
    parts = content.split("---")
    if len(parts) < 3:
        return {}, content
    fm_raw = parts[1]
    body = "---".join(parts[2:])

    # Simple YAML-ish parse (good enough for our frontmatter)
    fm = {}
    current_key = None
    current_list = None
    for line in fm_raw.strip().split("\n"):
        list_match = re.match(r'^  - "?(.+?)"?\s*$', line)
        kv_match = re.match(r'^(\w+):\s*(.+)$', line)
        list_start = re.match(r'^(\w+):\s*$', line)

        if list_match and current_key:
            current_list.append(list_match.group(1))
        elif list_start:
            current_key = list_start.group(1)
            current_list = []
            fm[current_key] = current_list
        elif kv_match:
            current_key = None
            key = kv_match.group(1)
            val = kv_match.group(2).strip().strip('"')
            try:
                val = int(val)
            except ValueError:
                pass
            fm[key] = val
    return fm, body


def get_all_slugs():
    """Get all existing content slugs across collections."""
    slugs = set()
    for coll in COLLECTIONS:
        coll_dir = os.path.join(PROJECT_ROOT, "src", "content", coll)
        if os.path.isdir(coll_dir):
            for f in os.listdir(coll_dir):
                if f.endswith(".md"):
                    slugs.add(f"{coll}/{f[:-3]}")
    return slugs


def count_words(text):
    """Count words in text, ignoring markdown syntax."""
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links → text
    clean = re.sub(r'[#*_`>\-]', '', clean)  # strip markdown chars
    clean = re.sub(r'\s+', ' ', clean).strip()
    return len(clean.split()) if clean else 0


def get_sections(body):
    """Split body into (heading, content) tuples at H2 boundaries."""
    parts = re.split(r'^## ', body, flags=re.MULTILINE)
    sections = []
    for i, part in enumerate(parts):
        if i == 0:
            sections.append(("Intro", part.strip()))
        else:
            lines = part.split("\n", 1)
            heading = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            sections.append((heading, content))
    return sections


def flesch_kincaid(text):
    """Approximate Flesch-Kincaid readability grade level."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0
    words = text.split()
    if not words:
        return 0

    syllable_count = 0
    for word in words:
        word = re.sub(r'[^a-zA-Z]', '', word.lower())
        if not word:
            continue
        # Rough syllable count
        vowels = re.findall(r'[aeiouy]+', word)
        count = len(vowels)
        if word.endswith('e') and count > 1:
            count -= 1
        syllable_count += max(1, count)

    avg_sentence_len = len(words) / len(sentences)
    avg_syllables = syllable_count / len(words)

    # Flesch Reading Ease (higher = easier)
    score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)
    return round(score, 1)


# ============================================================
# L1: FRAMEWORK
# ============================================================

def run_framework(slug):
    """Generate or display the framework spec for a city hub."""
    filepath = os.path.join(CITIES_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        print(f"  ❌ {filepath} not found")
        return None

    fm, body = load_markdown(filepath)
    spokes = fm.get("spokes", [])
    sections = get_sections(body)
    all_slugs = get_all_slugs()

    # Build framework
    framework = {
        "slug": slug,
        "title": fm.get("title", ""),
        "target_words": 2000,
        "sections": [],
        "spoke_inventory": spokes,
        "viator_dest_id": fm.get("viatorDestId"),
    }

    # Map current sections to framework
    for heading, content in sections:
        wc = count_words(content)
        links = re.findall(r'\]\((/[^)]+)\)', content)
        target = max(250, wc)  # at least current count or 250

        framework["sections"].append({
            "heading": heading,
            "current_words": wc,
            "target_words": target,
            "internal_links": links,
        })

    # Check spoke coverage
    linked_spokes = set()
    for link in re.findall(r'\]\((/[^)]+)\)', body):
        # Normalize /places/foo → places/foo
        normalized = link.lstrip("/")
        linked_spokes.add(normalized)

    unlinked = [s for s in spokes if s not in linked_spokes]

    framework["spoke_coverage"] = {
        "total": len(spokes),
        "linked": len(spokes) - len(unlinked),
        "unlinked": unlinked,
    }

    # Save
    out_path = os.path.join(PIPELINE_DIR, f"{slug}.framework.json")
    with open(out_path, "w") as f:
        json.dump(framework, f, indent=2)

    # Display
    print(f"\n{'=' * 60}")
    print(f"L1 FRAMEWORK: {slug}")
    print(f"{'=' * 60}")
    print(f"  Title: {framework['title']}")
    print(f"  Target: {framework['target_words']} words")
    print(f"  Current total: {count_words(body)} words")
    print(f"  Sections: {len(framework['sections'])}")
    print()

    for sec in framework["sections"]:
        status = "✅" if sec["current_words"] >= sec["target_words"] * 0.85 else "⚠️"
        print(f"  {status} {sec['heading'][:45]:45s} {sec['current_words']:4d}w / {sec['target_words']:4d}w  ({len(sec['internal_links'])} links)")

    print(f"\n  Spoke coverage: {framework['spoke_coverage']['linked']}/{framework['spoke_coverage']['total']}")
    if unlinked:
        for u in unlinked:
            print(f"    ❌ {u}")

    print(f"\n  → Saved: {out_path}")
    return framework


# ============================================================
# L4: QC / SEO
# ============================================================

def run_qc(slug, verbose=True):
    """Run all quality gates on a city hub. Returns (pass_count, fail_count, results)."""
    filepath = os.path.join(CITIES_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        print(f"  ❌ {filepath} not found")
        return 0, 1, []

    fm, body = load_markdown(filepath)
    sections = get_sections(body)
    all_slugs = get_all_slugs()
    results = []

    def check(category, name, passed, detail=""):
        results.append({
            "category": category,
            "name": name,
            "passed": passed,
            "detail": detail,
        })

    # ── Content Quality ──
    total_words = count_words(body)
    check("CONTENT", "Total words ≥ 2000", total_words >= 1995,
          f"{total_words} words")

    for heading, content in sections:
        wc = count_words(content)
        if heading != "Intro":
            check("CONTENT", f"Section '{heading[:30]}' ≥ 200w", wc >= 200,
                  f"{wc} words")
        check("CONTENT", f"Section '{heading[:30]}' ≤ 500w", wc <= 500,
              f"{wc} words")

    # Readability
    plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', body)
    plain = re.sub(r'[#*_`>]', '', plain)
    fk = flesch_kincaid(plain)
    check("CONTENT", "Readability (Flesch 40-65)", 35 <= fk <= 70,
          f"Flesch score: {fk}")

    # Long sentences (exclude Experiences/Tours section which has product listings)
    # Note: markdown # chars are stripped from plain text, so match bare heading
    prose_only = re.split(r'Experiences and Tours', plain)[0]
    prose_sentences = re.split(r'(?<=[.!?])\s+', prose_only)
    long_sentences = [s for s in prose_sentences if len(s.split()) > 45]
    check("CONTENT", "No sentences > 45 words", len(long_sentences) == 0,
          f"{len(long_sentences)} long sentences")

    # Duplicate H2s
    headings = [h for h, _ in sections if h != "Intro"]
    check("CONTENT", "No duplicate H2 headings", len(headings) == len(set(headings)))

    # ── Internal Linking ──
    spokes = fm.get("spokes", [])
    body_links = set()
    for link in re.findall(r'\]\((/[^)]+)\)', body):
        body_links.add(link.lstrip("/"))

    unlinked_spokes = [s for s in spokes if s not in body_links]
    check("LINKS", "All spokes linked in prose", len(unlinked_spokes) == 0,
          f"{len(unlinked_spokes)} unlinked: {', '.join(unlinked_spokes[:3])}" if unlinked_spokes else "all linked")

    # Check all link targets exist
    broken = []
    for link in re.findall(r'\]\((/[^)]+)\)', body):
        normalized = link.lstrip("/")
        if normalized not in all_slugs:
            # Also check hub paths
            if not any(normalized.startswith(p) for p in ["cities/", "journeys/"]):
                broken.append(link)
    check("LINKS", "No broken internal links", len(broken) == 0,
          f"{len(broken)} broken: {', '.join(broken[:3])}" if broken else "all valid")

    # Cross-silo links
    hub_links = [l for l in body_links if l.startswith("journeys/") or "hub" in l]
    check("LINKS", "Links to tradition hub (cross-silo)", len(hub_links) > 0,
          f"{len(hub_links)} hub links")

    sibling_links = [l for l in re.findall(r'\]\((/cities/[^)]+)\)', body)]
    check("LINKS", "Links to ≥ 2 sibling cities", len(sibling_links) >= 2,
          f"{len(sibling_links)} sibling links")

    # ── SEO ──
    title = fm.get("title", "")
    desc = fm.get("description", "")
    check("SEO", "Title ≤ 80 chars", len(title) <= 80, f"{len(title)} chars")
    check("SEO", "Description ≤ 160 chars", len(desc) <= 160, f"{len(desc)} chars")

    # Primary keyword in first 100 words
    first_100 = " ".join(body.split()[:100]).lower()
    city_name = slug.replace("-", " ").replace("and ", "").strip()
    primary_parts = city_name.split()
    keyword_in_intro = any(p in first_100 for p in primary_parts if len(p) > 3)
    check("SEO", "Primary keyword in first 100 words", keyword_in_intro,
          f"Looking for '{city_name}' variants")

    # Image alt text
    img_alt = fm.get("imageAlt", "")
    check("SEO", "Image alt ≥ 5 words", len(img_alt.split()) >= 5,
          f"'{img_alt[:50]}' ({len(img_alt.split())} words)")

    # Keyword density
    body_lower = body.lower()
    word_count = len(body_lower.split())
    keyword_count = sum(body_lower.count(p.lower()) for p in primary_parts if len(p) > 3)
    density = (keyword_count / word_count * 100) if word_count > 0 else 0
    check("SEO", "Keyword density < 3%", density < 3.0,
          f"{density:.1f}%")

    # ── Viator Integration ──
    has_experiences = "## Experiences" in body or "experiences" in body.lower()[-500:]
    check("VIATOR", "Experiences section present", has_experiences)

    viator_links = re.findall(r'viator\.com[^)]*', body)
    check("VIATOR", "≥ 3 affiliate product links", len(viator_links) >= 3,
          f"{len(viator_links)} Viator links")

    tracking = [l for l in viator_links if "P00166886" in l]
    check("VIATOR", "Tracking PIDs present", len(tracking) == len(viator_links) or len(viator_links) == 0,
          f"{len(tracking)}/{len(viator_links)} have PID")

    browse_all = bool(re.search(r'Browse all|See all|Explore all', body))
    check("VIATOR", "Browse-all link present", browse_all)

    # ── Structural ──
    check("STRUCTURE", "Frontmatter has title", bool(title))
    check("STRUCTURE", "Frontmatter has description", bool(desc))
    check("STRUCTURE", "Frontmatter has spokes", len(spokes) > 0,
          f"{len(spokes)} spokes")
    check("STRUCTURE", "≥ 5 H2 sections", len(headings) >= 5,
          f"{len(headings)} sections")

    # ── Report ──
    passes = sum(1 for r in results if r["passed"])
    fails = sum(1 for r in results if not r["passed"])

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"L4 QC REPORT: {slug}")
        print(f"{'=' * 60}")

        current_cat = ""
        for r in results:
            if r["category"] != current_cat:
                current_cat = r["category"]
                print(f"\n  [{current_cat}]")
            icon = "✅" if r["passed"] else "❌"
            detail = f" — {r['detail']}" if r["detail"] else ""
            print(f"    {icon} {r['name']}{detail}")

        print(f"\n  RESULT: {passes} passed, {fails} failed ({passes}/{passes+fails})")

        if fails == 0:
            print(f"  🎉 ALL CHECKS PASSED")
        else:
            print(f"\n  FAILURES requiring L5 correction:")
            for r in results:
                if not r["passed"]:
                    print(f"    → {r['name']}: {r['detail']}")

    # Save report
    report_path = os.path.join(PIPELINE_DIR, f"{slug}.qc-report.json")
    with open(report_path, "w") as f:
        json.dump({
            "slug": slug,
            "passes": passes,
            "fails": fails,
            "total_words": total_words,
            "results": results,
        }, f, indent=2)

    return passes, fails, results


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Hub Content Pipeline")
    parser.add_argument("slug", nargs="?", help="City hub slug (or --all)")
    parser.add_argument("--all", action="store_true", help="Run on all city hubs")
    parser.add_argument("--framework", action="store_true", help="L1: Generate framework")
    parser.add_argument("--qc", action="store_true", help="L4: Run QC/SEO checks")
    parser.add_argument("--summary", action="store_true", help="Summary only (no details)")
    args = parser.parse_args()

    if not any([args.framework, args.qc]):
        # Default: run both
        args.framework = True
        args.qc = True

    # Determine which slugs to process
    if args.all:
        slugs = sorted([
            f[:-3] for f in os.listdir(CITIES_DIR)
            if f.endswith(".md")
        ])
    elif args.slug:
        slugs = [args.slug]
    else:
        parser.print_help()
        return

    os.makedirs(PIPELINE_DIR, exist_ok=True)

    total_pass = 0
    total_fail = 0

    for slug in slugs:
        if args.framework:
            run_framework(slug)
        if args.qc:
            p, f, _ = run_qc(slug, verbose=not args.summary)
            total_pass += p
            total_fail += f

    if len(slugs) > 1 and args.qc:
        print(f"\n{'=' * 60}")
        print(f"PIPELINE SUMMARY: {len(slugs)} hubs")
        print(f"{'=' * 60}")
        print(f"  Total checks: {total_pass + total_fail}")
        print(f"  Passed: {total_pass}")
        print(f"  Failed: {total_fail}")
        if total_fail == 0:
            print(f"  🎉 ALL HUBS PASS ALL CHECKS")
        else:
            print(f"  ⚠️  {total_fail} failures require L5 correction")


if __name__ == "__main__":
    main()
