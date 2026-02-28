/**
 * rehype-image-optimize.mjs
 * 
 * Rehype plugin that enforces the image optimization ruleset at build time.
 * 
 * IMPORTANT: In Astro's pipeline, user rehype plugins run BEFORE rehype-raw.
 * So raw HTML in markdown arrives as { type: "raw", value: "<img ...>" } nodes.
 * This plugin handles BOTH:
 *   - "raw" nodes containing <img> (from markdown content)
 *   - "element" nodes with tagName "img" (from layouts/components)
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

function optimizeRawImgTag(html) {
  // Process raw HTML string containing an <img> tag
  return html.replace(/<img\b([^>]*?)\/?>/gi, (match, attrs) => {
    // Skip if already has srcset
    if (/srcset\s*=/i.test(attrs)) return match;
    
    // Extract src
    const srcMatch = attrs.match(/src\s*=\s*"([^"]+)"/i);
    if (!srcMatch) return match;
    const src = srcMatch[1];
    
    const rawPath = extractRawPath(src);
    
    // Extract existing alt or generate one
    const altMatch = attrs.match(/alt\s*=\s*"([^"]*)"/i);
    const alt = (altMatch && altMatch[1].trim()) ? altMatch[1] : filenameToAlt(rawPath);
    
    // Check for existing loading attr
    const hasLoading = /loading\s*=/i.test(attrs);
    const hasDecoding = /decoding\s*=/i.test(attrs);
    const hasWidth = /width\s*=/i.test(attrs);
    const hasHeight = /height\s*=/i.test(attrs);
    const hasSizes = /sizes\s*=/i.test(attrs);
    const hasStyle = /style\s*=/i.test(attrs);
    
    // Build optimized tag
    let newTag = `<img src="${cdnUrl(rawPath, 800)}"`;
    newTag += ` srcset="${buildSrcset(rawPath)}"`;
    newTag += hasSizes ? '' : ` sizes="${DEFAULT_SIZES}"`;
    newTag += ` alt="${alt}"`;
    newTag += hasWidth ? '' : ' width="800"';
    newTag += hasHeight ? '' : ' height="533"';
    newTag += hasLoading ? '' : ' loading="lazy"';
    newTag += hasDecoding ? '' : ' decoding="async"';
    
    if (!hasStyle) {
      newTag += ' style="border-radius:0.75rem;width:100%;height:auto;max-height:400px;object-fit:cover;"';
    }
    
    // Preserve any other existing attributes (loading, decoding, style, class, etc.)
    // that we haven't already added
    const preserveAttrs = attrs
      .replace(/src\s*=\s*"[^"]*"/i, '')
      .replace(/alt\s*=\s*"[^"]*"/i, '')
      .replace(/^\s+|\s+$/g, '');
    
    if (preserveAttrs.trim()) {
      // Only add attrs we haven't already set
      const toPreserve = preserveAttrs
        .replace(/width\s*=\s*"[^"]*"/gi, hasWidth ? '$&' : '')
        .replace(/height\s*=\s*"[^"]*"/gi, hasHeight ? '$&' : '')
        .replace(/loading\s*=\s*"[^"]*"/gi, '')
        .replace(/decoding\s*=\s*"[^"]*"/gi, '')
        .replace(/sizes\s*=\s*"[^"]*"/gi, '')
        .replace(/style\s*=\s*"[^"]*"/gi, hasStyle ? '$&' : '')
        .trim();
      if (toPreserve) newTag += ` ${toPreserve}`;
    }
    
    newTag += ' />';
    return newTag;
  });
}

export default function rehypeImageOptimize() {
  return (tree) => {
    visit(tree);
  };
}

function visit(node) {
  // Handle raw HTML nodes (from markdown content)
  if (node.type === 'raw' && typeof node.value === 'string' && /<img\b/i.test(node.value)) {
    node.value = optimizeRawImgTag(node.value);
  }
  
  // Handle parsed element nodes (from layouts)
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
    
    if (!props.className && !props.class) {
      const existingStyle = props.style || '';
      if (!existingStyle.includes('border-radius')) {
        props.style = 'border-radius:0.75rem;width:100%;height:auto;max-height:400px;object-fit:cover;' +
          (existingStyle ? ' ' + existingStyle : '');
      }
    }
    
    node.properties = props;
  }
  
  if (node.children) {
    for (const child of node.children) {
      visit(child);
    }
  }
}
