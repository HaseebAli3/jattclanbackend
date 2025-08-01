from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
      path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
path('comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    path('comments/', views.CommentListView.as_view(), name='comment_list'),
    path('like/', views.LikeView.as_view(), name='like'),
    path('suspend-user/<int:user_id>/', views.SuspendUserView.as_view(), name='suspend_user'),
]