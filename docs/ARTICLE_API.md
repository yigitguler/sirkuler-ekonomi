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

| Field   | Required | Description                    |
|--------|----------|--------------------------------|
| title  | Yes      | Article title                  |
| intro  | No       | Short summary (max 500 chars)  |
| body   | No       | Article body as HTML           |

## Example (curl)

Replace `YOUR_SECRET` with the actual secret we gave you.

```bash
curl -X POST https://sirkulerekonomi.com/api/articles/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_SECRET" \
  -d '{"title": "My news title", "intro": "A short summary.", "body": "<p>First paragraph.</p><p>Second paragraph.</p>"}'
```

## Responses

- **201 Created** – Article was created. Response body includes `id`, `url`, and `slug`.
- **400 Bad Request** – Invalid JSON or missing `title`. Response includes an `error` message.
- **401 Unauthorized** – Missing or wrong secret in the header.
- **404 Not Found** – Our Haberler section is not available (contact us).
