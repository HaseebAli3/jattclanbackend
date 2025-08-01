from rest_framework import serializers
from .models import Category, Article, Comment, Like, UserProfile
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'profile']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'article', 'user', 'content', 'parent', 'replies', 'created_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

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
        UserProfile.objects.create(user=user, bio=bio, profile_picture=profile_picture)
        return user