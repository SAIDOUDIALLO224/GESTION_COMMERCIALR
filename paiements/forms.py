from django import forms
from .models import CompteEcoBanqueClient


class CompteEcoBanqueClientForm(forms.ModelForm):
    class Meta:
        model = CompteEcoBanqueClient
        fields = ['client', 'montant_verset', 'montant_initial', 'montant_restant', 'montant_sorti', 'date_operation', 'motif']
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3}),
            'montant_verset': forms.NumberInput(attrs={'step': '0.01'}),
            'montant_initial': forms.NumberInput(attrs={'step': '0.01'}),
            'montant_restant': forms.NumberInput(attrs={'step': '0.01'}),
            'montant_sorti': forms.NumberInput(attrs={'step': '0.01'}),
            'date_operation': forms.DateInput(attrs={'type': 'date'}),
        }