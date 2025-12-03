from django.urls import path
from .views import PostListView, PostCreateView, PostRetrieveUpdateDeleteView, CommentListView, CommentCreateView, CommentRetrieveUpdateDeleteView,PostLikeToggleView, CommentLikeToggleView


urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<uuid:id>/', PostRetrieveUpdateDeleteView.as_view(), name='post-detail'),
    path('comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<uuid:id>/', CommentRetrieveUpdateDeleteView.as_view(), name='comment-detail'),
    path('<uuid:post_id>/like-toggle/', PostLikeToggleView.as_view(), name='post-like-toggle'),
    path('comments/<uuid:comment_id>/like-toggle/', CommentLikeToggleView.as_view(), name='comment-like-toggle'),  
]
