# Ejemplo tomado desde
# http://www.stavros.io/posts/python-fuse-filesystem/
#
# Uso:
# python example.py /un/directorio /punto/de/montaje

from __future__ import with_statement

import os
import shutil # Borrar directorios
import sys
import errno
import inspect
import time

# Depurar 
def decorador(f):
    def decorada(*args, **kwargs):
        if inspect.ismethod(f):
            print time.time(), f.__name__, args[1:], kwargs
        elif inspect.isfunction(f):
            print time.time(), f.__name__, args[1:], kwargs

        return f(*args, **kwargs)
    return decorada


try:
    from fuse import FUSE, FuseOSError, Operations
except ImportError:
    print "Falta fusepy. Asegurarse de haber ejecutado"
    print "sudo apt-get install python-pip"
    print "y luego"
    print "sudo pip install fusepy"
    sys.exit(1)


class Passthrough(Operations):
    def __init__(self, root):
        self.root = root

    # Helpers
    # =======
    #@decorador
    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================
    @decorador
    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)
    @decorador
    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)
    @decorador
    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)
    @decorador
    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
    @decorador
    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r
    @decorador
    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname
    @decorador
    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)
    @decorador
    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)
    @decorador
    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)
    @decorador
    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
    @decorador
    def unlink(self, path):
        return os.unlink(self._full_path(path))
    @decorador
    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))
    @decorador
    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))
    @decorador
    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    @decorador
    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============
    @decorador
    def open(self, path, flags):

        full_path = self._full_path(path)
        return os.open(full_path, flags)

    @decorador
    def create(self, path, mode, fi=None):

        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    @decorador
    def read(self, path, length, offset, fh):

        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    @decorador
    def write(self, path, buf, offset, fh):

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)
    @decorador
    def truncate(self, path, length, fh=None):

        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    @decorador
    def flush(self, path, fh):
        return os.fsync(fh)

    @decorador
    def release(self, path, fh):
        return os.close(fh)

    @decorador
    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    msg = ("A partir de este momento los archivos de {} se reflejan"
           " en {}").format(root, mountpoint)
    print msg
    FUSE(Passthrough(root), mountpoint, foreground=True)

if __name__ == '__main__':
    punto_de_montaje = './punto_de_montaje'
    raiz = './raiz'
    if os.path.isdir(punto_de_montaje):
        print "Borrando {}".format(punto_de_montaje) 
        shutil.rmtree(punto_de_montaje)
    os.mkdir(punto_de_montaje)
    if not os.path.isdir(raiz):
        print "Falta crear {}".format(raiz)
        sys.exit(1)
    main(punto_de_montaje, raiz)


