from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='Test-slug',
            description='Test-desription',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-text',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.post = PostModelTest.post
        self.group = PostModelTest.group
        expected_object = (
            (self.post, self.post.text[0:15]), (self.group, self.group.title)
        )
        for field, expected_object_value in expected_object:
            with self.subTest(field=field):
                self.assertEqual(str(field), expected_object_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым модель пост."""
        self.post = PostModelTest.post
        field_verboses = (
            ('text', 'описание поста'),
            ('author', 'автор поста')
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        self.post = PostModelTest.post
        field_help_texts = (
            ('group', 'Группа, к которой будет относиться пост'),
            ('text', 'Введите текст поста')
        )
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
