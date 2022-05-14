from cgitb import small
import shutil
import tempfile
from urllib import response

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.user_2 = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-desription',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-text',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Test-comment',
            post=cls.post
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.test_client_not_author = Client()
        self.test_client_not_author.force_login(self.user_2)

    def context_response_func(self, response, flag=False):
        if flag:
            first_object = response.context['post']
        else:
            first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.image, self.post.image)
        self.assertContains(response, '<img')

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for name, arg, template in self.templates_args_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=arg))
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.context_response_func(response)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (
            self.client.get(
                reverse('posts:group_list', args=(self.group.slug,)))
        )
        self.context_response_func(response)
        first_object = response.context['group']
        self.assertEqual(first_object.title, self.post.group.title)
        self.assertEqual(first_object.slug, self.post.group.slug)
        self.assertEqual(
            first_object.description, self.post.group.description
        )

    def test_profile_list_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,))
        )
        self.context_response_func(response)
        author_object = response.context['author']
        self.assertEqual(author_object, self.user)

    def test_post_detail_list_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.context_response_func(response, flag=True)
        first_object = response.context['comments'][0]
        self.assertEqual(first_object.text, self.comment.text)
        self.assertEqual(first_object.author_id, self.comment.author_id)
        self.assertEqual(first_object.post_id, self.comment.post_id)
        self.assertEqual(first_object.created, self.comment.created)

    def test_forms_page_show_correct_context(self):
        """Шаблоны с forms сформированы с правильным контекстом."""
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField)
        )
        url_forms = (
            ('posts:post_create', None), ('posts:post_edit', (self.post.id,))
        )
        for value, expected in form_fields:
            with self.subTest(value=value):
                for name, arg in url_forms:
                    with self.subTest(name=name):
                        response = (
                            self.authorized_client.get(reverse(name, args=arg))
                        )
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_not_in_new_group(self):
        """Тест, что пост не попал в новую группу"""
        self.new_post = Post.objects.create(
            author=self.user,
            text='Test-text',
            group=self.group,
        )
        new_group = Group.objects.create(
            title='Test-title',
            slug='black-stars',
            description='Test-desription',
        )
        response_new_group = self.authorized_client.get(
            reverse('posts:group_list', args=(new_group.slug,))
        )
        first_object = response_new_group.context['page_obj']
        self.assertEqual(response_new_group.status_code, HTTPStatus.OK)
        self.assertEqual(len(first_object), 0)

    def test_cahes_index_page(self):
        """Тестируем кэш главной страницы"""
        post = Post.objects.create(text='test_new_post', author=self.user,)
        response_one = self.authorized_client.get(reverse('posts:index'))
        post.delete()
        response_two = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_one.content, response_two.content)
        cache.clear()
        self.assertEqual(response_one.content, response_two.content)

    def test_follow_authorized_client(self):
        """User может подписываться и отписываться на авторов"""
        follow_count = Follow.objects.count()
        response = self.test_client_not_author.get(
            reverse('posts:profile_follow', args=(self.user.username,))
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.post.author)
        self.assertEqual(follow.user.username, self.user_2.username)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response_un = self.test_client_not_author.get(
            reverse('posts:profile_unfollow', args=(self.user.username,))
        )
        self.assertEqual(response_un.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_quest_client(self):
        """Гость не может оформить подписку"""
        follow_count = Follow.objects.count()
        self.client.get(
            reverse('posts:profile_follow', args=(self.user.username,))
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_author_not_following_author(self):
        """Автор не может оформить подписку сам на себя"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.user.username,))
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_context_follow_user(self):
        """Проверка ленты подписанных авторов"""
        Follow.objects.create(user=self.user_2, author=self.user)
        response = self.test_client_not_author.get(
            reverse('posts:follow_index')
        )
        first_object = response.context['page_obj'][0]
        response_other_client = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        first_object_other_client = response_other_client.context['page_obj']
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(len(first_object_other_client), 0)

    def test_user_delete_posts(self):
        """Автор может удалять посты """
        post_count = Post.objects.count()
        response = self.authorized_client.get(
            reverse('posts:post_delete', args = (self.post.id,))
        )
        self.assertEqual(Post.objects.count(), post_count - 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_guest_not_delete_posts(self):
        """Гость не может удалить пост"""
        post_count = Post.objects.count()
        response = self.client.get(
            reverse('posts:post_delete', args = (self.post.id,))
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-desription',
        )
        POST_COUNT = 13
        cls.PAGE_TWO = POST_COUNT - settings.TEN_POSTS
        for count in range(POST_COUNT):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Test-text number {count}',
                group=cls.group,
            )
        cls.names_args = (
            ('posts:index', None),
            ('posts:group_list', (cls.group.slug,)),
            ('posts:profile', (cls.user.username,)),
        )

    def test_paginator_test_page(self):
        """Тестируем паджинатор """
        for name, arg in self.names_args:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=arg))
                response_3 = self.client.get(
                    reverse(name, args=arg) + '?page=2'
                )
                self.assertEqual(
                    len(response.context['page_obj']), settings.TEN_POSTS
                )
                self.assertEqual(
                    len(response_3.context['page_obj']), self.PAGE_TWO
                )
