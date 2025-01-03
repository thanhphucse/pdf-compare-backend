from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, File, Comparison, Session

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

class ProjectSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'user', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FileSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    class Meta:
        model = File
        fields = ['id', 'name', 'type', 'url', 'project','project_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'project_name']

class ComparisonSerializer(serializers.ModelSerializer):
    file1 = FileSerializer()
    file2 = FileSerializer()
    project_name = serializers.ReadOnlyField(source='project.name')
    file1_name = serializers.ReadOnlyField(source='file1.name')
    file2_name = serializers.ReadOnlyField(source='file2.name')
    file1_id = serializers.ReadOnlyField(source='file1.id')
    file2_id = serializers.ReadOnlyField(source='file2.id')

    class Meta:
        model = Comparison
        fields = [
            'id', 'project', 'project_name', 
            'file1', 'file1_name', 'file1_id',
            'file2', 'file2_name', 'file2_id',
            'comparison_type', 
            'result_url', 'highlighted_differences_file',
            'created_at'
        ]
        read_only_fields = ['created_at', 'project_name', 'file1_name', 'file2_name', 'file1_id', 'file2_id']


class SessionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Session
        fields = ['id', 'user', 'token', 'expires_at', 'created_at']
        read_only_fields = ['created_at']
