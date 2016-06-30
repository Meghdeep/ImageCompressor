from django.db import models
import os, datetime
from django.utils.text import slugify

UPLOAD_PATH = "acceptor/images/"

class UploadedImage(models.Model):
    def generate_upload_path(self, filename):
        filename, ext = os.path.splitext(filename.lower())
        filename = "%s.%s%s" % (slugify(filename),datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S"), ext)
        return '%s/%s' % (UPLOAD_PATH, filename)

    image = models.ImageField(blank=True, null=True, upload_to=generate_upload_path)


class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')