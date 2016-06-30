from django.conf.urls import patterns, url
from .views import UploadURLView, UploadFileView, SelectView
from . import views


urlpatterns = patterns('',
	url(r'^$', views.SelectView, name="select-view"),
    url(r'^upload-url$', UploadURLView.as_view(), name="upload-url"),
    url(r'^upload-file$', UploadFileView.as_view(), name="upload-file-url"),

)

#views.UploadFileView