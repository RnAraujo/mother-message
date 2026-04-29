from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('students/create/', views.create_student, name='create_student'),
    path('students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('students/<int:student_id>/qr/', views.view_qr, name='view_qr'),
    path('students/<int:student_id>/card/', views.student_card, name='student_card'),
    path('students/<int:student_id>/qr/download/', views.download_qr, name='download_qr'),
    path('students/<int:student_id>/qr/generate/', views.generate_and_download_qr, name='generate_download_qr'),
    path('students/<int:student_id>/qr/image/', views.view_qr_image, name='view_qr_image'),
    path('students/<int:student_id>/qr/pdf/', views.download_qr_pdf, name='download_qr_pdf'),
]
