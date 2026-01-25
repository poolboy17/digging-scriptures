# Pilgrimage Site — Astro Static Site

A cultural, historical, and experiential guide to faith-based journeys, pilgrimages, and sacred places.

---

## ⚠️ ARCHITECTURAL CONSTRAINTS — READ BEFORE EDITING

This document defines the **locked architecture** of this site. Future editors (human or LLM) must follow these rules without exception.

---

## Site Intent

This site is:
- **Descriptive, not prescriptive** — We describe pilgrimages and sacred places; we do not tell people what to believe
- **Place- and journey-centered** — Content focuses on locations and routes, not religious instruction
- **Non-doctrinal** — We present information about faith traditions without advocating for any
- **YMYL-safe** — Content follows Google's "Your Money or Your Life" quality guidelines
- **Adsense-safe** — No content that violates ad network policies
- **Affiliate-capable** — Structured for future contextual monetization in designated sections only

This site is **NOT**:
- Religious instruction or evangelism
- A booking platform
- A blog with date-based content
- Server-rendered or database-backed

---

## Technical Architecture

| Constraint | Value |
|------------|-------|
| Framework | Astro 5.x |
| Output | Static Site Generation (SSG) only |
| Hosting | Netlify (static) |
| SSR | ❌ FORBIDDEN |
| APIs | ❌ FORBIDDEN |
| CMS | ❌ FORBIDDEN |
| Database | ❌ FORBIDDEN |

---

## Content Collections

### 1. `hubs`
**Purpose:** Authority pages that define broad topics and link downward to specific content.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | ✅ | Max 70 chars |
| description | string | ✅ | Max 160 chars |
| topics | string[] | ❌ | Taxonomy tags |
| relatedPlaces | string[] | ❌ | Links to place pages |
| relatedRoutes | string[] | ❌ | Links to route pages |
| draft | boolean | ❌ | Default: false |

**Monetization:** ❌ NEVER  
**Word count:** 2000-3000 words  
**URL pattern:** `/journeys/[slug]`

---

### 2. `places`
**Purpose:** Sacred sites and pilgrimage destinations.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | ✅ | Max 70 chars |
| description | string | ✅ | Max 160 chars |
| region | string | ✅ | Geographic region |
| country | string | ✅ | Country name |
| coordinates | {lat, lng} | ❌ | Geographic coordinates |
| faithTraditions | string[] | ❌ | Associated traditions |
| placeType | enum | ❌ | shrine, temple, church, etc. |
| parentHub | string | ❌ | Link to parent hub |
| hasExperienceSection | boolean | ❌ | Enables monetization section |
| draft | boolean | ❌ | Default: false |

**Monetization:** ✅ OPTIONAL — only in "Experiencing This Place Today" section  
**Word count:** 1200-2500 words  
**URL pattern:** `/places/[slug]`

---

### 3. `routes`
**Purpose:** Pilgrimage routes and paths.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | ✅ | Max 70 chars |
| description | string | ✅ | Max 160 chars |
| region | string | ✅ | Geographic region |
| countries | string[] | ✅ | Countries traversed |
| distanceKm | number | ❌ | Total distance |
| typicalDurationDays | number | ❌ | Typical completion time |
| faithTraditions | string[] | ❌ | Associated traditions |
| difficulty | enum | ❌ | easy, moderate, challenging, difficult |
| hasModernSection | boolean | ❌ | Enables monetization section |
| draft | boolean | ❌ | Default: false |

**Monetization:** ✅ OPTIONAL — only in "Modern Pilgrimage Experiences" section  
**Word count:** 1200-2500 words  
**URL pattern:** `/routes/[slug]`

---

### 4. `stories`
**Purpose:** People, traditions, and cultural narratives.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | ✅ | Max 70 chars |
| description | string | ✅ | Max 160 chars |
| storyType | enum | ✅ | historical-figure, tradition, etc. |
| faithTraditions | string[] | ❌ | Associated traditions |
| timePeriod | string | ❌ | Historical period |
| relatedPlaces | string[] | ❌ | Links to places |
| relatedRoutes | string[] | ❌ | Links to routes |
| draft | boolean | ❌ | Default: false |

**Monetization:** ❌ NO (by default)  
**Word count:** 1000-2000 words  
**URL pattern:** `/stories/[slug]`

---

### 5. `context`
**Purpose:** Historical and cultural background articles.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | ✅ | Max 70 chars |
| description | string | ✅ | Max 160 chars |
| contextType | enum | ✅ | historical-background, cultural-overview, etc. |
| faithTraditions | string[] | ❌ | Related traditions |
| regions | string[] | ❌ | Geographic scope |
| draft | boolean | ❌ | Default: false |

**Monetization:** ❌ NEVER  
**Word count:** 1000-2000 words  
**URL pattern:** `/context/[slug]`

---

## Page Templates

Each collection has a dedicated layout template in `src/layouts/`:

| Template | Collection | Monetization Zones |
|----------|------------|-------------------|
| `HubLayout.astro` | hubs | None |
| `PlaceLayout.astro` | places | Section 5 only |
| `RouteLayout.astro` | routes | Section 5 only |
| `StoryLayout.astro` | stories | None |
| `ContextLayout.astro` | context | None |

**Template sections are LOCKED.** Do not reorder or remove sections.

---

## Monetization Rules

### ✅ ALLOWED (in designated sections only)
- Affiliate links to tour operators
- Affiliate links to accommodation
- Affiliate links to travel gear
- Contextual display ads (future)

### ❌ FORBIDDEN (everywhere)
- Pop-ups or interstitials
- Hard-sell CTAs
- Misleading claims
- Auto-playing media ads
- Content that violates YMYL guidelines

### Monetization Zones
Monetization is permitted **ONLY** in these clearly marked template sections:
- `PlaceLayout.astro` → "Experiencing This Place Today"
- `RouteLayout.astro` → "Modern Pilgrimage Experiences"

All other sections and all other page types: **NO monetization**

---

## URL Structure

| Pattern | Collection | Example |
|---------|------------|---------|
| `/journeys/[slug]` | hubs | `/journeys/faith-based-journeys` |
| `/places/[slug]` | places | `/places/santiago-de-compostela` |
| `/routes/[slug]` | routes | `/routes/camino-de-santiago` |
| `/stories/[slug]` | stories | `/stories/legend-of-saint-james` |
| `/context/[slug]` | context | `/context/history-of-christian-pilgrimage` |

**DO NOT** use date-based or blog-style URLs.

---

## What Future Editors Must NOT Change

1. **Output mode** — Must remain `static` (SSG only)
2. **Content collection schemas** — Field types and required fields are locked
3. **Template section order** — Sections must remain in defined order
4. **Monetization zones** — Only designated sections may contain affiliate/ad content
5. **URL patterns** — Semantic, non-date-based routing is required
6. **Site intent** — Descriptive, non-doctrinal framing must be maintained

---

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Deployment

This site is configured for Netlify static hosting. Push to the main branch to trigger deployment.

**Pre-deployment checklist:**
- [ ] All placeholder content replaced with real content
- [ ] All `draft: true` flags removed from publishable content
- [ ] Site URL updated in `astro.config.mjs`
- [ ] Build completes without errors

---

## License

[Add license information]

---

## Version

Architecture version: 1.0.0  
Last updated: 2026-01-25
