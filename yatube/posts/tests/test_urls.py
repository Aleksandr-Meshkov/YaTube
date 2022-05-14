
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Leo')
        cls.user_2 = User.objects.create_user(username='Peter')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-desription',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-text',
        )
        cls.templates_args_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (cls.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),

        )
        cls.names_args_urls = (
            ('posts:index', None, '/'),
            ('posts:group_list', (cls.group.slug,),
             f'/group/{cls.group.slug}/'),
            ('posts:profile', (cls.user.username,),
             f'/profile/{cls.user.username}/'),
            ('posts:post_detail', (cls.post.id,), f'/posts/{cls.post.id}/'),
            ('posts:post_edit', (cls.post.id,), f'/posts/{cls.post.id}/edit/'),
            ('posts:post_create', None, '/create/'),
            ('posts:add_comment', (cls.post.id,),
             f'/posts/{cls.post.id}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow', (cls.user.username,),
             f'/profile/{cls.user.username}/follow/'),
            ('posts:profile_unfollow', (cls.user.username,),
             f'/profile/{cls.user.username}/unfollow/'),
            ('posts:post_delete', (cls.post.id,),
             f'/posts/{cls.post.id}/delete/'),
        )

    def setUp(self):
        self.test_client_author = Client()
        self.test_client_author.force_login(self.user)
        self.test_client_not_author = Client()
        self.test_client_not_author.force_login(self.user_2)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        response_login = reverse('users:login')
        for name, arg, _ in self.templates_args_names:
            with self.subTest(name=name):
                target_url = (
                    f'{response_login}?next={reverse(name, args=arg)}'
                )
                if name in [
                    'posts:post_edit',
                    'posts:post_create',
                    'posts:follow_index'
                ]:
                    response = (
                        self.client.get(reverse(name, args=arg), follow=True)
                    )
                    self.assertRedirects(response, target_url)
                else:
                    response_name = self.client.get(reverse(name, args=arg))
                    self.assertEqual(response_name.status_code, HTTPStatus.OK)

    def test_urls_authorized_exists_at_desired_location(self):
        """Страницы доступны авторизованному пользователю(автора)."""
        for name, arg, _ in self.templates_args_names:
            with self.subTest(name=name):
                response = self.test_client_author.get(reverse(name, args=arg))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_not_exists_at_desired_location(self):
        """Страницa '/unnexisting_page/' не имеет нужного адреса"""
        response = self.client.get('/unnexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for name, arg, template in self.templates_args_names:
            with self.subTest(name=name):
                response = (
                    self.test_client_author.
                    get(reverse(name, args=arg))
                )
                self.assertTemplateUsed(response, template)

    def test_reverse_uses_correct_url(self):
        """Проверка доступности reverse"""
        for name, argument, url in self.names_args_urls:
            with self.subTest(name=name):
                reverse_name = reverse(name, args=argument)
                self.assertEqual(reverse_name, url)

    def test_urls_exists_at_desired_location_for_not_author(self):
        """Страницы доступны авторизованному пользователю(не автору)."""
        response_post = reverse('posts:post_detail', args=(self.post.id,))
        for name, arg, _ in self.templates_args_names:
            with self.subTest(name=name):
                if name == 'posts:post_edit':
                    response = (
                        self.test_client_not_author.get(
                            reverse(name, args=arg), follow=True)
                    )
                    self.assertRedirects(response, response_post)
                else:
                    response_name = self.test_client_not_author.get(
                        reverse(name, args=arg)
                    )
                    self.assertEqual(response_name.status_code, HTTPStatus.OK)
