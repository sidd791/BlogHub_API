from celery import shared_task
from .models import Post, Follow, Author
from django.core.mail import send_mail
from django.conf import settings



@shared_task
def notify_author_of_new_comment(post_id, comment_content):

    post = Post.objects.get(id=post_id)
    author = post.author

    print(f"Notification: {author.user.email} - A new comment was added to your post: '{post.title}'")
    print(f"Comment content: {comment_content}")


@shared_task
def notify_readers_of_new_post(author_id, post_title):

    author = Author.objects.get(id=author_id)
    followers = Follow.objects.filter(author=author)

    for follow in followers:
        reader_email = follow.reader.user.username
        print(f"Notification:{author.user.username} published or updated a new post: '{post_title}'")

from django.core.mail import EmailMessage

@shared_task
def send_password_reset_email(subject, message, recipient_email):
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.content_subtype = 'html'  # Ensuring the email is sent as HTML
    email.send(fail_silently=False)
    print("Mail sent")


