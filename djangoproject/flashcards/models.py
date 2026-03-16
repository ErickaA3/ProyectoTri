from django.db import models
import uuid

class FlashcardCollection(models.Model):
    DIFFICULTY_CHOICES = [
        ('facil', 'Fácil'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='facil')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_cards = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el contador de tarjetas
        self.total_cards = self.flashcards.count()
        if self.total_cards > 0:
            super().save(update_fields=['total_cards'])

class Flashcard(models.Model):
    collection = models.ForeignKey(
        FlashcardCollection, 
        on_delete=models.CASCADE, 
        related_name='flashcards'
    )
    question = models.TextField()
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.collection.title} - Card {self.order}"

class StudySession(models.Model):
    collection = models.ForeignKey(FlashcardCollection, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_cards = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Session: {self.collection.title} - {self.started_at}"
    
    @property
    def accuracy(self):
        if self.total_cards > 0:
            return round((self.correct_answers / self.total_cards) * 100, 1)
        return 0