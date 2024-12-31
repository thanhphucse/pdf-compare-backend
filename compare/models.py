from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class File(models.Model):
    FILE_TYPES = [
        ('image', 'Image'),
        ('text', 'Text'),
        ('pdf', 'PDF'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_data = models.BinaryField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Comparison(models.Model):
    COMPARISON_TYPES = [
        ('image', 'Image'),
        ('text', 'Text'),
        ('pdf', 'PDF'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comparisons')
    file1 = models.ForeignKey(File, on_delete=models.CASCADE, related_name='comparison_file1')
    file2 = models.ForeignKey(File, on_delete=models.CASCADE, related_name='comparison_file2')
    comparison_type = models.CharField(max_length=10, choices=COMPARISON_TYPES)
    result_url = models.TextField(blank=True, null=True)
    highlighted_differences_file = models.BinaryField(blank=True, null=True)  # Store the file directly
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comparison {self.id} ({self.comparison_type})"

class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session for {self.user.username}"
