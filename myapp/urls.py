from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
      path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('profile/<int:id>/', views.UserProfileView.as_view(), name='user_profile'),
path('comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    path('comments/', views.CommentListView.as_view(), name='comment_list'),
    path('like/', views.LikeView.as_view(), name='like'),
    path('users/<int:user_id>/make-admin/', views.MakeAdminView.as_view(), name='make_admin'),
    path('suspend-user/<int:user_id>/', views.SuspendUserView.as_view(), name='suspend_user'),
]