import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Leo')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-desription',
        )
        cls.post = Post.objects.create(
            text='Test-text',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()
        cls.comment = Comment.objects.create(
            text='Test-comment',
            author=cls.user,
            post=cls.post
        )
        cls.form_comment = CommentForm

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверим создание поста через форму"""
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Test-form',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.group)
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.user.username,))
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Test-form',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit_post(self):
        """Проверяем редактирование поста """
        post_count = Post.objects.count()
        self.new_group = Group.objects.create(
            title='Test-title',
            slug='New-group',
            description='Test-desription',
        )
        form_data = {
            'text': 'New-text',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,)))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.new_group)
        self.assertEqual(post.text, form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text='New-text',
                group=self.new_group.id,
            ).exists()
        )

    def test_guest_not_create_post(self):
        """Гость не может создать пост """
        post_count = Post.objects.count()
        response_login = reverse('users:login')
        url = (
            f'{response_login}?next={reverse("posts:post_create", args=None)}'
        )
        form_data = {
            'text': 'Test-form',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)

    def test_create_comments(self):
        """Проверяем создание комментария через форму"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Test-form-comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        comments = Comment.objects.order_by('-pk').first()
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comments.author_id, self.post.author_id)
        self.assertEqual(comments.post_id, self.post.id)
        self.assertEqual(comments.text, form_data['text'])

    def test_guest_not_create_comments(self):
        """Гость не может создать комментарий"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Test-form-comment',
        }
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
