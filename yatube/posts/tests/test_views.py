import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

COUNT_OF_POST: int = 13


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары 'имя_html_шаблона: reverse(name)'
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': f'{self.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': f'{self.user.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create.html'}
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_fields = {
            response.context.get('post').text: self.post.text,
            response.context.get('post').group: self.post.group,
            response.context.get('post').author: self.post.author,
            response.context.get('post').image: self.post.image,
        }
        for value, expected in post_fields.items():
            self.assertEqual(value, expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='Тестовый пост добавлен корректно',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                ).context['page_obj']
                self.assertIn(post, response)

    def test_cache_index(self):
        """Проверка кеширования главной страницы"""
        post = Post.objects.create(
            text='Проверка кеширования главной страницы',
            author=self.user,
            group=self.group,
        )
        reverse_name = reverse('posts:index')
        # Создаем пост и сохраняем контент страницы
        post.save()
        response1 = self.authorized_client.get(reverse_name).content
        # Удаляем пост и сохраняем контент страницы
        post.delete()
        response2 = self.authorized_client.get(reverse_name).content
        # Чистим кеш и сохраняем контент страницы
        cache.clear()
        response3 = self.authorized_client.get(reverse_name).content
        # Если после удаления поста он остался в кеше
        # то response1 равен response2
        self.assertEqual(response1, response2)
        # После очистки кеша response2 не равен response3
        self.assertNotEqual(response2, response3)


class PaginatorPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group'
        )
        bulk_post: list = []
        for number in range(COUNT_OF_POST):
            bulk_post.append(
                Post(
                    text=f'Тестовый текст {number}',
                    group=self.group,
                    author=self.user
                )
            )
        Post.objects.bulk_create(bulk_post)

    def test_correct_page_context_guest_client(self):
        """Проверка количества постов на первой и второй страницах."""
        reverse_names = (
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        for reverse_name in reverse_names:
            count_posts = {
                reverse_name: 10,
                reverse_name + '?page=2': 3,
            }
            for value, expected in count_posts.items():
                with self.subTest(value=value):
                    response = self.guest_client.get(value).context['page_obj']
                    self.assertEqual(len(response), expected)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(
            username='auth_author',
        )
        cls.user_follow = User.objects.create(
            username='auth_follow',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.user_follow)
        self.follow_client = Client()
        self.follow_client.force_login(self.user_author)

    def test_follow(self):
        """Проверка подписки на авторов."""
        follow_count = Follow.objects.count()
        response = self.follow_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_follow}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user_follow}
            )
        )
        latest_follow = Follow.objects.latest('id')
        self.assertEqual(latest_follow.user_id, self.user_author.id)
        self.assertEqual(latest_follow.author_id, self.user_follow.id)

    def test_unfollow(self):
        """Проверка отписки от авторов."""
        Follow.objects.create(
            user=self.user_author,
            author=self.user_follow
        )
        follow_count = Follow.objects.count()
        response = self.follow_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_follow}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user_follow}
            )
        )

    def test_posts_on_followers(self):
        """Проверка удаления авторов из подписок."""
        post = Post.objects.create(
            author=self.user_author,
            text='Тестовый текст'
        )
        Follow.objects.create(
            user=self.user_follow,
            author=self.user_author
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        post_object = response.context['page_obj']
        self.assertIn(post, post_object)

    def test_posts_on_unfollowers(self):
        """Новая запись появляется в ленте тех, кто на него подписан."""
        post = Post.objects.create(
            author=self.user_author,
            text='Тестовый текст'
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        post_object = response.context['page_obj']
        self.assertNotIn(post, post_object)
