import io
from zipfile import ZipFile

import requests


def gralwz_get(url):
    response = requests.get(url+"/gralwz").json()
    print("gralwz:", response)


def healthcheck_get(url):
    response = requests.get(url+"/healthcheck").json()
    print("healthcheck:", response)


def grammfile_get(url):
    response = requests.get(url+"/grammfile").json()
    print("grammfile:", response)


def gralfile_get(url) -> ZipFile | None:
    response = requests.get(url+"/gralfile")
    # print("gralfile:", response)

    if response.ok:
        return ZipFile(io.BytesIO(response.content))
