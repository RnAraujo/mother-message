import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from .forms import CustomUserCreationForm


def generate_qr_code(student):
    """Genera QR para un estudiante"""
    # URL completa para ver el estudiante
    base_url = settings.BASE_DIR  # En producción usar dominio real
    from django.urls import reverse
    relative_url = reverse('student_card', kwargs={'student_id': student.id})
    full_url = f"http://localhost:8000{relative_url}"  # Cambiar en producción
    
    # Crear QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar en memoria
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Guardar archivo
    filename = f'qr_student_{student.id}.png'
    student.qr_code.save(filename, ContentFile(buffer.read()), save=False)
    buffer.close()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})