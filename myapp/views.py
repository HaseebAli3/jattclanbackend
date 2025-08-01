from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied
from .models import Category, Article, Comment, Like, UserProfile
from .serializers import CategorySerializer, ArticleSerializer, CommentSerializer, UserRegistrationSerializer, UserProfileSerializer, UserSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = User.objects.get(username=request.data['username'])
        profile, created = UserProfile.objects.get_or_create(user=user)
        response.data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'profile': UserProfileSerializer(profile).data
        }
        return response

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'profile': UserProfileSerializer(user.profile).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class ArticleListView(generics.ListCreateAPIView):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Article.objects.all().order_by('-created_at')
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        if search:
            queryset = queryset.filter(Q(title__icontains=search))
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        article_id = self.request.query_params.get('article')
        if article_id:
            return Comment.objects.filter(article_id=article_id)
        return Comment.objects.none()
# Add to views.py
class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Allow author or admin to modify
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_update(self, serializer):
        if self.request.user == serializer.instance.user or self.request.user.is_staff:
            serializer.save()
        else:
            raise PermissionDenied("You don't have permission to edit this comment")

    def perform_destroy(self, instance):
        if self.request.user == instance.user or self.request.user.is_staff:
            instance.delete()
        else:
            raise PermissionDenied("You don't have permission to delete this comment")

class LikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        article_id = request.data.get('article_id')
        comment_id = request.data.get('comment_id')
        if article_id:
            Like.objects.get_or_create(user=request.user, article_id=article_id)
        elif comment_id:
            Like.objects.get_or_create(user=request.user, comment_id=comment_id)
        return Response(status=status.HTTP_201_CREATED)

class SuspendUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return Response({'message': 'User suspended'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)