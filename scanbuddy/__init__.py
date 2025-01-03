import os
import tarfile
from . import __version__

def version():
   return __version__.__version__
 
def archive(indir, output):
    with tarfile.open(output, 'w:gz') as tar:
        tar.add(indir, os.path.basename(indir))
