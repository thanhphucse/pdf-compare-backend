from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

from rest_framework import viewsets, permissions
from .models import Project, File, Comparison, Session
from .serializers import UserSerializer, ProjectSerializer, FileSerializer, ComparisonSerializer, SessionSerializer
from rest_framework.permissions import IsAuthenticated

from .pagination import CustomPageNumberPagination

from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

# views.py
from django.http import HttpResponse
import base64
from rest_framework.decorators import api_view

from django.contrib.auth import update_session_auth_hash

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.check_password(request.data.get('current_password')):
            return Response({'error': 'Current password is incorrect'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(request.data.get('new_password'))
        user.save()
        update_session_auth_hash(request, user)  # Keep user logged in
        return Response({'message': 'Password updated successfully'})

@api_view(['GET'])
def serve_file(request, file_id):
    try:
        file = File.objects.get(id=file_id)
        if file.type == 'image':
            # Convert binary to base64 for images
            base64_data = base64.b64encode(file.file_data).decode('utf-8')
            return Response({
                'data': f'data:image/jpeg;base64,{base64_data}',
                'type': 'image'
            })
        elif file.type == 'text':
            # Decode text data
            text_content = file.file_data.decode('utf-8')
            return Response({
                'data': text_content,
                'type': 'text'
            })
        elif file.type == 'pdf':
            # Serve PDF as binary
            response = HttpResponse(file.file_data, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{file.name}"'
            return response
            
    except File.DoesNotExist:
        return Response({'error': 'File not found'}, status=404)


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
    pagination_class = CustomPageNumberPagination

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = Project.objects.filter(user=self.request.user)
        # Add ordering
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return File.objects.filter(project__user=self.request.user).order_by('-created_at')

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return Session.objects.filter(user=self.request.user).order_by('-created_at')


class ComparisonViewSet(viewsets.ModelViewSet):
    queryset = Comparison.objects.all()
    serializer_class = ComparisonSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['comparison_type', 'project']

    def get_queryset(self):
        return Comparison.objects.filter(project__user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def create_files_and_comparison(self, request):
        try:
            # project_id = request.data.get('project')
            project = Project.objects.get(id=request.data["project"], user=request.user)
            print(request.data["file1_data"])
            # Save file1
            try:
                file1 = File.objects.create(
                    name=request.data["file1_name"],
                    type=request.data["file1_type"],
                    file_data=request.data["file1_data"].read(),  # Read binary data
                    project=project,
                )
                print(f"File1 created with ID: {file1.id}")
            except Exception as e:
                print("Error creating file1:", e)
                return Response({"error": "Error creating file1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Save file2
            try:
                file2 = File.objects.create(
                    name=request.data["file2_name"],
                    type=request.data["file2_type"],
                    file_data=request.data["file2_data"].read(),  # Read binary data
                    project=project,
                )
                print(f"File2 created with ID: {file2.id}")
            except Exception as e:
                print("Error creating file2:", e)
                return Response({"error": "Error creating file2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save comparison
            try:
                result_data = request.data.get("result_data", None)
                # if result_data:
                #     result_data = result_data.read()

                highlighted_differences_data = request.data.get("highlighted_differences_data", None)
                if highlighted_differences_data:
                    highlighted_differences_data = highlighted_differences_data.read()

                comparison = Comparison.objects.create(
                    project=project,
                    file1=file1,
                    file2=file2,
                    comparison_type=request.data["comparison_type"],
                    result_url=result_data,
                    highlighted_differences_file=highlighted_differences_data,
                )
                print(f"Comparison created with ID: {comparison.id}")
            except Exception as e:
                print("Error creating comparison:", e)
                return Response({"error": "Error creating comparison"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
