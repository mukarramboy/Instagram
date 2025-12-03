from .models import Post, PostComment, PostLike, CommentLike
from .serializers import PostSerializer, CommentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from shared.custom_pagination import CustomPagination

from drf_spectacular.utils import extend_schema, OpenApiExample


class PostListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
    
    def get(self, request):
        posts = Post.objects.all().order_by('-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(posts, request)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создать пост",
        description="Этот эндпоинт создаёт новый пост. Требуется авторизация.",
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: dict,   # если ошибка
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                summary="Создание простого поста",
                request_only=True,
                value={
                    "title": "Мой первый пост",
                    "content": "Это мой текст",
                }
            ),
            OpenApiExample(
                name="Пример ответа",
                summary="Что вернёт API",
                response_only=True,
                value={
                    "id": 1,
                    "title": "Мой первый пост",
                    "content": "Это мой текст",
                    "image": None,
                    "created_at": "2025-12-01T12:00:00Z"
                }
            ),
        ]
    )
    def post(self, request):
        serializer = PostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PostRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        if post.author != request.user:
            return Response({'detail': 'You do not have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        if post.author != request.user:
            return Response({'detail': 'You do not have permission to delete this post.'}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CommentListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get(self, request):
        comments = PostComment.objects.all().order_by('-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(comments, request)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CommentCreateView(APIView):
    def post(self, request):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CommentRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, id):
        try:
            comment = PostComment.objects.get(id=id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, id):
        try:
            comment = PostComment.objects.get(id=id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        if comment.author != request.user:
            return Response({'detail': 'You do not have permission to edit this comment.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(comment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        try:
            comment = PostComment.objects.get(id=id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        if comment.author != request.user:
            return Response({'detail': 'You do not have permission to delete this comment.'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class PostLikeToggleView(APIView):
    def post(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = PostLike.objects.get_or_create(post=post, author=request.user)
        if not created:
            like.delete()
            return Response({'detail': 'Post unliked.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Post liked.'}, status=status.HTTP_201_CREATED)
    

class CommentLikeToggleView(APIView):
    def post(self, request, comment_id):
        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            return Response({'detail': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = CommentLike.objects.get_or_create(comment=comment, author=request.user)
        if not created:
            like.delete()
            return Response({'detail': 'Comment unliked.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Comment liked.'}, status=status.HTTP_201_CREATED)