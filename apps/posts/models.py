from django.db import models
from shared.models import BaseModel
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxLengthValidator


User = get_user_model()
# Create your models here.
class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='post_images/', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png','webp'])
        ])
    caption = models.TextField(validators=[MaxLengthValidator(2200)])

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return f'Post by {self.author.username} - {self.caption[:20]}'
        

class PostComment(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    content = models.TextField(validators=[MaxLengthValidator(1000)])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='child', null=True, blank=True)

    class Meta:
        db_table = 'post_comments'
        verbose_name = 'Post Comment'
        verbose_name_plural = 'Post Comments'

    def __str__(self):
        return f'Comment by {self.author.username} on Post {self.post.id}'


class PostLike(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')

    class Meta:
        db_table = 'post_likes'
        verbose_name = 'Post Like'
        verbose_name_plural = 'Post Likes'
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'author'], 
                name='unique_post_like'
            )
        ]

    def __str__(self):
        return f'Like by {self.author.username} on Post {self.post.id}'

class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        db_table = 'comment_likes'
        verbose_name = 'Comment Like'
        verbose_name_plural = 'Comment Likes'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'comment'], 
                name='unique_comment_like'
            )
        ]

    def __str__(self):
        return f'Like by {self.author.username} on Comment {self.comment.id}'