from django.test import TestCase
from django.urls import reverse


class MarketViewTest(TestCase):
    def test_market_home_view_exists(self):
        # Si vous avez une URL publish ou root, adaptez la route
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])

