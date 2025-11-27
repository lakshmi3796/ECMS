from django import forms
from .models import Campaign
from django.core.validators import FileExtensionValidator

class CampaignForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Optional — set a future time to schedule sending."
    )

    class Meta:
        model = Campaign
        fields = ['name', 'subject', 'content', 'scheduled_at', 'status']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
            'status': forms.Select()
        }

class RecipientUploadForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv','xlsx'])],
        help_text='CSV with columns: name,email OR Excel (.xlsx)'
    )
