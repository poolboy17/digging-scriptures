/**
 * rehype-image-optimize.mjs
 * 
 * Rehype plugin: auto-optimizes every <img> at build time.
 * 
 * For raw HTML nodes in markdown (before rehype-raw parses them):
 *   1. Routes src through Netlify Image CDN
 *   2. Generates srcset at 5 breakpoints
 *   3. Adds sizes, width, height, loading, decoding
 *   4. Wraps bare <img> in <figure> with <figcaption> from alt text
 * 
 * For already-parsed element nodes:
 *   - Same attribute normalization
 *   - Skips images that already have srcset
 */

const WIDTHS = [320, 480, 640, 800, 1080];
const DEFAULT_SIZES = '(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 800px';

function cdnUrl(path, width) {
  if (path.startsWith('/.netlify/images')) {
    return path.replace(/w=\d+/, `w=${width}`);
  }
  return `/.netlify/images?url=${encodeURIComponent(path)}&w=${width}`;
}

function extractRawPath(src) {
  const match = src.match(/[?&]url=([^&"]+)/);
  if (match) return decodeURIComponent(match[1]);
  if (src.startsWith('/images/')) return src;
  return src;
}

function filenameToAlt(src) {
  const filename = src.split('/').pop().replace(/\.[^.]+$/, '');
  const clean = filename.replace(/-[a-f0-9]{6}$/, '').replace(/-\d+$/, '');
  return clean.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function buildSrcset(rawPath) {
  return WIDTHS.map(w => `${cdnUrl(rawPath, w)} ${w}w`).join(', ');
}

/**
 * Process a raw HTML string containing <img> tags.
 * - Adds responsive attributes to any <img> missing srcset
 * - Wraps bare <img> (not already inside <figure>) in <figure>/<figcaption>
 */
function optimizeRawHtml(html) {
  // Skip if already inside a <figure>
  const inFigure = /<figure[\s>]/i.test(html);
  
  const optimized = html.replace(/<img\b([^>]*?)\/?>/gi, (match, attrs) => {
    if (/srcset\s*=/i.test(attrs)) return match;
    
    const srcMatch = attrs.match(/src\s*=\s*"([^"]+)"/i);
    if (!srcMatch) return match;
    const src = srcMatch[1];
    const rawPath = extractRawPath(src);
    
    const altMatch = attrs.match(/alt\s*=\s*"([^"]*)"/i);
    const alt = (altMatch && altMatch[1].trim()) ? altMatch[1] : filenameToAlt(rawPath);
    
    const hasLoading = /loading\s*=/i.test(attrs);
    const hasDecoding = /decoding\s*=/i.test(attrs);
    const hasWidth = /width\s*=/i.test(attrs);
    const hasHeight = /height\s*=/i.test(attrs);
    const hasSizes = /sizes\s*=/i.test(attrs);
    
    let tag = `<img src="${cdnUrl(rawPath, 800)}"`;
    tag += ` srcset="${buildSrcset(rawPath)}"`;
    if (!hasSizes) tag += ` sizes="${DEFAULT_SIZES}"`;
    tag += ` alt="${alt}"`;
    if (!hasWidth) tag += ' width="800"';
    if (!hasHeight) tag += ' height="533"';
    if (!hasLoading) tag += ' loading="lazy"';
    if (!hasDecoding) tag += ' decoding="async"';
    tag += ' style="border-radius:0.75rem;width:100%;height:auto;max-height:400px;object-fit:cover;"';
    tag += ' />';
    
    // Wrap in figure if not already inside one
    if (!inFigure) {
      return `<figure style="margin:2rem 0">\n${tag}\n<figcaption style="font-size:0.8125rem;color:#a8a29e;margin-top:0.5rem;font-style:italic;">${alt}</figcaption>\n</figure>`;
    }
    
    return tag;
  });
  
  return optimized;
}

export default function rehypeImageOptimize() {
  return (tree) => {
    visit(tree);
  };
}

function visit(node) {
  // Handle raw HTML nodes (markdown content before rehype-raw)
  if (node.type === 'raw' && typeof node.value === 'string' && /<img\b/i.test(node.value)) {
    node.value = optimizeRawHtml(node.value);
  }
  
  // Handle parsed element nodes (from layouts/components)
  if (node.type === 'element' && node.tagName === 'img') {
    const props = node.properties || {};
    
    if (props.srcSet || props.srcset) {
      if (!props.loading) props.loading = 'lazy';
      if (!props.decoding) props.decoding = 'async';
      node.properties = props;
      return;
    }
    
    const src = props.src || '';
    if (!src) return;
    const rawPath = extractRawPath(src);
    
    props.src = cdnUrl(rawPath, 800);
    props.srcSet = buildSrcset(rawPath);
    if (!props.sizes) props.sizes = DEFAULT_SIZES;
    if (!props.width) props.width = '800';
    if (!props.height) props.height = '533';
    if (!props.loading) props.loading = 'lazy';
    if (!props.decoding) props.decoding = 'async';
    if (!props.alt || props.alt.trim() === '') {
      props.alt = filenameToAlt(rawPath);
    }
    
    node.properties = props;
  }
  
  if (node.children) {
    for (const child of node.children) {
      visit(child);
    }
  }
}
