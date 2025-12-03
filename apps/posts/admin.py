from django.contrib import admin
from .models import Post, PostComment, PostLike, CommentLike


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'caption', 'created_at')
    search_fields = ('author__username', 'caption')
    list_filter = ('created_at',)

class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'created_at')
    search_fields = ('author__username', 'content')
    list_filter = ('created_at',)

    
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'created_at')
    search_fields = ('author__username',)
    list_filter = ('created_at',)


class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'author', 'created_at')
    search_fields = ('author__username',)
    list_filter = ('created_at',)


admin.site.register(Post, PostAdmin)
admin.site.register(PostComment, PostCommentAdmin)
admin.site.register(PostLike, PostLikeAdmin)
admin.site.register(CommentLike, CommentLikeAdmin)