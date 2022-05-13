from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField('название группы', max_length=200)
    slug = models.SlugField('адрес группы', unique=True)
    description = models.TextField('описание группы')

    class Meta:
        verbose_name_plural = 'Сообщество'

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField('описание поста', help_text='Введите текст поста')
    pub_date = models.DateTimeField('дата публикации',
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name="группа поста",
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name_plural = 'публикация'

    def __str__(self) -> str:
        return self.text[0:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='коментарий к посту'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commets',
        verbose_name='автор поста'
    )
    text = models.TextField(
        'описание комментария', help_text='Введите текст комментария'
    )

    class Meta:
        verbose_name_plural = 'Комментарий'

    def __str__(self) -> str:
        return self.text[0:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь который подписывается'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор на которого подписываются'
    )

    class Meta:
        verbose_name_plural = 'Подписка'
