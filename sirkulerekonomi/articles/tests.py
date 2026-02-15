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

    def test_post_with_bearer_token_succeeds(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "Bearer Test"}',
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer test-secret',
        )
        self.assertEqual(response.status_code, 201)

    def test_post_missing_title_returns_400(self):
        response = self.client.post(
            '/api/articles/',
            data='{}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json().get('error', ''))

    def test_post_with_correct_header_returns_201(self):
        response = self.client.post(
            '/api/articles/',
            data='{"title": "API Test Article", "intro": "Summary"}',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('url', data)
        self.assertIn('slug', data)
