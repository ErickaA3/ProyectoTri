from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('txt', 'Texto'),
        ('pdf', 'PDF'),
        ('doc', 'Word'),
        ('manual', 'Texto Manual'),
    ]
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    original_file = models.FileField(upload_to='documents/', null=True, blank=True)
    original_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.title

class Summary(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Resumen de {self.document.title}"
