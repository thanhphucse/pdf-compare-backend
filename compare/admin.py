from django.contrib import admin
from .models import Project, File, Comparison, Session


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username')

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'project', 'created_at', 'updated_at')
    list_filter = ('type',)
    search_fields = ('name', 'project__name')

@admin.register(Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'file1', 'file2', 'comparison_type', 'created_at')
    list_filter = ('comparison_type',)
    search_fields = ('project__name', 'file1__name', 'file2__name')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'expires_at', 'created_at')
    search_fields = ('user__username', 'token')
