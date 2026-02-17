# SEO checklist (critical)

This project treats SEO as critical. Use this checklist when adding or changing pages and templates.

## Meta and Open Graph

- [ ] Every page has a unique `<title>` (prefer `seo_title` when set, else page title + site name).
- [ ] Meta description present and unique; use `search_description` when set, else sensible fallback.
- [ ] Canonical URL is absolute and correct (`page.full_url` for Wagtail pages).
- [ ] Articles: `og:type` = article; `og:title`, `og:description`, `og:image` set.
- [ ] `og:image:width`, `og:image:height`, `og:image:alt` set when an image is used (better sharing and snippets).
- [ ] Twitter card: `twitter:card` (summary_large_image for articles), `twitter:title`, `twitter:description`; image comes from og:image.
- [ ] Default `meta name="robots"` is `index, follow`; override only for noindex pages.

## Structured data (JSON-LD)

- [ ] Article/news pages output a NewsArticle schema with:
  - `@context`, `@type`, `mainEntityOfPage`, `headline`, `description`, `datePublished`, `dateModified`, `url`, `publisher`, `author`, `image` (array of URLs).
- [ ] Description in schema uses `search_description` when set, else intro.
- [ ] Escape `</` in JSON-LD as `<\/` to avoid breaking in HTML.

## Performance (Core Web Vitals)

- [ ] LCP: Main hero/cover image has explicit `width` and `height` to avoid layout shift (CLS).
- [ ] LCP image uses `fetchpriority="high"` and `loading="eager"`; consider `<link rel="preload" as="image">` for that image in `<head>`.
- [ ] All images have meaningful `alt` text.
- [ ] Fonts: preconnect to font origins; prefer `font-display: swap` (e.g. Google Fonts default).

## Sitemap and crawling

- [ ] `robots.txt` allows crawling and points to `sitemap.xml`.
- [ ] Wagtail sitemap includes all public pages; article pages set `lastmod` where possible.

## New page types

- [ ] New Wagtail page models that should be indexed: add `search_description` (and `seo_title` if needed), expose them in promote_panels, and set canonical and meta in the template.
- [ ] New API or endpoints that create content: accept and store `meta_title`, `meta_description`, `meta_keywords` (and cover image) so templates can render full SEO meta.
