import json
from django.test import TestCase, override_settings

from articles.models import ArticlePage


def _api_post(client, url, data, key='test-secret'):
    return client.post(url, data=json.dumps(data) if isinstance(data, dict) else data,
                       content_type='application/json', HTTP_X_API_KEY=key)


def _api_get(client, url, key='test-secret'):
    return client.get(url, HTTP_X_API_KEY=key)


def _api_patch(client, url, data, key='test-secret'):
    return client.patch(url, data=json.dumps(data), content_type='application/json', HTTP_X_API_KEY=key)


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
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        article_id = data['id']
        detail = _api_get(self.client, '/api/articles/%d/' % article_id)
        self.assertEqual(detail.status_code, 200)
        body_html = detail.json().get('body', '')
        self.assertIn('Test Heading', body_html)
        self.assertIn('A paragraph with', body_html)
        self.assertIn('bold', body_html)
        self.assertIn('A blockquote line', body_html)

    def test_post_body_parsed_as_heading_paragraph_blockquote_blocks(self):
        """Assert the markdown body is parsed into the correct StreamField block types and values."""
        body_md = '## Test Heading\n\nA paragraph with **bold**.\n\n> A blockquote line.'
        payload = {
            'title': 'Parse Structure Test',
            'meta_title': 'Parse SEO',
            'meta_description': 'Parse test.',
            'body': body_md,
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201, response.content)
        article = ArticlePage.objects.get(pk=response.json()['id'])
        blocks = list(article.body)
        self.assertEqual(len(blocks), 3, 'Expected 3 blocks: heading, paragraph, blockquote. Got %s' % [b.block_type for b in blocks])
        self.assertEqual(blocks[0].block_type, 'heading')
        self.assertEqual(blocks[0].value.strip(), 'Test Heading')
        self.assertEqual(blocks[1].block_type, 'paragraph')
        paragraph_val = blocks[1].value
        self.assertTrue(hasattr(paragraph_val, 'source'), 'Paragraph block should have RichText with .source')
        self.assertIn('A paragraph with', paragraph_val.source)
        self.assertIn('bold', paragraph_val.source)
        self.assertEqual(blocks[2].block_type, 'blockquote')
        self.assertIn('A blockquote line', blocks[2].value.strip())

    def test_post_body_rendered_html_has_expected_structure(self):
        """Assert the API body response contains proper HTML elements from each block type."""
        body_md = '## Section Title\n\nSome text.\n\n> Quote text.'
        payload = {
            'title': 'HTML Structure Test',
            'meta_title': 'HTML SEO',
            'meta_description': 'HTML structure.',
            'body': body_md,
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        detail = _api_get(self.client, '/api/articles/%d/' % response.json()['id'])
        body_html = detail.json().get('body', '')
        self.assertIn('<h2>', body_html, 'Body should contain heading tag')
        self.assertIn('Section Title', body_html)
        self.assertIn('<blockquote>', body_html, 'Body should contain blockquote tag')
        self.assertIn('Quote text.', body_html)
        self.assertIn('Some text.', body_html)

    def test_post_invalid_json_returns_400(self):
        response = self.client.post(
            '/api/articles/',
            data='not json',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertIn('JSON', response.json().get('error', ''))

    def test_post_with_empty_body_creates_article(self):
        payload = {
            'title': 'Empty Body Article',
            'meta_title': 'Empty Body SEO',
            'meta_description': 'No body.',
            'body': '',
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        article_id = response.json()['id']
        detail = _api_get(self.client, '/api/articles/%d/' % article_id)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json().get('body', ''), '')

    def test_post_body_with_markdown_lists_converted_to_paragraphs(self):
        body_md = '## Section\n\n- Item one\n- Item two\n\nAnother paragraph.'
        payload = {
            'title': 'List Body Test',
            'meta_title': 'List SEO',
            'meta_description': 'Lists as paragraphs.',
            'body': body_md,
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        detail = _api_get(self.client, '/api/articles/%d/' % response.json()['id'])
        body_html = detail.json().get('body', '')
        self.assertIn('Section', body_html)
        self.assertIn('Item one', body_html)
        self.assertIn('Another paragraph', body_html)

    def test_post_body_lists_parsed_as_blocks_not_dropped(self):
        """Lists and unsupported markdown become paragraph blocks; no content dropped."""
        body_md = '## Section\n\n- Item one\n- Item two\n\nAnother paragraph.'
        response = _api_post(self.client, '/api/articles/', {
            'title': 'List Parse Test',
            'meta_title': 'List Parse SEO',
            'meta_description': 'List parse.',
            'body': body_md,
        })
        self.assertEqual(response.status_code, 201)
        article = ArticlePage.objects.get(pk=response.json()['id'])
        blocks = list(article.body)
        block_types = [b.block_type for b in blocks]
        self.assertIn('heading', block_types)
        self.assertIn('paragraph', block_types, 'List/unsupported content should become paragraph(s)')
        self.assertGreaterEqual(len(blocks), 2, 'Should have at least heading + some content blocks')
        full_text = ' '.join(str(b.value) for b in blocks)
        self.assertIn('Item one', full_text)
        self.assertIn('Another paragraph', full_text)

    def test_post_body_with_multiple_headings_and_paragraphs(self):
        body_md = '''# First

First para.

## Second

Second para.

### Third

Third para.'''
        payload = {
            'title': 'Multi Heading Test',
            'meta_title': 'Multi SEO',
            'meta_description': 'Many blocks.',
            'body': body_md,
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        detail = _api_get(self.client, '/api/articles/%d/' % response.json()['id'])
        body_html = detail.json().get('body', '')
        self.assertIn('First', body_html)
        self.assertIn('Second', body_html)
        self.assertIn('Third', body_html)
        self.assertIn('First para', body_html)
        self.assertIn('Second para', body_html)
        self.assertIn('Third para', body_html)

    def test_post_publish_immediately_false_creates_draft(self):
        payload = {
            'title': 'Draft Article',
            'meta_title': 'Draft SEO',
            'meta_description': 'Not published.',
            'publish_immediately': False,
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertFalse(data.get('published'))
        article = ArticlePage.objects.get(pk=data['id'])
        self.assertFalse(article.live)

    def test_post_publish_immediately_string_yes_treated_as_true(self):
        payload = {
            'title': 'Published Article',
            'meta_title': 'Pub SEO',
            'meta_description': 'Published.',
            'publish_immediately': 'yes',
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json().get('published'))

    def test_post_with_intro_and_meta_keywords_roundtrip(self):
        payload = {
            'title': 'Full Meta Test',
            'meta_title': 'Full SEO',
            'meta_description': 'Full description.',
            'intro': 'Short intro text here.',
            'meta_keywords': 'keyword1, keyword2',
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        detail = _api_get(self.client, '/api/articles/%d/' % response.json()['id'])
        self.assertEqual(detail.json().get('intro'), 'Short intro text here.')
        self.assertEqual(detail.json().get('meta_keywords'), 'keyword1, keyword2')
        self.assertEqual(detail.json().get('meta_title'), 'Full SEO')
        self.assertEqual(detail.json().get('meta_description'), 'Full description.')

    def test_post_title_with_special_chars_slugified(self):
        payload = {
            'title': 'İçerik & Döngüsel Ekonomi — Test',
            'meta_title': 'Unicode SEO',
            'meta_description': 'Unicode test.',
        }
        response = _api_post(self.client, '/api/articles/', payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('slug', data)
        self.assertTrue(len(data['slug']) > 0)
        detail = _api_get(self.client, '/api/articles/%d/' % data['id'])
        self.assertIn('İçerik', detail.json().get('title', '') or '')


@override_settings(ARTICLE_API_SECRET='test-secret')
class GetArticleListAPITests(TestCase):
    def test_list_without_auth_returns_401(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 401)

    def test_list_with_auth_returns_200(self):
        response = _api_get(self.client, '/api/articles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIsInstance(data['results'], list)

    def test_list_limit_and_offset(self):
        response = _api_get(self.client, '/api/articles/?limit=2&offset=0')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data['results']), 2)
        if data['count'] > 2:
            self.assertIn('next_offset', data)
        response2 = _api_get(self.client, '/api/articles/?limit=1&offset=0')
        self.assertEqual(len(response2.json()['results']), min(1, response2.json()['count']))

    def test_list_filter_live(self):
        response = _api_get(self.client, '/api/articles/?live=true')
        self.assertEqual(response.status_code, 200)
        for item in response.json().get('results', []):
            self.assertTrue(item['live'])
        response_draft = _api_get(self.client, '/api/articles/?live=false')
        self.assertEqual(response_draft.status_code, 200)
        for item in response_draft.json().get('results', []):
            self.assertFalse(item['live'])

    def test_list_item_has_expected_fields(self):
        response = _api_get(self.client, '/api/articles/?limit=1')
        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', [])
        if results:
            item = results[0]
            for key in ('id', 'title', 'slug', 'url', 'intro', 'live', 'first_published_at', 'locale', 'main_image_url'):
                self.assertIn(key, item)


@override_settings(ARTICLE_API_SECRET='test-secret')
class GetArticleDetailAPITests(TestCase):
    def test_detail_without_auth_returns_401(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Detail Auth Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
        })
        self.assertEqual(response.status_code, 201)
        aid = response.json()['id']
        unauth = self.client.get('/api/articles/%d/' % aid)
        self.assertEqual(unauth.status_code, 401)

    def test_detail_not_found_returns_404(self):
        response = _api_get(self.client, '/api/articles/999999/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_detail_returns_all_expected_fields(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Detail Fields Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
            'intro': 'Intro',
            'body': '## Hi\n\nParagraph.',
        })
        self.assertEqual(response.status_code, 201)
        detail = _api_get(self.client, '/api/articles/%d/' % response.json()['id'])
        self.assertEqual(detail.status_code, 200)
        data = detail.json()
        for key in ('id', 'title', 'slug', 'url', 'intro', 'body', 'main_image_url', 'meta_title',
                    'meta_description', 'meta_keywords', 'live', 'first_published_at', 'last_published_at', 'locale'):
            self.assertIn(key, data)


@override_settings(ARTICLE_API_SECRET='test-secret')
class PatchArticleAPITests(TestCase):
    def test_patch_without_auth_returns_401(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Patch Auth Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
        })
        self.assertEqual(response.status_code, 201)
        aid = response.json()['id']
        unauth = self.client.patch('/api/articles/%d/' % aid, data='{"title":"New"}', content_type='application/json')
        self.assertEqual(unauth.status_code, 401)

    def test_patch_not_found_returns_404(self):
        response = _api_patch(self.client, '/api/articles/999999/', {'title': 'New'})
        self.assertEqual(response.status_code, 404)

    def test_patch_invalid_json_returns_400(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Patch JSON Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
        })
        aid = response.json()['id']
        response = self.client.patch(
            '/api/articles/%d/' % aid,
            data='not json',
            content_type='application/json',
            HTTP_X_API_KEY='test-secret',
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_title_updates(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Original Title',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
        })
        aid = response.json()['id']
        patch = _api_patch(self.client, '/api/articles/%d/' % aid, {'title': 'Updated Title'})
        self.assertEqual(patch.status_code, 200)
        detail = _api_get(self.client, '/api/articles/%d/' % aid)
        self.assertEqual(detail.json().get('title'), 'Updated Title')

    def test_patch_body_updates_and_roundtrips(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Patch Body Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
            'body': 'Old body.',
        })
        aid = response.json()['id']
        patch = _api_patch(self.client, '/api/articles/%d/' % aid, {
            'body': '## New Section\n\nNew content with **formatting**.',
        })
        self.assertEqual(patch.status_code, 200)
        detail = _api_get(self.client, '/api/articles/%d/' % aid)
        body = detail.json().get('body', '')
        self.assertIn('New Section', body)
        self.assertIn('New content', body)
        self.assertIn('formatting', body)

    def test_patch_live_to_false_response(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Patch Live Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
            'publish_immediately': True,
        })
        aid = response.json()['id']
        patch = _api_patch(self.client, '/api/articles/%d/' % aid, {'live': False})
        self.assertEqual(patch.status_code, 200)
        self.assertFalse(patch.json().get('published'))

    def test_patch_intro_and_meta_fields(self):
        response = _api_post(self.client, '/api/articles/', {
            'title': 'Patch Meta Test',
            'meta_title': 'SEO',
            'meta_description': 'Desc',
        })
        aid = response.json()['id']
        _api_patch(self.client, '/api/articles/%d/' % aid, {
            'intro': 'New intro.',
            'meta_title': 'New SEO',
            'meta_description': 'New description.',
            'meta_keywords': 'new, keywords',
        })
        detail = _api_get(self.client, '/api/articles/%d/' % aid)
        self.assertEqual(detail.json().get('intro'), 'New intro.')
        self.assertEqual(detail.json().get('meta_title'), 'New SEO')
        self.assertEqual(detail.json().get('meta_description'), 'New description.')
        self.assertEqual(detail.json().get('meta_keywords'), 'new, keywords')
