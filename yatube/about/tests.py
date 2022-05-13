from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class AboutModelTest(TestCase):
    def setUp(self):
        self.urls_names_templates = (
            ('/about/author/', 'about:author', None, 'about/author.html'),
            ('/about/tech/', 'about:tech', None, 'about/tech.html')
        )

    def test_urls_template_exists_at_desired_location(self):
        """
        Url адрес существует в нужном месте.
        Url адрес использует соотвествующий шаблон.
        Проверка доступности reverse and url.
        """
        for url, name, arg, template in self.urls_names_templates:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=arg))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
                reverse_name = reverse(name, args=arg)
                self.assertEqual(reverse_name, url)
