from django import forms

from . models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", 'image')
        labels = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        help_texts = {
            'text': 'Любой текст',
            'group': 'выбрать из уже существующих'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Любой текст',
        }
