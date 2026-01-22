from django.db import models
class ContactMessage(models.Model):
    nom = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)

    # Nouveaux champs
    response = models.TextField(blank=True, null=True)
    responded = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.date_envoi.strftime('%Y-%m-%d %H:%M')}"
# Create your models here.
