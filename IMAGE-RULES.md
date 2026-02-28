# Image Optimization Ruleset — Digging Scriptures

All images on diggingscriptures.com pass through Netlify Image CDN and must follow these standards.

## Required Attributes (Every `<img>` Tag)

| Attribute | Value | Purpose |
|---|---|---|
| `src` | `/.netlify/images?url={path}&w=800` | CDN-routed fallback at 800px |
| `srcset` | 5 breakpoints via CDN | Responsive delivery |
| `sizes` | Viewport-based hint | Browser picks optimal size |
| `alt` | Descriptive, 5-15 words | Accessibility + SEO |
| `width` | Intrinsic or layout width | Prevents CLS |
| `height` | Intrinsic or layout height | Prevents CLS |
| `loading` | `lazy` (default) or `eager` | Performance |
| `decoding` | `async` | Non-blocking decode |

### Hero images (above the fold) also need:
| Attribute | Value |
|---|---|
| `loading` | `eager` |
| `fetchpriority` | `high` |


## Srcset Breakpoints

All images use the same 5 widths:

```
320w, 480w, 640w, 800w, 1080w
```

Generated via Netlify CDN:
```
srcset="/.netlify/images?url={path}&w=320 320w,
        /.netlify/images?url={path}&w=480 480w,
        /.netlify/images?url={path}&w=640 640w,
        /.netlify/images?url={path}&w=800 800w,
        /.netlify/images?url={path}&w=1080 1080w"
```


## Sizes Attribute by Context

| Context | `sizes` value |
|---|---|
| **Full-width hero** (hub pages) | `100vw` |
| **Inline content image** (articles) | `(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 800px` |
| **Card thumbnail** (grids) | `(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw` |
| **Sidebar image** (sidebar products) | `220px` |


## Width × Height Defaults

| Context | width | height | Aspect |
|---|---|---|---|
| Hero image | `1200` | `600` | 2:1 |
| Inline content | `800` | `533` | 3:2 |
| Card thumbnail | `640` | `427` | 3:2 |


## Alt Text Rules

- **5-15 words** — enough for screen readers, short enough for clean HTML
- **Describe the scene**, not the filename. "Pilgrims walking the Camino at dawn" not "camino-pilgrims-01"
- **Never empty** — use the image caption or article title as fallback
- **No keyword stuffing** — describe what's visible, don't game SEO
- **No "image of" or "photo of"** — screen readers already announce it as an image


## File Standards

| Property | Standard |
|---|---|
| **Format** | JPEG (photos), PNG (diagrams/transparency), SVG (icons) |
| **Source size** | Upload at 1200-1600px wide minimum |
| **Max file size** | ~500KB before CDN (CDN handles compression) |
| **Naming** | `{slug}-{n}-{hash}.jpg` e.g. `bodh-gaya-3-025ef2.jpg` |
| **Location** | `/public/images/content/inline/` (inline), `/public/images/content/` (hero) |
| **License** | Pixabay (free commercial) or Unsplash (free commercial) |


## Two Ways to Add Images

### 1. In Astro layouts/components → Use `<CdnImage>`
```astro
<CdnImage
  src="/images/content/places-bodh-gaya.jpg"
  alt="The Mahabodhi Temple in Bodh Gaya, Bihar"
  width={800}
  height={533}
  loading="lazy"
/>
```
The component auto-generates srcset, sizes, and CDN URLs.

### 2. In markdown content → Use raw `<img>` with full attributes
```html
<img
  src="/.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=800"
  srcset="/.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=320 320w,
          /.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=480 480w,
          /.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=640 640w,
          /.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=800 800w,
          /.netlify/images?url=/images/content/inline/bodh-gaya-3-025ef2.jpg&w=1080 1080w"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 800px"
  alt="The Mahabodhi Temple rising above Bodh Gaya"
  width="800" height="533"
  loading="lazy" decoding="async"
  style="border-radius:0.75rem;width:100%;height:auto;max-height:400px;object-fit:cover;"
/>
```

### Never do this:
```html
<!-- ❌ Missing srcset, sizes, width, height, decoding -->
<img src="/.netlify/images?url=/images/foo.jpg&w=800" alt="foo" loading="lazy" />

<!-- ❌ Hardcoded pixel URL, no responsive breakpoints -->
<img src="/images/foo.jpg" width="800" />

<!-- ❌ Empty alt -->
<img src="..." alt="" />
```


## Image Density Target

- **1 image per ~400 words** of prose content
- Minimum 2 inline images per article (below 1500 words)
- Minimum 3 inline images per article (above 1500 words)
- Hub pages: minimum 4 inline images
- Place after the first paragraph of a new H2 section for natural rhythm


## Inline Image Styling

All inline content images share this style:
```css
border-radius: 0.75rem;
width: 100%;
height: auto;
max-height: 400px;
object-fit: cover;
```

Captions use italic markdown: `*Caption text*` on the line below the `<img>`.


## Validation

Run this to audit all images:
```bash
python3 -c "
import re, glob
for f in glob.glob('src/content/**/*.md', recursive=True):
    body = open(f).read().split('---')[2] if '---' in open(f).read() else ''
    for m in re.finditer(r'<img\b[^>]+>', body):
        tag = m.group()
        issues = []
        if 'srcset=' not in tag: issues.append('NO srcset')
        if 'sizes=' not in tag: issues.append('NO sizes')
        if 'width=' not in tag: issues.append('NO width')
        if 'loading=' not in tag: issues.append('NO loading')
        if 'decoding=' not in tag: issues.append('NO decoding')
        if 'alt=\"\"' in tag: issues.append('EMPTY alt')
        if issues:
            print(f'{f}: {\" | \".join(issues)}')
if not issues: print('All images pass ✅')
"
```
