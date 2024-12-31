from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

from rest_framework import viewsets, permissions
from .models import Project, File, Comparison, Session
from .serializers import UserSerializer, ProjectSerializer, FileSerializer, ComparisonSerializer, SessionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

class CustomTokenObtainPairView(TokenObtainPairView):
    """Customized TokenObtainPairView to include additional user details."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])
            response.data["user_id"] = user.id
            response.data["username"] = user.username
        return response


class RegisterView(APIView):
    permission_classes = [AllowAny]  # Ensure this view is publicly accessible

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        User.objects.create_user(username=username, password=password)
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only projects belonging to the authenticated user
        return Project.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

# class ComparisonViewSet(viewsets.ModelViewSet):
#     queryset = Comparison.objects.all()
#     serializer_class = ComparisonSerializer
#     permission_classes = [permissions.IsAuthenticated]

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]


class ComparisonViewSet(viewsets.ModelViewSet):
    queryset = Comparison.objects.all()
    serializer_class = ComparisonSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Comparison.objects.filter(project__user=self.request.user)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def create_files_and_comparison(self, request):
        try:
            project_id = request.data.get('project')
            if not project_id:
                return Response(
                    {"error": "Project ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate project
            project = Project.objects.get(id=request.data["project"], user=request.user)
            return(print("hello_world"))
            # Save file1
            file1 = File.objects.create(
                name=request.data["file1_name"],
                type=request.data["file1_type"],
                file_data=request.data["file1_data"].read(),  # Read binary data
                project=project,
            )
            
            # Save file2
            file2 = File.objects.create(
                name=request.data["file2_name"],
                type=request.data["file2_type"],
                file_data=request.data["file2_data"].read(),  # Read binary data
                project=project,
            )

            # Get result and highlighted differences data if provided
            result_data = None
            if 'result_data' in request.data:
                result_data = request.data["result_data"].read()

            highlighted_differences_data = None
            if 'highlighted_differences_data' in request.data:
                highlighted_differences_data = request.data["highlighted_differences_data"].read()

            # Save comparison
            comparison = Comparison.objects.create(
                project=project,
                file1=file1,
                file2=file2,
                comparison_type=request.data["comparison_type"],
                result_url=None,  # No longer using URLs
                highlighted_differences_file=highlighted_differences_data,
            )

            # Serialize and return the comparison
            serializer = ComparisonSerializer(comparison)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found or does not belong to the user."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )