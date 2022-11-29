from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Текст для тестирования формы',
            'group': self.group.id
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Получим последний пост и явно сравним поля
        latest_post = Post.objects.latest('pub_date')
        self.assertEqual(latest_post.text, form_data['text'])
        self.assertEqual(latest_post.group.id, form_data['group'])
        self.assertEqual(latest_post.author.username, self.user.username)

    def test_edit_post(self):
        """Валидная форма вносит изменения в запись."""
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Текст для тестирования формы',
            'group': self.group.id
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, что запись изменилась
        edit_post = Post.objects.get(id=self.post.id)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group.id, form_data['group'])
        self.assertEqual(edit_post.author.username, self.user.username)
        self.assertEqual(edit_post.pub_date, self.post.pub_date)

    def test_authorized_client_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        form_data = {
            'text': 'Текст для тестирования комментария',
            'post': self.post.id
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        latest_comment = Comment.objects.latest('created')
        self.assertEqual(latest_comment.text, form_data['text'])
        self.assertEqual(latest_comment.post.id, form_data['post'])
        self.assertEqual(latest_comment.author.username, self.user.username)
