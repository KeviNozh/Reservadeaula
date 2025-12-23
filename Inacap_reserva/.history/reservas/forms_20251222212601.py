from django import forms
from django.core.exceptions import ValidationError
from .models import Reserva, Elemento, ElementoReserva
from django.utils import timezone

class ElementoForm(forms.ModelForm):
    class Meta:
        model = Elemento
        fields = [
            'nombre', 'descripcion', 'categoria', 'codigo_patrimonial',
            'marca', 'modelo', 'serie', 'cantidad_total', 'ubicacion',
            'fecha_adquisicion', 'valor', 'observaciones', 'imagen'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def clean_cantidad_total(self):
        cantidad = self.cleaned_data.get('cantidad_total')
        if cantidad < 1:
            raise ValidationError("La cantidad total debe ser al menos 1")
        return cantidad
    
    def save(self, commit=True):
        elemento = super().save(commit=False)
        # Al crear un nuevo elemento, la cantidad disponible es igual a la total
        if not elemento.pk:
            elemento.cantidad_disponible = elemento.cantidad_total
            elemento.estado = 'disponible' if elemento.cantidad_total > 0 else 'baja'
        
        if commit:
            elemento.save()
        return elemento

class ElementoReservaForm(forms.ModelForm):
    elemento_id = forms.IntegerField(widget=forms.HiddenInput())
    
    class Meta:
        model = ElementoReserva
        fields = ['cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control cantidad-elemento',
                'style': 'width: 80px;'
            })
        }

class ReservaElementosForm(forms.ModelForm):
    elementos_seleccionados = forms.ModelMultipleChoiceField(
        queryset=Elemento.objects.filter(estado='disponible', cantidad_disponible__gt=0),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'elemento-checkbox'}),
        required=False,
        label="Seleccionar elementos"
    )
    
    class Meta:
        model = Reserva
        fields = ['requiere_elementos', 'observaciones_elementos']
        widgets = {
            'observaciones_elementos': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Especificaciones adicionales sobre los elementos requeridos...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar elementos por categoría y nombre
        self.fields['elementos_seleccionados'].queryset = Elemento.objects.filter(
            estado='disponible', 
            cantidad_disponible__gt=0
        ).order_by('categoria', 'nombre')

# FORMULARIOS CORREGIDOS - USANDO SOLO CAMPOS QUE EXISTEN EN TU MODELO ORIGINAL

class ElementoPrestamoForm(forms.ModelForm):
    class Meta:
        model = ElementoReserva
        fields = ['fecha_prestamo', 'prestado']  # SOLO estos campos existen en tu modelo
        widgets = {
            'fecha_prestamo': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        labels = {
            'fecha_prestamo': 'Fecha y hora del préstamo',
            'prestado': 'Marcar como prestado'
        }

class ElementoDevolucionForm(forms.ModelForm):
    class Meta:
        model = ElementoReserva
        fields = ['fecha_devolucion', 'devuelto']  # SOLO estos campos existen en tu modelo
        widgets = {
            'fecha_devolucion': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        labels = {
            'fecha_devolucion': 'Fecha y hora de devolución',
            'devuelto': 'Marcar como devuelto'
        }