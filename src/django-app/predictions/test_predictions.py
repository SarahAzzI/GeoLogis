from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch


class PredictionApiTest(TestCase):
    def test_predict_endpoint_returns_200(self):
        client = APIClient()

        response = client.post("/api/predictions/", {
            "prix_m2": 3000,
            "property_tax": 1000,
            "last_year_property_tax": 900,
            "population": 50000
        }, format="json")

        self.assertIn(response.status_code, [200, 201])

    @patch('predictions.views.requests.get')
    @patch('predictions.views.fake_prediction')
    def test_predict_view_post_with_geo(self, mock_fake_prediction, mock_requests_get):
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = [{
            'nom': 'Testville',
            'centre': {'coordinates': [2.35, 48.85]},
            'population': 100000,
            'contour': {"type": "FeatureCollection", "features": []}
        }]
        mock_fake_prediction.return_value = 1

        response = APIClient().post("/api/predictions/", {'zipcode': '75000'}, format='json')
        self.assertIn(response.status_code, [200, 201])


class PredictionModelTest(TestCase):
    def test_get_predictions_empty(self):
        client = APIClient()
        response = client.get("/api/predictions/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
