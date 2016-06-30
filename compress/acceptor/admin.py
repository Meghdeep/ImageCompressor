from django.contrib import admin

# Register your models here.

from .models import UploadedImage


class UploadedImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(UploadedImage, UploadedImageAdmin)