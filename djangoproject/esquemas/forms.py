# esquemas/forms.py
from django import forms
from .models import Esquema

class CrearEsquemaTextoForm(forms.ModelForm):
    contenido_texto = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Pega o escribe aquí el contenido que quieres convertir en esquema...',
            'rows': 15,
            'style': 'min-height: 300px;'
        }),
        label='Contenido',
        help_text='Introduce el texto del cual quieres generar el esquema'
    )
    
    class Meta:
        model = Esquema
        fields = ['titulo', 'tipo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de tu esquema'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['tipo'].required = True


class CrearEsquemaArchivoForm(forms.ModelForm):
    archivo = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt'
        }),
        label='Archivo',
        help_text='Sube un archivo PDF, DOC, DOCX o TXT (máximo 10MB)',
        required=True
    )
    
    class Meta:
        model = Esquema
        fields = ['titulo', 'tipo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de tu esquema'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['tipo'].required = True

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño del archivo (10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo es demasiado grande. El tamaño máximo es 10MB.')
            
            # Validar extensión
            nombre = archivo.name.lower()
            extensiones_validas = ['.pdf', '.doc', '.docx', '.txt']
            if not any(nombre.endswith(ext) for ext in extensiones_validas):
                raise forms.ValidationError('Formato de archivo no válido. Solo se permiten PDF, DOC, DOCX y TXT.')
        
        return archivo