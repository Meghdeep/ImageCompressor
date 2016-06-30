import mimetypes
import http
import requests
import os
import io
import mimetypes as mi
from io import BytesIO
from urllib.parse import urlparse
from django.core.files.base import ContentFile
import datetime
import zipfile
from django.http import HttpResponse
from PIL import Image
import xlrd
from openpyxl.reader.excel import load_workbook
import urllib.request

MAX_SIZE = 4*1024*1024
VALID_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
]
VALID_IMAGE_MIMETYPES = [
    "image"
]


def split_url(url):
    parse_object = urlparse(url)
    return parse_object.netloc, parse_object.path

def get_url_tail(url):
    return url.split('/')[-1]

def get_extension(filename):
    return os.path.splitext(filename)[1]

def valid_url_extension(url, extension_list=VALID_IMAGE_EXTENSIONS):
    '''
    A simple method to make sure the URL the user has supplied has
    an image-like file at the tail of the path
    '''
    return any([url.endswith(e) for e in extension_list])


def get_mimetype(fobject):
    '''
    Guess mimetype of a file using python-magic
    
    mime = magic.Magic(mime=True)
    mimetype = mime.from_buffer(fobject.read(1024))
    fobject.seek(0)
    '''

    return mi.guess_type(fobject)


def valid_url_mimetype(url, mimetype_list=VALID_IMAGE_MIMETYPES):
    '''
    As an alternative to checking the url extension, a basic method to
    check the image file in the URL the user has supplied has an
    image mimetype
    - https://docs.python.org/2/library/mimetypes.html
    '''
    mimetype, encoding = mi.guess_type(url)
    if mimetype:
        return any([mimetype.startswith(m) for m in mimetype_list])
    else:
        return False


def valid_image_mimetype(get_object):
    mimetype = get_object.headers['content-type']
    if mimetype:
        if 'image' in mimetype:
            return True
    else:
        return False

def image_exists(domain, path, check_size=False, size_limit=1024):
    '''
    Make a HEAD request to the remote server to make sure the image
    actually exists before downloading. Also, check the headers sent
    back to check the image size
    - http://stackoverflow.com/q/5616102/396300
    '''
    try:
        conn = http.client.HTTPConnection(domain)
        conn.request('HEAD', path)
        response = conn.getresponse()
        headers = response.getheaders()
        conn.close()
    except:
        return False

    try:
        length = int([x[1] for x in headers if x[0] == 'content-length'][0])
    except:
        length = 0
    if length > MAX_SIZE:
        return False

    return response.status == 200


def retrieve_image(url):
    '''Download the image from the remote server'''
    return requests.get(url)

def valid_image_size(image, max_size=MAX_SIZE):
    width, height = image.size
    if (width * height) > max_size:
        return (False, "Image is too large")
    return (True, image)

def pil_to_django(image, format="JPEG"):
    img_file = io.BytesIO()
    image.save(img_file, format=format)
    return ContentFile(img_file.getvalue())

def multiple_compressor(file_list):
    zip_name = 'acceptor/zips/image_archive_%s.zip'%(datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S"))
    with zipfile.ZipFile(zip_name , 'w') as myzip:
        for image_file in file_list:
            myzip.write(image_file)
    myzip.close()
    return zip_name

def compressor(file_name):
    zip_name = 'acceptor/zips/image_archive_%s.zip'%(datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S"))
    s = io.BytesIO()
    z = zipfile.ZipFile(s, 'w')
    z.write(file_name)
    z.close()
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_name
    resp['Content-length'] = s.tell()

    return resp

#if f.content_type in ["image/jpg", "image/jpeg", "image/png", "image/gif"]:

def file_image_handler(f):
    zipped_file = io.BytesIO()
    with zipfile.ZipFile(zipped_file, 'w') as file:
        img_ftype = f.content_type[6:]
        img = Image.open(f)
        i = io.BytesIO()
        img.save(i, img_ftype)
        file.writestr( "zipped_image.%s"%(img_ftype), i.getvalue() )
    resp = HttpResponse(zipped_file.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % "image_zipped.zip"
    resp['Content-length'] = zipped_file.tell()
    return resp

        
def file_text_handler(f):
    url_list = f.read().decode("utf-8").split('\n')
    count = 1
    zipped_file = io.BytesIO()
    with zipfile.ZipFile(zipped_file, 'w') as file:
        for url in url_list:
            if url == '':
                continue
            img_ftype = image_filetype(url)
            domain, path = split_url(url)
            filename = get_url_tail(path)

            if not image_exists(domain, path):
                return HttpResponse("Couldn't retreive image. (There was an error reaching the server)")

            get_object = retrieve_image(url)
            if not valid_image_mimetype(get_object):
                return HttpResponse("Downloaded file was not a valid image")
            img = Image.open(BytesIO(urllib.request.urlopen(url).read()))
            i = io.BytesIO()
            img.save(i, img_ftype)
            file.writestr( "%d.%s"%(count, img_ftype), i.getvalue() )
            count = count + 1

    resp = HttpResponse(zipped_file.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % "images_text_urls.zip"
    resp['Content-length'] = zipped_file.tell()
    return resp


def file_xls_handler(f):
    #"application/vnd.ms-excel":
    url_list = []
    file = io.BytesIO()
    for chunk in f.chunks():
        file.write(chunk)
    xls_filename = "url_list.xls"
    with open(xls_filename, 'wb') as xls:         ## Excel File
            xls.write(file.getvalue())             
    book = xlrd.open_workbook(xls_filename)
    sheet = book.sheet_by_index(0)
    num_rows = sheet.nrows 
    if num_rows != 0:
        for i in range(num_rows):
            url_list.append(sheet.cell(i,0).value)
    else:
        return HttpResponse("Empty Excel Sheet")
    os.remove(xls_filename)
    count = 1
    zipped_file = io.BytesIO()
    with zipfile.ZipFile(zipped_file, 'w') as file:
        for url in url_list:
            if url == '':
                continue
            img_ftype = image_filetype(url)
            domain, path = split_url(url)
            filename = get_url_tail(path)

            if not image_exists(domain, path):
                return _invalidate(_("Couldn't retreive image. (There was an error reaching the server)"))

            get_object = retrieve_image(url)
            if not valid_image_mimetype(get_object):
                return _invalidate(_("Downloaded file was not a valid image"))
            img = Image.open(BytesIO(urllib.request.urlopen(url).read()))
            i = io.BytesIO()
            img.save(i, img_ftype)
            file.writestr( "%d.%s"%(count, img_ftype), i.getvalue() )
            count = count + 1

    resp = HttpResponse(zipped_file.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % "images_xls_urls.zip"
    resp['Content-length'] = zipped_file.tell()
    return resp



def image_filetype(url):
    temp = mimetypes.guess_type(url)[0]
    if temp.startswith("image/"):
        return temp[6:]




