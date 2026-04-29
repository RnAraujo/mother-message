from django.contrib import admin
from .models import Student, UserLimit

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['first_name', 'last_name', 'user__username']
    readonly_fields = ['qr_code']

@admin.register(UserLimit)
class UserLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'max_students', 'current_count']
    list_editable = ['max_students']