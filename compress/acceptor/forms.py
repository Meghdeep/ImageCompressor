from .utils import *

from django.utils.translation import ugettext as _
from django import forms
import mimetypes as mi


class UploadURLForm(forms.Form):
    url = forms.URLField(required=True,
        error_messages={
            "required": "Please enter a valid URL to an image (.jpg .jpeg .png)"
        },
    )

    def clean_url(self):
        url = self.cleaned_data['url'].lower()
        domain, path = split_url(url)
        if not valid_url_extension(url) or not valid_url_mimetype(url):
            raise forms.ValidationError(_("Not a valid Image. The URL must have an image extensions (.jpg/.jpeg/.png)"))
        return url



class UploadFileForm(forms.Form):
    docfile = forms.FileField(label='Select a File')
'''
    def clean(self):
        docfile = self.cleaned_data.get['docfile']
        VALID_FILE_EXTENSIONS = ["image/jpg", "image/jpeg", "image/png", "image/gif", "text/plain", "application/vnd.ms-excel", "text/csv"]
        if not docfile:
            raise forms.ValidationError(_("No file given as input"))
        elif docfile.content_type in VALID_FILE_EXTENSIONS:
            return docfile
        else:
           raise forms.ValidationError(_("Not a valid file type- only jpg, png, gif, txt, xls and csv accepted"))

'''