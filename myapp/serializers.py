from rest_framework import serializers
from .models import Category, Article, Comment, Like, UserProfile
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
    
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return f"http://localhost:8000{obj.profile_picture.url}"
        return None
    
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            # Fallback if request context is missing
            try:
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                return f"{base_url}{obj.profile_picture.url}"
            except:
                return None
        return None

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': False}
        }
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'profile']
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# Add this new serializer for comment creation
class CommentCreateSerializer(serializers.ModelSerializer):
    article = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all())
    
    class Meta:
        model = Comment
        fields = ['content', 'article', 'parent']
        extra_kwargs = {
            'content': {'required': True},
            'article': {'required': True},
            'parent': {'required': False}
        }

    def validate(self, data):
        if not data.get('article'):
            raise serializers.ValidationError("Article ID is required")
        return data

# Update the existing CommentSerializer
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'article', 'user', 'content', 'parent', 'replies', 
                 'created_at', 'likes', 'is_liked']
        read_only_fields = ['user', 'created_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

    def get_article(self, obj):
        return {
            'id': obj.article.id,
            'title': obj.article.title,
            'url': f'/articles/{obj.article.id}'
        }

    def get_likes(self, obj):
        return obj.like_set.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_set.filter(user=request.user).exists()
        return False

class ArticleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()
    views = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'thumbnail', 'content', 'category', 'category_id', 'author', 'comments', 'likes', 'views', 'created_at']

    def get_likes(self, obj):
        return obj.like_set.count()

class UserRegistrationSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    profile_picture = serializers.ImageField(write_only=True, required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'bio', 'profile_picture']

    def create(self, validated_data):
        bio = validated_data.pop('bio', '')
        profile_picture = validated_data.pop('profile_picture', None)
        user = User.objects.create_user(**validated_data)
        # Use get_or_create to handle existing profiles
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'bio': bio, 'profile_picture': profile_picture}
        )
        return user