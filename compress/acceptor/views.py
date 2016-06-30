from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from PIL import Image
import urllib.request
import re
from io import BytesIO
from django.views.generic.edit import FormView
from django.views.generic import DetailView
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from .forms import UploadURLForm, UploadFileForm
from .utils import *
from .models import UploadedImage

def SelectView(request):
    return render_to_response("upload.html")

class UploadURLView(FormView):
    form_class = UploadURLForm
    template_name = "upload-url.html"

    def form_valid(self, form):
        def _invalidate(msg):
            form.errors['url'] = [msg, ]
            return super(UploadURLView, self).form_invalid(form)

        url = form.data['url']
        domain, path = split_url(url)
        filename = get_url_tail(path)

        if not image_exists(domain, path):
            return _invalidate(_("Couldn't retreive image. (There was an error reaching the server)"))

        get_object = retrieve_image(url)
        if not valid_image_mimetype(get_object):
            return _invalidate(_("Downloaded file was not a valid image"))

        #pil_image = Image.open(get_object)
        pil_image = Image.open(BytesIO(urllib.request.urlopen(url).read()))
        #if not valid_image_size(pil_image)[0]:
        #    return _invalidate(_("Image is too large (> 4mb)"))
        ftype = image_filetype(url)
        django_file = pil_to_django(pil_image, ftype)
        self.uploaded_image = UploadedImage()
        self.uploaded_image.image.save(filename, django_file)
        self.uploaded_image.save()

        return compressor(self.uploaded_image.image.url)


class UploadDetailView(DetailView):
    model = UploadedImage
    context_object_name = "image"
    template_name = "detail.html"

    def form_valid(self, form):
        url = form.data['url']
        domain, path = split_url(url)
        filename = get_url_tail(path)


class UploadFileView(FormView):
    form_class = UploadFileForm
    template_name = "upload-file.html"

    def form_valid(self, form):
        def _invalidate(msg):
            form.errors['docfile'] = [msg, ]
            return super(UploadFileView, self).form_invalid(form)
        f = self.request.FILES['docfile']
        VALID_FILE_EXTENSIONS = ["image/jpg", "image/jpeg", "image/png", "image/gif", "text/plain", "application/vnd.ms-excel", "text/csv"]
        if f.content_type not in VALID_FILE_EXTENSIONS:
            return _invalidate(_("Incorrect File Type"))
        if f.content_type in ["image/jpg", "image/jpeg", "image/png", "image/gif"]:
            return file_image_handler(f)
        elif f.content_type == "text/plain" or f.content_type == "text/csv":
            return file_text_handler(f)
        elif f.content_type == "application/vnd.ms-excel":
            return file_xls_handler(f)