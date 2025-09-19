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
        labels = {
            'titulo': 'Título del Esquema',
            'tipo': 'Tipo de Esquema'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['tipo'].required = True
        self.fields['contenido_texto'].required = True
        
        # Agregar opciones mejoradas para tipo
        self.fields['tipo'].choices = [
            ('', 'Selecciona el tipo de esquema'),
            ('jerarquico', 'Esquema Jerárquico - Organiza información en niveles'),
            ('conceptual', 'Mapa Conceptual - Conecta ideas y conceptos'),
            ('cronologico', 'Línea de Tiempo - Ordena eventos cronológicamente'),
        ]

    def clean_contenido_texto(self):
        contenido = self.cleaned_data.get('contenido_texto')
        if contenido:
            # Validar longitud mínima
            if len(contenido.strip()) < 50:
                raise forms.ValidationError('El contenido debe tener al menos 50 caracteres.')
            
            # Validar longitud máxima
            if len(contenido) > 10000:
                raise forms.ValidationError('El contenido no puede exceder 10,000 caracteres.')
        
        return contenido

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            if len(titulo.strip()) < 3:
                raise forms.ValidationError('El título debe tener al menos 3 caracteres.')
            if len(titulo) > 200:
                raise forms.ValidationError('El título no puede exceder 200 caracteres.')
        
        return titulo.strip()


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
        labels = {
            'titulo': 'Título del Esquema',
            'tipo': 'Tipo de Esquema'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['tipo'].required = True
        
        # Agregar opciones mejoradas para tipo
        self.fields['tipo'].choices = [
            ('', 'Selecciona el tipo de esquema'),
            ('jerarquico', 'Esquema Jerárquico - Organiza información en niveles'),
            ('conceptual', 'Mapa Conceptual - Conecta ideas y conceptos'),
            ('cronologico', 'Línea de Tiempo - Ordena eventos cronológicamente'),
        ]

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
            
            # Validar que el archivo no esté vacío
            if archivo.size == 0:
                raise forms.ValidationError('El archivo está vacío.')
        
        return archivo

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            if len(titulo.strip()) < 3:
                raise forms.ValidationError('El título debe tener al menos 3 caracteres.')
            if len(titulo) > 200:
                raise forms.ValidationError('El título no puede exceder 200 caracteres.')
        
        return titulo.strip()


class FiltroEsquemasForm(forms.Form):
    """Formulario para filtrar esquemas en la vista de mis esquemas"""
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar esquemas...',
            'id': 'searchInput'
        }),
        label='Buscar'
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos los tipos'),
            ('jerarquico', 'Jerárquico'),
            ('conceptual', 'Conceptual'),
            ('cronologico', 'Cronológico'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filterSelect'
        }),
        label='Tipo'
    )
    
    fuente = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas las fuentes'),
            ('texto', 'Desde texto'),
            ('archivo', 'Desde archivo'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'sourceFilter'
        }),
        label='Fuente'
    )


class EditarEsquemaForm(forms.ModelForm):
    """Formulario para editar un esquema existente"""
    class Meta:
        model = Esquema
        fields = ['titulo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del esquema'
            }),
        }
        labels = {
            'titulo': 'Título del Esquema'
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            if len(titulo.strip()) < 3:
                raise forms.ValidationError('El título debe tener al menos 3 caracteres.')
            if len(titulo) > 200:
                raise forms.ValidationError('El título no puede exceder 200 caracteres.')
        
        return titulo.strip()