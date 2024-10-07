from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [("author", "Author"), ("reader", "Reader")]
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default="reader")

    def __str__(self):
        return self.username


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()

    def get_posts(self):
        return self.posts.all()

    def __str__(self):
        return f"Author: {self.user}"


class Reader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def get_followed_authors(self):
        return self.follows.all()

    def __str__(self):
        return f"Reader: {self.user}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published')]
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default = 'draft')
    tags = models.ManyToManyField(Tag, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")

    def __str__(self):
        return f"{self.user} liked {self.post}"


class Follow(models.Model):
    reader = models.ForeignKey(Reader, related_name='follows', on_delete=models.CASCADE)
    author = models.ForeignKey(Author, related_name='followers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['reader', 'author']

    def __str__(self):
        return f"{self.reader} follows {self.author}"
