from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import Student, UserLimit
from .forms import StudentForm, CustomUserCreationForm
from .utils import generate_qr_code
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.files import File
from django.conf import settings
from PIL import Image
import qrcode
from io import BytesIO
import os
from .models import Student

def landing_page(request):
    return render(request, 'landing_page.html')

def register(request):
    """Registrar nuevo usuario"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cuenta creada exitosamente. Por favor inicia sesión.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    return render(request, 'registration/register.html', context)


@login_required
def dashboard(request):
    """Dashboard del usuario"""
    user_limit = UserLimit.objects.get(user=request.user)
    students = Student.objects.filter(user=request.user)
    
    # Calcular estadísticas
    total_students = user_limit.current_count
    available_spots = user_limit.max_students - total_students
    limit_percent = (total_students / user_limit.max_students) * 100 if user_limit.max_students > 0 else 0
    
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user_limit': user_limit,
        'page_obj': page_obj,
        'total_students': total_students,
        'available_spots': available_spots,
        'limit_percent': limit_percent,
    }
    return render(request, 'emotion/dashboard.html', context)


@login_required
def create_student(request):
    """Crear nuevo estudiante"""
    user_limit, created = UserLimit.objects.get_or_create(user=request.user)
    
    if not user_limit.can_add_more:
        messages.error(request, f'Has alcanzado el límite de {user_limit.max_students} estudiantes.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.save()
            
            # Generar QR
            generate_qr_code(student)
            student.save()
            
            messages.success(request, 'Estudiante registrado exitosamente.')
            return redirect('dashboard')
    else:
        form = StudentForm()
    
    context = {
        'form': form,
        'user_limit': user_limit,
    }
    return render(request, 'emotion/create_student.html', context)

@login_required
def edit_student(request, student_id):
    """Editar estudiante"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            # Regenerar QR si cambian datos importantes
            generate_qr_code(student)
            student.save()
            messages.success(request, 'Estudiante actualizado exitosamente.')
            return redirect('dashboard')
    else:
        form = StudentForm(instance=student)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'emotion/edit_student.html', context)

@login_required
def delete_student(request, student_id):
    """Eliminar estudiante"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    if request.method == 'POST':
        # Eliminar archivos físicos
        if student.photo:
            student.photo.delete()
        if student.audio:
            student.audio.delete()
        if student.qr_code:
            student.qr_code.delete()
        
        student.delete()
        messages.success(request, 'Estudiante eliminado exitosamente.')
        return redirect('dashboard')
    
    context = {'student': student}
    return render(request, 'emotion/confirm_delete.html', context)

@login_required
def view_qr(request, student_id):
    """Ver QR del estudiante"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    return render(request, 'emotion/view_qr.html', {'student': student})

def student_card(request, student_id):
    """Vista pública para mostrar el estudiante (al escanear QR)"""
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'emotion/student_card.html', {'student': student})



@login_required
def download_qr(request, student_id):
    """Descargar el código QR del estudiante"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    # Verificar si existe el QR
    if not student.qr_code:
        # Si no existe, generarlo
        from .utils import generate_qr_code
        generate_qr_code(student)
        student.save()
    
    # Verificar que el archivo existe físicamente
    if student.qr_code and os.path.exists(student.qr_code.path):
        # Abrir el archivo y devolverlo como descarga
        with open(student.qr_code.path, 'rb') as qr_file:
            response = HttpResponse(qr_file.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="qr_{student.first_name}_{student.last_name}.png"'
            return response
    else:
        messages.error(request, 'No se encontró el código QR.')
        return redirect('view_qr', student_id=student.id)

@login_required
def generate_and_download_qr(request, student_id):
    """Generar y descargar QR en diferentes formatos y tamaños"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    # Obtener parámetros de la URL
    size = request.GET.get('size', 'medium')  # small, medium, large
    format_type = request.GET.get('format', 'png')  # png, svg
    
    # Configurar tamaño según parámetro
    size_map = {
        'small': 200,
        'medium': 400,
        'large': 800
    }
    box_size = size_map.get(size, 400) // 40
    
    # URL completa para ver el estudiante
    from django.urls import reverse
    relative_url = reverse('student_card', kwargs={'student_id': student.id})
    full_url = request.build_absolute_uri(relative_url)
    
    # Crear QR
    qr = qrcode.QRCode(
        version=size_map.get(size, 400) // 100,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=2,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    
    # Generar imagen
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Redimensionar
    img = img.resize((size_map.get(size, 400), size_map.get(size, 400)), Image.Resampling.LANCZOS)
    
    # Guardar en memoria
    buffer = BytesIO()
    
    if format_type == 'svg':
        # Para SVG, necesitaríamos una biblioteca diferente
        # Por ahora usamos PNG
        img.save(buffer, format='PNG')
        content_type = 'image/svg+xml'
        file_extension = 'svg'
    else:
        img.save(buffer, format='PNG')
        content_type = 'image/png'
        file_extension = 'png'
    
    buffer.seek(0)
    
    # Crear respuesta
    response = HttpResponse(buffer, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="qr_{student.first_name}_{student.last_name}_{size}.{file_extension}"'
    
    return response

@login_required
def view_qr_image(request, student_id):
    """Ver la imagen QR en el navegador (no descargar)"""
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    if not student.qr_code or not os.path.exists(student.qr_code.path):
        from .utils import generate_qr_code
        generate_qr_code(student)
        student.save()
    
    if student.qr_code and os.path.exists(student.qr_code.path):
        with open(student.qr_code.path, 'rb') as qr_file:
            return HttpResponse(qr_file.read(), content_type='image/png')
    else:
        raise Http404("El código QR no existe")

@login_required
def download_qr_pdf(request, student_id):
    """Descargar QR en formato PDF con información adicional"""
    
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="qr_{student.first_name}_{student.last_name}.pdf"'
    
    # Crear PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    # Título
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 50, "Código QR - Estudiante")
    
    # Información del estudiante
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Nombre: {student.full_name}")
    p.drawString(50, height - 120, f"Fecha de registro: {student.created_at.strftime('%d/%m/%Y')}")
    
    # Cargar QR
    if student.qr_code and os.path.exists(student.qr_code.path):
        qr_img = ImageReader(student.qr_code.path)
        qr_size = 150
        qr_x = (width - qr_size) / 2
        qr_y = height - 300
        p.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
        
        # Instrucciones
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, qr_y - 20, "Escanea este código QR para ver la información")
        
        # URL
        from django.urls import reverse
        relative_url = reverse('student_card', kwargs={'student_id': student.id})
        full_url = request.build_absolute_uri(relative_url)
        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, qr_y - 40, full_url[:80])
    
    p.showPage()
    p.save()
    
    return response