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
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import CategorySerializer, ArticleSerializer, CommentSerializer, UserRegistrationSerializer, UserProfileSerializer, UserSerializer,ProfileUpdateSerializer, CommentCreateSerializer

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
class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
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
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = request.user.profile
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        
        # Handle profile picture
        if 'profile_picture' in request.data:
            if request.data['profile_picture'] == 'null':
                if profile.profile_picture:
                    profile.profile_picture.delete()
                profile.profile_picture = None
            else:
                if profile.profile_picture:
                    profile.profile_picture.delete()
                profile.profile_picture = request.data['profile_picture']
        
        # Handle bio
        if 'bio' in request.data:
            profile.bio = request.data['bio']
        
        profile.save()
        
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)



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

# Update the CommentCreateView
class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentCreateSerializer  # Use the new serializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        article_id = self.request.query_params.get('article')
        user_id = self.request.query_params.get('user')
        
        queryset = Comment.objects.all()
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.select_related('article', 'user').order_by('-created_at')
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
            like, created = Like.objects.get_or_create(
                user=request.user,
                article_id=article_id,
                defaults={'comment': None}
            )
            if not created:
                like.delete()
        elif comment_id:
            like, created = Like.objects.get_or_create(
                user=request.user,
                comment_id=comment_id,
                defaults={'article': None}
            )
            if not created:
                like.delete()
        
        return Response(status=status.HTTP_201_CREATED)

class SuspendUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            if user.is_staff:
                return Response(
                    {'error': 'Cannot suspend admin users'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.delete()

            return Response(
                {'message': f'User account {"suspended" if not user.is_active else "activated"}'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )