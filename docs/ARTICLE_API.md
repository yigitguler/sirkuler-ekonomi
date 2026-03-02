# Article API – Create, list, retrieve and update articles

You can create, list, retrieve and update articles via the article API. All endpoints require a shared secret in a header.

## Authentication

Send the secret in one of these headers:

- **X-API-Key:** `<your-secret>`
- **Authorization:** `Bearer <your-secret>`

(Use the same secret value we sent you separately. Do not share it.)

---

## POST – Create article

- **URL:** `https://sirkulerekonomi.com/api/articles/`
- **Method:** POST
- **Content-Type:** application/json

### Request body

**Mandatory:** `title`, `meta_title`, `meta_description`

| Field             | Required | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| title             | Yes      | Article title                                                              |
| meta_title        | Yes      | SEO title for &lt;title&gt;, og:title, twitter:title (max 70 chars)        |
| meta_description  | Yes      | Meta description and og:description (max 500 chars)                         |
| intro             | No       | Short summary (max 1000 chars)                                              |
| body              | No       | Article body as **Markdown**. Converted to HTML then parsed into Wagtail StreamField blocks (paragraph, heading, blockquote). Supports **extra** (tables, fenced code) and **nl2br** (newlines as `<br>`). |
| meta_keywords     | No       | Meta keywords tag (max 255 chars)                                          |
| cover_image_url   | No       | Public URL of the cover image; we download it and use as og:image         |
| cover_image_base64 | No      | Cover image as base64 (raw string or data URL like `data:image/png;base64,...`). Supported: JPEG, PNG, GIF, WebP. If both URL and base64 are sent, base64 is used. |
| publish_immediately | No     | If `true`, the article is published right away. If `false` or omitted, it is saved as a draft (default: `true`). |

## Example (curl)

Replace `YOUR_SECRET` with the actual secret we gave you.

```bash
curl -X POST https://sirkulerekonomi.com/api/articles/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_SECRET" \
  -d '{
    "title": "Döngüsel Ekonomi ve Sürdürülebilir Üretim",
    "intro": "Avrupa Birliği yeşil mutabakatı ve yerel uygulamalar.",
    "meta_title": "Döngüsel Ekonomi 2025 – Sürdürülebilir Üretim",
    "meta_description": "Döngüsel ekonomi, yeşil mutabakat ve sürdürülebilir üretim uygulamaları hakkında güncel analiz.",
    "meta_keywords": "döngüsel ekonomi, sürdürülebilirlik, yeşil mutabakat",
    "cover_image_url": "https://example.com/image.jpg",
    "publish_immediately": true,
    "body": "Sürdürülebilir büyüme ve kaynak verimliliği, günümüz sanayi politikalarının merkezinde yer alıyor. Bu yazıda **döngüsel ekonomi** modelleri ve uygulama örneklerini inceliyoruz.\n\n## Yeşil Mutabakat ve Hedefler\n\nAvrupa Birliği Yeşil Mutabakatı, 2050 karbon nötr hedefine yönelik yatırım ve düzenlemeleri içeriyor. Üye ülkeler ve ticaret ortakları için *dönüşüm* fırsatları ve yükümlülükler getiriyor.\n\nYerel üreticilerin uyum süreçleri, finansman araçları ve teknik destek programlarıyla desteklenmesi gerekiyor. Özellikle KOBİ’lerin döngüsel ekonomi prensiplerine geçişi için net yol haritaları önem taşıyor.\n\n### Atık Azaltımı ve Geri Kazanım\n\nAtık yönetimi ve geri dönüşüm altyapısı, döngüsel ekonominin temel taşlarından biri. Kaynak verimliliği artırılırken atık miktarının azaltılması hedefleniyor.\n\n> Döngüsel ekonomi, ürünlerin ve malzemelerin mümkün olduğunca uzun süre ekonomide kalmasını ve atığın en aza indirilmesini amaçlar.\n\nSonuç olarak, hem çevresel hem de ekonomik fayda sağlayan bir üretim modeli giderek daha fazla benimseniyor. Önümüzdeki dönemde politika ve sektör uyumunun hızlanması bekleniyor."
  }'
```

### Responses (POST)

- **201 Created** – Article was created. Response body includes `id`, `url`, `slug`, and `published` (whether it went live immediately).
- **400 Bad Request** – Invalid JSON, missing mandatory field (`title`, `meta_title`, or `meta_description`), or invalid cover image (`cover_image_url` not an image, or `cover_image_base64` invalid/unsupported). Response includes an `error` message.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – Our Haberler section is not available (contact us).

---

## GET – List articles

- **URL:** `https://sirkulerekonomi.com/api/articles/`
- **Method:** GET

### Query parameters (optional)

| Parameter | Description |
|-----------|-------------|
| limit     | Number of results per page (default 20, max 100). |
| offset    | Number of results to skip (default 0). |
| live      | Filter by published state: `true` or `false`. |
| locale    | Filter by locale, e.g. `tr`, `en`. |

### Response

JSON object:

- **results** – Array of article summaries. Each item: `id`, `title`, `slug`, `url` (full URL), `intro`, `live`, `first_published_at`, `last_published_at`, `locale`, `main_image_url`.
- **count** – Total number of articles matching the filters.
- **next_offset** – Present if there are more results (use as `offset` for next page).
- **previous_offset** – Present if offset &gt; 0.

- **401 Unauthorized** – Missing or wrong secret in the header.

---

## GET – Retrieve one article

- **URL:** `https://sirkulerekonomi.com/api/articles/<id>/`
- **Method:** GET
- **&lt;id&gt;** – Article primary key (integer).

### Response

JSON object with full content: `id`, `title`, `slug`, `url`, `intro`, `body` (article body as a single **HTML** string), `main_image_url`, `meta_title`, `meta_description`, `meta_keywords`, `live`, `first_published_at`, `last_published_at`, `locale`.

- **200 OK** – Article found.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – No article with that id. Response: `{ "error": "Not found" }`.

---

## PATCH – Update article

- **URL:** `https://sirkulerekonomi.com/api/articles/<id>/`
- **Method:** PATCH
- **Content-Type:** application/json
- **&lt;id&gt;** – Article primary key (integer).

Partial update: send only the fields you want to change. All fields are optional.

| Field              | Description (same as POST where applicable) |
|--------------------|----------------------------------------------|
| title              | Article title. |
| meta_title         | SEO title (max 70 chars). |
| meta_description   | Meta description (max 500 chars). |
| intro              | Short summary (max 1000 chars). |
| body               | Article body as **Markdown** (converted to StreamField blocks). |
| meta_keywords      | Meta keywords (max 255 chars). |
| cover_image_url    | Public URL of cover image; we download and set as main image. |
| cover_image_base64 | Cover image as base64 (raw or data URL). |
| live               | If `true`, publish the current revision; if `false`, leave as draft. |

### Response

Same as POST success: `id`, `url`, `slug`, `published` (whether the article is now live).

- **200 OK** – Article updated.
- **400 Bad Request** – Invalid JSON. Response includes an `error` message.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – No article with that id. Response: `{ "error": "Not found" }`.
