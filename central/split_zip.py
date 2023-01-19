import os
from zipfile import ZipFile

import psutil


def file_split(file: open, max_size, dest_path=None):
    """Split file into pieces, every size is max_size = 15*1024*1024 Byte"""
    buffer_memory = psutil.virtual_memory().available
    max_size = max_size * 1024 ** 2
    chapters = 1
    uglybuf = ''
    file_list = []
    path = os.path.dirname(__file__) + os.sep + file.name.split('/')[-1]
    while True:
        if dest_path is not None:
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
            if dest_path[-1] != os.sep:
                dest_path += os.sep
            path = os.path.join(dest_path, file.name.split('/')[-1])
        tgt = open(path + '.%03d' % chapters, 'wb')
        written = 0
        while written < max_size:
            if len(uglybuf) > 0: tgt.write(uglybuf)
            tgt.write(file.read(min(buffer_memory, max_size - written)))
            written += min(buffer_memory, max_size - written)
            uglybuf = file.read(1)
            if len(uglybuf) == 0: break
        tgt.close()
        file_list.append(open(tgt.name, 'rb'))
        if len(uglybuf) == 0: break
        chapters += 1
    return file_list


def zip_file(files: list, zip_name: str):
    zip = ZipFile(zip_name, 'w')
    [zip.write(file, file.split('/')[-1]) for file in files]
    return open(zip_name, 'rb')
