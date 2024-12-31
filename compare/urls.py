from django.urls import path, include
from . import viewsImage
from . import viewsPdf
from .views import CustomTokenObtainPairView
from .views import RegisterView
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProjectViewSet, FileViewSet, ComparisonViewSet, SessionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'files', FileViewSet, basename='file')
router.register(r'comparisons', ComparisonViewSet, basename='comparison')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('compare-images/', viewsImage.compare_images, name='compare_images'),
    path('compare-pdfs/', viewsPdf.compare_pdfs, name='compare_pdfs'),
    # path('projects/', ProjectView.as_view(), name='projects'),
    # path('projects/<int:project_id>/documents/', DocumentView.as_view(), name='documents'),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path('', include(router.urls)),
]
