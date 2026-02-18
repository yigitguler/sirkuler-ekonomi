# Article API – Posting articles to Haberler

You can create articles automatically by sending a **POST** request to our article API. The request must include a shared secret in a header so only authorized clients can publish.

## Endpoint

- **URL:** `https://sirkulerekonomi.com/api/articles/`
- **Method:** POST
- **Content-Type:** application/json

## Authentication

Send the secret in one of these headers:

- **X-API-Key:** `<your-secret>`
- **Authorization:** `Bearer <your-secret>`

(Use the same secret value we sent you separately. Do not share it.)

## Request body

**Mandatory:** `title`, `meta_title`, `meta_description`

| Field             | Required | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| title             | Yes      | Article title                                                              |
| meta_title        | Yes      | SEO title for &lt;title&gt;, og:title, twitter:title (max 70 chars)        |
| meta_description  | Yes      | Meta description and og:description (max 500 chars)                         |
| intro             | No       | Short summary (max 500 chars)                                               |
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

## Responses

- **201 Created** – Article was created. Response body includes `id`, `url`, `slug`, and `published` (whether it went live immediately).
- **400 Bad Request** – Invalid JSON, missing mandatory field (`title`, `meta_title`, or `meta_description`), or invalid cover image (`cover_image_url` not an image, or `cover_image_base64` invalid/unsupported). Response includes an `error` message.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – Our Haberler section is not available (contact us).
