import json
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(ARTICLE_API_SECRET='test-secret')
class PostArticleAPITests(TestCase):
    def test_post_without_header_returns_401(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Test"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'error': 'Unauthorized'})

    def test_post_with_wrong_header_returns_401(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Test"}',
            content_type='application/json',
            HTTP_X_API_KEY='wrong',
        )
        self.assertEqual(response.status_code, 401)

    def _valid_payload(self, **overrides):
        payload = {'title': 'Test Title', 'meta_title': 'SEO Title', 'meta_description': 'Meta description text.'}
        payload.update(overrides)
        return payload

    def test_post_with_bearer_token_succeeds(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Bearer Test", "meta_title": "SEO", "meta_description": "Description"}',
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer test-secret',
        )
        self.assertEqual(response.status_code, 201)

    def test_post_missing_title_returns_400(self):
        response = self.client.post(
            '/api/articles/',
            data='{"meta_title": "SEO", "meta_description": "Desc"}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json().get('error', ''))

    def test_post_missing_meta_title_returns_400(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Title", "meta_description": "Desc"}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('meta_title', response.json().get('error', ''))

    def test_post_missing_meta_description_returns_400(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Title", "meta_title": "SEO"}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('meta_description', response.json().get('error', ''))

    def test_post_with_correct_header_returns_201(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "API Test Article", "meta_title": "API SEO Title", "meta_description": "Summary for meta.", "intro": "Summary"}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('url', data)
        self.assertIn('slug', data)

    def test_post_with_body_roundtrips_correctly(self):
        body_md = '## Test Heading\n\nA paragraph with **bold**.\n\n> A blockquote line.'
        payload = {
            'title': 'Body Roundtrip Test',
            'meta_title': 'Body Roundtrip SEO',
            'meta_description': 'Testing body import.',
            'intro': 'Intro',
            'body': body_md,
        }
        response = self.client.post(
            '/api/articles/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        article_id = data['id']
        detail = self.client.get(
            '/api/articles/%d/' % article_id,
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(detail.status_code, 200)
        body_html = detail.json().get('body', '')
        self.assertIn('Test Heading', body_html)
        self.assertIn('A paragraph with', body_html)
        self.assertIn('bold', body_html)
        self.assertIn('A blockquote line', body_html)
