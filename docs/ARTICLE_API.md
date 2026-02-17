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
| body              | No       | Article body as HTML                                                       |
| meta_keywords     | No       | Meta keywords tag (max 255 chars)                                          |
| cover_image_url   | No       | Public URL of the cover image; we download it and use as og:image         |
| publish_immediately | No     | If `true`, the article is published right away. If `false` or omitted, it is saved as a draft (default: `true`). |

## Example (curl)

Replace `YOUR_SECRET` with the actual secret we gave you.

```bash
curl -X POST https://sirkulerekonomi.com/api/articles/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_SECRET" \
  -d '{
    "title": "My news title",
    "intro": "A short summary.",
    "meta_title": "Custom SEO title for search and social",
    "meta_description": "One sentence for search results and social previews.",
    "meta_keywords": "keyword1, keyword2, keyword3",
    "cover_image_url": "https://example.com/image.jpg",
    "body": "<p>First paragraph.</p><p>Second paragraph.</p>"
  }'
```

## Responses

- **201 Created** – Article was created. Response body includes `id`, `url`, `slug`, and `published` (whether it went live immediately).
- **400 Bad Request** – Invalid JSON, missing mandatory field (`title`, `meta_title`, or `meta_description`), or invalid `cover_image_url` (e.g. URL not an image). Response includes an `error` message.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – Our Haberler section is not available (contact us).
