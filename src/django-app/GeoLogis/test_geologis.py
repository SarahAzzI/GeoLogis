from django.test import TestCase
from .models import Article


class ArticleModelTest(TestCase):
    def test_str_returns_title(self):
        article = Article.objects.create(title='Test', content='Contenu')
        self.assertEqual(str(article), 'Test')

    def test_date_auto_now_add(self):
        article = Article.objects.create(title='Test', content='Contenu')
        self.assertIsNotNone(article.published_date)

