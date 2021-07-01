import shutil
import os
import subprocess

from sh import cpio
from sh import basename
from sh import gunzip
from sh import cp
from sh import chown

DEPPATH='/home/user/BigMAC/ExtractDep/atsh_setup' #Location of folder that contains IMGTOOL
IMGTOOL=str(DEPPATH)+'/imgtool/imgtool.ELF64' #Specific location of IMGTOOL
#DEPPATH does not need to be used if a full path to IMGTOOL is provided

MY_FULL_DIR='' #Directory in which extractions are placed
SUB_DIR='' #Directory of this specific extraction
EXTUSER='' #User given ownership of extraction
EXTGROUP='' #Group given ownership of extraction

#get the first word from the file command
def getFormat(filename):
  formatProcess = subprocess.run(['file','-b', filename],stdout=subprocess.PIPE)
  return formatProcess.stdout.decode('utf-8').split()[0]

def getBasename(filename):
  return basename(filename).stdout.decode('utf-8').rstrip("\n")

def handle_bootimg(filename):
  name=getBasename(filename)
  if (name[:4] in ['boot','hosd','BOOT'] or
      name[:8] in ['recovery','fastboot','RECOVERY'] or
      name[:9] == 'droidboot' or
      name[:10] == 'okrecovery' or
      name[-4:] == '.bin'):
    subprocess.run([IMGTOOL, filename, 'extract'])
    os.chdir('extracted')
    format_ = getFormat('ramdisk')
    if (format_ == 'LZ4'):
      subprocess.run(['unlz4', 'ramdisk', 'ramdisk.out'], shell=True)
      subprocess.run(['cat', 'ramdisk.out', '|', 'cpio', '-i'], shell=True)
      os.remove('ramdisk.out')
    elif (format_ == 'gzip'):
      cpio(gunzip('ramdisk','-c'),'-i')
    shutil.rmtree('ramdisk')
    os.chdir('..')
    cp('-r', 'extracted', MY_FULL_DIR + '/' + SUB_DIR + '/' + name)
    chown('-R', EXTUSER + ':' + EXTGROUP, MY_FULL_DIR + '/' + SUB_DIR + '/' + name)
    shutil.rmtree("extracted")
  else:
    print('This image file is not known and should be handled as a binary')
