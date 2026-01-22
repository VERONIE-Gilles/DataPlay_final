from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.core.mail import send_mail
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_envoi', 'responded')
    list_filter = ('date_envoi', 'responded')
    search_fields = ('email', 'message')
    readonly_fields = ('email', 'message', 'date_envoi')

    # Champs à afficher dans le formulaire
    fields = ('nom', 'email', 'message', 'date_envoi', 'response', 'responded')

    def save_model(self, request, obj, form, change):
        # Si une réponse est ajoutée et le message n'a pas encore été répondu
        if obj.response and not obj.responded:
            send_mail(
                subject="Réponse à votre message",
                message=obj.response,
                from_email="votre.email@example.com",  # à remplacer
                recipient_list=[obj.email],
                fail_silently=False,
            )
            obj.responded = True
        super().save_model(request, obj, form, change)
# Register your models here.
