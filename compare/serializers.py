from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, File, Comparison, Session

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password_hash', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {'password_hash': {'write_only': True}}

class ProjectSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'user', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FileSerializer(serializers.ModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')
    class Meta:
        model = File
        fields = ['id', 'name', 'type', 'url', 'project', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ComparisonSerializer(serializers.ModelSerializer):
    project = serializers.ReadOnlyField(source='project.name')
    file1 = serializers.ReadOnlyField(source='file1.name')
    file2 = serializers.ReadOnlyField(source='file2.name')

    class Meta:
        model = Comparison
        fields = [
            'id', 'project', 'file1', 'file2', 'comparison_type', 
            'result_url', 'highlighted_differences_file', 'created_at'
        ]
        read_only_fields = ['created_at']

class SessionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Session
        fields = ['id', 'user', 'token', 'expires_at', 'created_at']
        read_only_fields = ['created_at']

# class ComparisonSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comparison
#         fields = [
#             'id', 'project', 'file1', 'file2', 'comparison_type', 
#             'result_url', 'highlighted_differences_url', 'created_at'
#         ]
#         read_only_fields = ['created_at']