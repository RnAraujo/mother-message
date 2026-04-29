from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os

def user_directory_path(instance, filename):
    return f'users/{instance.user.id}/{filename}'

class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=100, verbose_name='Nombres')
    last_name = models.CharField(max_length=100, verbose_name='Apellidos')

    photo = models.ImageField(
        upload_to=user_directory_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        verbose_name='Foto'
    )

    audio = models.FileField(
        upload_to=user_directory_path,
        validators=[FileExtensionValidator(['mp3', 'wav', 'ogg'])],
        verbose_name='Audio'
    )

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        verbose_name='Código QR'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('student_detail', kwargs={'student_id': self.id})

class UserLimit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_limit')
    max_students = models.IntegerField(default=50, verbose_name='Límite máximo de estudiantes')
    
    def __str__(self):
        return f"{self.user.username} - Límite: {self.max_students}"
    
    @property
    def current_count(self):
        return self.user.students.count()
    
    @property
    def can_add_more(self):
        return self.current_count < self.max_students
