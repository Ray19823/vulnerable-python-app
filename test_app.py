import unittest
from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Vulnerable Python Demo App', response.data)

    def test_execute_route(self):
        response = self.app.get('/execute?cmd=echo test')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
