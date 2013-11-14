import logging

from django import forms
from django.contrib.contenttypes.models import ContentType

from form_utils.forms import BetterForm

from formable.builder.models import FormStructure

log = logging.getLogger(__name__)

class FormStructureForm(forms.ModelForm):
    """
    Form for creating a new form structure.
    """
    title = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'form_structure_title'}))
    structure = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'form_structure_data'}))
    type = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'form_structure_type'}))
    
    class Meta:
        model = FormStructure
        fields = ['title', 'structure', 'type']
        
class ListForPublishForm(forms.Form):
    """
    Form for creating a select field consisting the available structures for publishing
    """
    records = FormStructure.objects.all().values_list('id', 'title')
    struct_id = forms.ChoiceField(records)

class CloneFormForm(forms.Form):
    """
    Creates a dropdown containing the created form structures
    """
    form_structure = forms.ChoiceField(FormStructure.objects.all()
        .values_list('id', 'title'))
  
class ViewFormForm(BetterForm):
    """
    Creates a form based on the saved form structure. Parses the JSON and creates
    a new form structure that can be rendered by Django.
    """
    base_fieldsets = None
        
    def __init__(self, fieldsets, fields, *args, **kwargs):
        self.base_fieldsets = fieldsets
        super(ViewFormForm, self).__init__(*args, **kwargs)
        self.fields = fields