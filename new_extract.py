#!/usr/bin/python3

#variables must be set for EXTUSER, EXTGROUP, MY_DIR, MY_FULL_DIR, TOP_DIR, DEPPATH, and USEDEPPATH
#in addition to usual dependencies from old versions, add rarfile, zipfile, and sh through PIP
import os
import os.path
import sys
import subprocess
import argparse
import glob
import rarfile
import zipfile
import sh
import shutil

from subprocess import call
from os.path import expanduser
from zipfile import ZipFile

#CONNOR: sh commands to replace subprocess
from sh import rm
from sh import umount
from sh import mount
from sh import mkdir
from sh import cp
from sh import rmdir
from sh import ls
from sh import mv
from sh import basename
from sh import gunzip
from sh import cpio
from sh import find
from sh import chown
from sh import cat
from sh import simg2img

IMAGE = ''
VENDOR = ''
KEEPSTUFF = 0 # keep all the decompiled/unpackaged stuff for later analysis
VENDORMODE = 0 # should be provided as 0 unless alternate mode

#HOME = str(expanduser('~'))
HOME='/root'

EXTUSER = 'connor' #replace with valid user to use keepstuff functionality
EXTGROUP = 'connor' #replace with valid group to use keepstuff functionality
MY_TMP = 'extract.sum'
MY_OUT = 'extract.db'
MY_USB = 'extract.usb'
MY_PROP = 'extract.prop'

TIZ_LOG = 'tizen.log' # samsung
PAC_LOG = 'spd_pac.log' # lenovo
SBF_LOG = 'sbf.log' # moto
MZF_LOG = 'mzf.log' # moto
RAW_LOG = 'raw.log' # asus
KDZ_LOG = 'kdz.log' # lg
MY_DIR = 'extract3/'
MY_FULL_DIR = '/home/connor/BigMAC/extract3/' #replace with full directory for extraction ex: /home/user/BigMAC/extract
TOP_DIR = 'extract3' #the last folder of your extract
AT_CMD = 'AT\+|AT\*'
AT_CMD = 'AT\+|AT\*|AT!|AT@|AT#|AT\$|AT%|AT\^|AT&' # expanding target AT Command symbols

#These next ones need to be figured out
DIR_TMP = ''
MNT_TMP = ''
APK_TMP = ''
ZIP_TMP = ''
ODEX_TMP = ''
TAR_TMP = ''
MSC_TMP = ''

JAR_TMP = 'dex.jar'

DEPPATH='/home/connor/BigMAC/ExtractDep/atsh_setup'
USINGDEPPATH=1 # 1 = true, 0 = false

#SOME REQUIRE CHANGE MODE
DEX2JAR=str(DEPPATH)+'/dex2jar/dex-tools/target/dex2jar-2.1-SNAPSHOT/d2j-dex2jar.sh'
JDCLI=str(DEPPATH)+'/jd-cmd/jd-cli/target/jd-cli.jar'
# These are the most recent versions of baksmali/smali that work with java 7 (needed for JADX-nohang)
BAKSMALI=str(DEPPATH)+'/baksmali-2.2b4.jar'
SMALI=str(DEPPATH)+'/smali-2.2b4.jar'
JADX=str(DEPPATH)+'/jadx/build/jadx/bin/jadx'
# ~~~The following tools needed to unpack LG images: avail https://github.com/ehem/kdztools~~~
UNKDZ=str(DEPPATH)+'/kdztools/unkdz'
UNDZ=str(DEPPATH)+'/kdztools/undz'
UPDATA=str(DEPPATH)+'/split_updata.pl/splitupdate'
UNSPARSE=str(DEPPATH)+'/combine_unsparse.sh'
SDAT2IMG=str(DEPPATH)+'/sdat2img/sdat2img.py'
SONYFLASH=str(DEPPATH)+'/flashtool/FlashToolConsole'
SONYELF=str(DEPPATH)+'/unpackelf/unpackelf'
IMGTOOL=str(DEPPATH)+'/imgtool/imgtool.ELF64'
HTCRUUDEC=str(DEPPATH)+'/htcruu-decrypt3.6.5/RUU_Decrypt_Tool' # rename libcurl.so to libcurl.so.4
SPLITQSB=str(DEPPATH)+'/split_qsb.pl'
LESZB=str(DEPPATH)+'/szbtool/leszb' # szb format1 for lenovo
UNYAFFS=str(DEPPATH)+'/unyaffs/unyaffs' # yaffs2 format1 for sony

BOOT_OAT = ''
BOOT_OAT_64 = ''
SUB_SUB_TMP = 'extract_sub'
SUB_DIR = ''
CHUNKED = 0 # system.img
CHUNKEDO = 0 # oem.img
CHUNKEDU = 0 # userdata.img
COMBINED0 = 0 # system; may be a more elegant solution than this~
COMBINED1 = 0 # userdata
COMBINED2 = 0 # cache
COMBINED3 = 0 # factory or fac
COMBINED4 = 0 # preload
COMBINED5 = 0 # without_carrier_userdata
TARNESTED = 0

#########################
#    Argument Parser    #
#########################

def parse_arguments():
  parser = argparse.ArgumentParser(description = 'Android image extraction tool. Type \'Android Extract -h\' for more information')
  parser.add_argument('-f', dest='filepath', metavar='FIRMWARE IMG FILEPATH', type=str,
    help = 'Path to the top-level packaged archive')
  parser.add_argument('-vendor', dest='vendor', metavar='VENDOR NAME', type=str,
    help = 'The vendor who produced the firmware image (e.g., Samsung, LG)')
  parser.add_argument('-i', dest='index', metavar='INDEX', type=int, 
    help = 'To extract multiple images at the same time, temporary directories will need different indices. For best results, supply an integer value > 0')
  parser.add_argument('-ks', dest='keepstuff', metavar='KEEP STUFF? [0 OR 1]',type=int, 
    help = 'if 0, will remove any extracted files after Processing them;\nif 1, extracted files (e.g., filesystem contents, apps) will be kept')
  parser.add_argument('--vendor-mode', dest='vendormode', metavar='VENDOR MODE [0 OR 1]', type=int, 
    help = 'Supplying 1 as this optional argument will invoke an adjusted extraction')
  
  return parser.parse_args()

##############################################################################################

#########################
#       Help Menu       #
#########################

def print_how_to(): #Help menu
  print('This program must be run with AT LEAST the first 4 of the following options, 5th option is not mandatory:')
  print('-f <FILEPATH>                              : to define package filepath')
  print('-vendor <VENDOR NAME>                      : to define the vendor')
  print('-i <INDEX>                                 : to declare index number of directory')
  print('-ks <KEEP STUFF? [0 OR 1]>                 : to declare whether to remove extracted files after Processing')
  print('--vendor-mode <VENDOR MODE [0 OR 1]>       : to configure specific vendor related settings')

  fo2 = open('2', 'wt')

  print('ERROR: not enough arguments provided.',file=fo2)
  print('USAGE: ./atextract.sh <firmware image file> <vendor> <index> <keepstuff flag> <vendor mode (optional)>',file=fo2)
  print('          firmware image file = path to the top-level packaged archive (zip, rar, 7z, kdz, etc.)',file=fo2)
  print('                                (may be absolute or relative path)',file=fo2)
  print('          vendor = the vendor who produced the firmware image (e.g., Samsung, LG)',file=fo2)
  print('                   currently supported = samsung, lg, lenovo, zte, huawei, motorola, asus, aosp,',file=fo2)
  print('                                         nextbit, alcatel, blu, vivo, xiaomi, oneplus, oppo,',file=fo2)
  print('                                         lineage, htc, sony',file=fo2)
  print('          index = to extract multiple images at the same time, temporary directories will',file=fo2)
  print('                  need different indices. For best results, supply an integer value > 0.',file=fo2)
  print('          keepstuff = 0/1',file=fo2)
  print('                      if 0, will remove any extracted files after processing them',file=fo2)
  print('                      if 1, extracted files (e.g., filesystem contents, apps) will be kept',file=fo2)
  print('                            (useful for later manual inspection)',file=fo2)
  print('          vendor mode = some vendors will have several different image packagings',file=fo2)
  print('                        if so, supplying 1 as this optional argument will invoke an adjusted extraction',file=fo2)
  print('                        currently applies to:',file=fo2)
  print('                            password protected Samsung (.zip) image files from firmwarefile.com',file=fo2)
  print('                        extend as needed',file=fo2)
  print('', file=fo2)
  print('For additional guidance and a full list of dependencies, please refer to the provided README.',file=fo2)
  
  fo2.close()

#########################
#     Helper Methods    #
#########################

#removes files from previous run, if any
def clean_up():
 	  #umount(MNT_TMP, '-fl', '>', '/dev/null')
  files=subprocess.run(['ls', DIR_TMP],stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
  for f in files:
    if f.startswith('mnt'):
      try:
        umount('-fl', DIR_TMP + '/' + f)
      except:
        print('Failure to unmount: ' + f)

  if os.path.exists(DIR_TMP):
    shutil.rmtree(DIR_TMP)
  if os.path.exists(APK_TMP):
    shutil.rmtree(APK_TMP)
  if os.path.exists(ZIP_TMP):
    shutil.rmtree(ZIP_TMP)
  if os.path.exists(ODEX_TMP):
    shutil.rmtree(ODEX_TMP)
  if os.path.exists(TAR_TMP):
    shutil.rmtree(TAR_TMP)
  if os.path.exists(MSC_TMP):
    shutil.rmtree(MSC_TMP)

#get the first word from the file command
def getFormat(filename):
  formatProcess = subprocess.run(['file','-b', filename],stdout=subprocess.PIPE)
  return formatProcess.stdout.decode('utf-8').split()[0]

#get the second word from the file command
def getFormat2(filename):
  format2Process = subprocess.run(['file','-b', filename],stdout=subprocess.PIPE)
  try:
    return format2Process.stdout.decode('utf-8').split()[1]
  except:
    return None

def getBasename(filename):
  return basename(filename).stdout.decode('utf-8').rstrip("\n")

def getFiles():
  return subprocess.run(['ls'],stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()

def check_for_suffix(filename):
  suffix = filename[-4:]
  suffix2 = filename[-5:]
  
  if (suffix == '.apk' or suffix == '.APK' or suffix == '.Apk'
        or suffix == '.jar' or suffix == '.Jar' or suffix == '.JAR'):
    return 'java'
  elif (suffix2 == '.odex' or suffix2 == '.ODEX' or suffix2 == '.Odex'):
    return 'odex'
  else:
    return 'TBD'

#decompress the zip-like file
def at_unzip(filename, directory):
  format_=getFormat(filename)
  format2=getFormat2(filename)
  if (format_ in ['zip','Zip','ZIP']):
    if directory == None:         
      z = ZipFile(filename, 'r')
      z.extractall()
      z.close()
      return True
    else:
      z = ZipFile(filename, 'r')
      z.extractall(directory)
      z.close()
      return True
  elif(format == 'POSIX' and format2 == 'tar'):
    if directory is None:     
      subprocess.run(['tar', 'xvf', filename], shell=True)
    else:
      subprocess.run(['tar','xvf', filename, '-C', directory], shell=True)
    AT_RES = "good"
    return True
  else:
    return False

#########################
#    Handle Filetypes   #
#########################
def handle_text(filename):
  f=open(MY_TMP, 'a')
  with open(filename) as openfileobject:
    for line in openfileobject:
      for word in AT_CMD:
        if word in line:
          #CONNOR: FIX OUTPUT TO MATCH AWK COMMAND ON LINE 321
          f.write(line)

def handle_binary(filename):
  return
  f=open(MY_TMP, 'a')
  with open(filename, 'rb') as openfileobject:
    for line in openfileobject:
      for word in AT_CMD:
        if word in line.decode('utf-8'):
          #CONNOR: FIX OUTPUT TO MATCH AWK COMMAND ON LINE 321
          f.write(line)

#CONNOR: NEXT TWO ARE JUST USING BINARY IN PREVIOUS VERSION, MIGHT CHANGE LATER
def handle_elf(filename):
	handle_binary(filename)
	# Can run bingrep, elfparser but they suck...

def handle_x86(filename):
	# Currently no special handling for x86 boot sectors
	handle_binary(filename)

def handle_bootimg(filename):
  global KEEPSTUFF
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
    rm('ramdisk')
    os.chdir('..')
    find_output = find('extracted', '-print0').stdout.decode('utf-8').splitlines()
    for line in find_output:
      if (os.path.isfile(line)):
        format_ = getFormat('ramdisk')
        if (format_ == 'gzip'):
          mv(line, line, '.gz')
          gunzip('-f', line, '.gz')
          result = at_extract(line)
        else:
          result = at_extract(line)
        print(line + "processed: " + result)
    if ( KEEPSTUFF == 1 ):
      cp('-r', 'extracted', MY_FULL_DIR + '/' + SUB_DIR + '/' + name)
      chown('-R', EXTUSER + ':' + EXTGROUP, MY_FULL_DIR + '/' + SUB_DIR + '/' + name)
    shutil.rmtree("extracted")
  else:
    handle_binary(filename)

def handle_zip(filename, filetype):
  rtn = ''
  print('Unzipping ' + filename + ' ...')
  mkdir(ZIP_TMP)
  cp(filename,ZIP_TMP)
  if (filetype == 'zip'):
    z = ZipFile(ZIP_TMP, 'r')
    z.extractall(str(ZIP_TMP)+'/'+filename)
    z.close()
  elif (filetype == 'gzip'):
    if (filename[-7:] == '.img.gz'):
      print('Handling a .img.gz file... ')
      gzip = subprocess.run(['basename', filename, '.gz'], shell=True)
      subprocess.run('gunzip' + ' ' + '-c' + ' ' + str(ZIP_TMP)+'/'+filename,shell=True,stdout=open(str(ZIP_TMP)+'/'+str(gzip),'wb'))
    else:
      print('Handling a .tar.gz file... ')
      subprocess.run(['tar','xvf',str(ZIP_TMP)+'/'+filename,'-C',str(ZIP_TMP)],shell=True)
    if os.path.exists(ZIP_TMP+'/'+filename):
      shutil.rmtree(ZIP_TMP+'/'+filename)
    #Skipping while loop because AT command extraction is not necessary
    if (KEEPSTUFF == 1):
      subprocess.run(['sudo','cp','-r',str(ZIP_TMP),str(MY_FULL_DIR)+'/'+str(SUB_DIR)+'/'+filename],shell=True)
      subprocess.run(['sudo','chown','-R',str(EXTUSER)+':'+str(EXTGROUP),str(MY_FULL_DIR)+'/'+str(SUB_DIR)+'/'+filename],shell=True)
    os.rmdir(ZIP_TMP+'/'+filename)

def handle_vfat(img):
  global BOOT_OAT, BOOT_OAT_64
  ext = getBasename(img)
  mnt_name=MNT_TMP + '_' + ext
  os.makedirs(DIR_TMP, exist_ok=True)
  os.makedirs(mnt_name, exist_ok=True)
  cp(img, DIR_TMP + '/' + ext)
  try:
    mount('-o', 'ro', '-t', 'vfat', DIR_TMP + '/' + ext, mnt_name )
  except sh.ErrorReturnCode_32:
    print('error mounting vfat image: ' + ext)
  BOOT_OAT=''
  BOOT_OAT_64=''
  return True

def handle_ext4(img):
  global BOOT_OAT, BOOT_OAT_64
  ext = getBasename(img)
  mnt_name=MNT_TMP + '_' + ext
  os.makedirs(DIR_TMP, exist_ok=True)
  os.makedirs(mnt_name, exist_ok=True)
  cp(img, DIR_TMP + '/' + ext)
  try:
    mount('-o', 'ro', '-t', 'ext4', DIR_TMP + '/' + ext, mnt_name )
  except sh.ErrorReturnCode_32:
    print('error mounting vfat image: ' + ext)
  BOOT_OAT=''
  BOOT_OAT_64=''
  return True

def handle_simg(img):
  ext = getBasename(img)[:-4] + ".ext4"
  mnt_name=MNT_TMP + '_' + ext
  os.makedirs(DIR_TMP, exist_ok=True)
  os.mkdir(mnt_name)
  print('Converting to image: ' + img + ' ' + DIR_TMP +'/' + ext)
  simg2img(img,DIR_TMP +'/' + ext)
  mount('-o', 'ro', '-t', 'ext4', DIR_TMP + '/' + ext, mnt_name )
  return True

#########################
#      FILE EXTRACT     #
#########################
#Get AT commands from supported filetypes
def at_extract(filename):
  format_= getFormat(filename)
  justname = getBasename(filename)

  usbFile = open(MY_USB)
  propFile = open(MY_PROP)
  #tizFile = open(TIZ_LOG)

  if (justname == str(glob.glob('init*usb.rc'))):    # Save init file for USB config analysis
    # also need to capture e.g., init.hosd.usb.rc (notable: aosp sailfish)
    # there's also init.tuna.usb.rc in aosp yakju, etc.
    # init.steelhead.usb.rc in tungsten
    print(filename, file = usbFile)
    print('---------',file = usbFile)
    subprocess.run('cat' + ' ' + str(filename),shell=True,stdout=usbFile)
    print('=========',file=usbFile)

  elif (justname == 'build.prop' ):
    # Save the contents of build.prop to get information about OS version, etc.
    print(filename,file=propFile)
    print('---------',file=propFile)
    # in rare cases, permission denied when trying to access build.prop
    subprocess.run('sudo' + ' ' + 'cat' + ' ' + str(filename),shell=True,stdout=propFile)
    print('=========',file=propFile)

  elif ( VENDOR == 'samsung' ) and ( justname == 'dzImage' ):
    # Tizen OS image detected. Should abort
    # touch ../$MY_TIZ
    print(str(filename)+' processed: '+str('tizen'))
    print(IMAGE,file=tizFile)
    # for easier ID later, needs to be existing file
    exit(55)
    # exit immediately; no need to go further

  if(format_ in ['data', 'apollo','FoxPro,','Mach-O','DOS/MBR','PE32','PE32+','dBase','MS','PDP-11','zlib','ISO-8859','Composite','very','Hitachi','SQLite']):
    handle_binary(filename)
    return'good'
  elif (format_ == 'ELF'):
    handle_elf(filename)
    result = check_for_suffix(filename)
    if (result == 'odex'):
      handle_odex(filename)
    return 'good'
  elif (format_ == 'x86'):
    handle_x86(filename)
    return 'good'
  elif (format_ == 'DOS'):
    handle_text(filename)
    return 'good'
  elif (format_ == 'Java'):
    handle_java(filename)
    return 'good'
  elif (format_ in ['POSIX','Bourne-Again']):
    handle_text(filename)
    return 'good'
  elif (format_ in ['ASCII','XML', 'Tex','html','UTF-8','C','Pascal','python']):
    handle_text(filename)
    return 'good'
  elif (format_ == 'Windows'):
    handle_text(filename)
    return 'good'
  elif (format_ == 'Zip'):
    if (check_for_suffix(filename) == 'java'):
      handle_java(filename)
      return 'good'
    else:
      handle_zip(filename, 'zip')
      return 'good'
  elif (format_ in ['gzip','XZ']):
    handle_zip(filename, 'gzip')
    return 'good'
  elif (format_ == 'Android'):
    print('Processing .img file as binary!')
    handle_bootimg(filename)
    return 'good'
  elif (format_ in ['broken','symbolic','SE', 'empty', 'directory','Ogg',
    'PNG', 'JPEG', 'PEM', 'TrueType', 'LLVM', 'Device']):
    # format == dBase was being skipped before; now handled as binary (jochoi)
    # format == Device Tree Blob after extracting boot/recovery img; ignoring
    # Skip broken/symbolic/sepolicy/empty/dir/...
    return 'skip'
  else:
    return 'bad'


#########################
#  OS Specific Extracts #
#########################
def extract_aosp():
  print('handling AOSP images...')
  
  # Check for another zip file inside and unzip it
  print('checking for more zips inside...')
  files=getFiles()
  for f in files:
    unzipped = at_unzip(f, None)
    # Debug
    #print('$f at_unzip: $AT_RES'
    if (unzipped):
      print('Unzipped sub image: ' + f)
      # Remove the zip file
      os.remove(f)
  # Assume all the files will be flat in the same dir
  # without subdirs
  print('Extracting AT commands...')
  print('-------------------------')
  files=getFiles()
  for f in files:
    file_result=''
    justname = getBasename(f)
    # local format=`file -b $filename | cut -d' ' -f1`
    handled = False
    # echo 'Processing file: $filename' >> ../$MY_TMP # printing out the file being processed
    # echo 'IN process_file | handling file: $filename'
    if (justname in ['system.img', 'system_other.img', 'vendor.img']):
      #  Handle sparse ext4 fs image
      print('Processing sparse ext4 img...')
      print('-----------------------------')
      handle_simg(f)
      print('-----------------------------')
      handled = True
    elif(justname.startswith('radio') and justname.endswith('.img')):
      print('Processing vfat img...')
      print('-----------------------------')
      handle_vfat(f)
      print('-----------------------------')
    #---------------------------------------------------------------------------------
    if (handled == False):
      file_result=at_extract(f)
    #----------------------------------------------------------------------------------
    print(f + ' processed: ' + file_result)
  print('-------------------------')
    
def process_file_samsung(filename):
  global TARNESTED
  justname=getBasename(filename)
  samformat=getFormat(filename)
  if(justname.endswith('.img.ext4')):
    if(samformat == 'Linux'):
      print('Processing ext4 img...')
      print('-----------------------------')
      handle_ext4(filename)
      print('-----------------------------')
    else:
      print('Processing sparse ext4 img...')
      print('-----------------------------')
      handle_simg(filename)
      print('-----------------------------')
    return True
  elif(justname in ['cache.img', 'hidden.img', 'omr.img', 'hidden.img.md5', 'cache.img.md5', 'persist.img', 'factoryfs.img', 'vendor.img']):
    print('Processing sparse ext4 img...')
    print('-----------------------------')
    handle_simg(filename)
    print('-----------------------------')
    return True
  elif(justname in ['system.img', 'userdata.img','system.img.md5', 'userdata.img.md5']):
    if(samformat=='DOS/MBR'):
      print('Processing vfat img...')
      print('-----------------------------')
      handle_vfat(filename)
      print('-----------------------------')
    else:
      print('Processing sparse ext4 img...')
      print('-----------------------------')
      handle_simg(filename)
      print('-----------------------------')
    return True
  elif(justname == 'adspso.bin'):
      print('Processing ext4 img...')
      print('-----------------------------')
      handle_ext4(filename)
      print('-----------------------------')
      return True
  elif(justname in ['system.rfs','csc.rfs','efs.img','factoryfs.rfs','cache.rfs','hidden.rfs']):
      print('Processing vfat img...')
      print('-----------------------------')
      handle_vfat(filename)
      print('-----------------------------')
      return True
  elif(justname =='fota.zip'):
    print('Skipping password protected fota.zip')
    return True
  elif('.tar' in justname or '.TAR' in justname):
    TARNESTED = TARNESTED + 1
    os.mkdir('nestedPOSIXtar' + str(TARNESTED))
    ret = subprocess.run(["tar","xvf",str(filename),"-C","nestedPOSIXtar"+str(TARNESTED)],shell=True)
    os.chdir('nestedPOSIXtar' + str(TARNESTED))
    fileList=getFiles()
    for f in fileList:
      res=process_file_samsung(f)
      if res:
        print(f + ' processed: good')
      else:
        print(f + 'processed: bad')
    os.chdir('..')
    if str(ret) == "55":
      exit(55)
    print("-------------------------")
    os.rmdir("nestedPOSIXtar"+str(TARNESTED))
    TARNESTED=((TARNESTED - 1))
    return True
  return at_extract(filename)

def extract_samsung():
  print('handling Samsung images...')
  print('unarchiving each zip inside...')
  files=getFiles()
  for f in files:
    print('Attempting to untar ' + f)
    os.makedirs(TAR_TMP, exist_ok=True)
    res=at_unzip(f, TAR_TMP)
    if res:
      print('Unzipped sub image ' + f)
      currentDir=os.getcwd()
      os.chdir(TAR_TMP)
      files_tar=getFiles()
      for i in files_tar:
        res2= process_file_samsung(i)
        if res2:
          print(i + ' processed: good')
        else:
          print(i + 'processed: bad')
      os.chdir(currentDir)
    else:
      os.chdir(f)
      files_sub=getFiles()
      for i in files_sub():
        res2=process_file_samsung(i)
        if res2:
          print(i + ' processed: good')
        else:
          print(i + 'processed: bad')
      os.chdir('..')
    subprocess.run(["cp","-r",TAR_TMP,MY_FULL_DIR+"/"+SUB_DIR+"/"+os.popen("basename \""+str(f)+"\"").read().rstrip("\n")])
  return

#########################
#      MAIN FUNCTION    #
#########################
def main():
  global MY_TMP, MY_USB, MY_PROP, MY_OUT, DIR_TMP, MNT_TMP, APK_TMP, ZIP_TMP, ODEX_TMP, TAR_TMP, MSC_TMP, IMAGE, VENDOR, KEEPSTUFF, VENDORMODE, SUB_DIR, MY_FULL_DIR, MY_DIR

  args = parse_arguments()
  # if no args
  
  print('Args.filepath: ' + args.filepath)
  print('Args.vendor: ' + args.vendor)

  if (args.filepath != None and args.vendor != None):
    print('setting variables')
    IMAGE = args.filepath
    VENDOR = args.vendor
    KEEPSTUFF = (args.keepstuff) # keep all the decompiled/unpackaged stuff for later analysis
    VENDORMODE = (args.vendormode) # should be provided as 0 unless alternate mode
    JOB_ID = str(args.index)

    MY_DIR=MY_DIR + VENDOR
    MY_FULL_DIR = MY_FULL_DIR + VENDOR

    print('home value: ' + HOME) 
    DIR_TMP = HOME + '/atsh_tmp' + JOB_ID
    print('dir_tmp:' + DIR_TMP)
    MNT_TMP = HOME + '/atsh_tmp' + JOB_ID + '/mnt'
    APK_TMP = HOME + '/atsh_apk' + JOB_ID
    ZIP_TMP = HOME + '/atsh_zip' + JOB_ID
    ODEX_TMP = HOME + '/atsh_odex' + JOB_ID
    TAR_TMP = HOME + '/atsh_tar' + JOB_ID
    MSC_TMP = HOME + '/atsh_msc' + JOB_ID
  else:
    print('filepath and/or vendor are empty')
  temp_str = 'error'

  print()
  print('---------------------------------------------------')
  print('Welcome to Connor Short\'s Android extraction tool!')
  print('----------------------------------------------------------')
  print()

  print('**********************************************************')
  print()
  print('This tool was created in cohesion with FICS. The tool is based of a previous iteration')
  print('of android extraction where AT commands were pulled from Android image files.')
  print()
  print('It also relies heavily on code from the previous python iteration of Android Extract')
  print('developed by Sam Simon')
  print()
  print('For more information on the previous tool, please visit:')
  print('www.atcommands.org')
  print()
  print()
  print('**********************************************************')
  print()
  print()

  fo2 = open('2', 'wt')

  if (USINGDEPPATH == 1 ) and (DEPPATH == '' ):
    print('ERROR: variable DEPPATH not initialized on line 64',file=fo2)
    print('     : if not using DEPPATH and manually updated all dependency locations on lines 67-85',file=fo2)
    print('     : set USINGDEPPATH=0 to disable this check.',file=fo2)
    print('',file=fo2)
    print('For additional guidance and a full list of dependencies, please refer to the provided README.',file=fo2)
    exit(1)
  
  # print usage if not enough arguments provided
  if (args.filepath is None or args.vendor is None or args.index is None or args.vendormode is None):
    print_how_to()
    print()
    print()
    exit(0)
  elif (args.vendormode == 0):
    print('WARN : VENDoRMODE has been set to 0!')
    print('WARN : some images may require alternative steps for extraction, in which case you should supply',file=fo2)
    print('an additional argument (1). currently applies to:',file=fo2)
    print('password protected Samsung (.zip) image files from firmwarefile.com',file=fo2)
    print('Continuing after defaulting to 0!',file=fo2)
    print()
    VENDORMODE = 0

  print('ALERT: Now initiating extraction process')
  
  #os.mkdir(TOP_DIR)
  os.makedirs(TOP_DIR, exist_ok=True)
  #os.mkdir(MY_DIR)
  os.makedirs(MY_DIR, exist_ok=True)
  cp(IMAGE, MY_DIR)
  os.chdir(MY_DIR)

  VENDOR = subprocess.run(['basename', VENDOR, '-expanded'], universal_newlines=True, stdout=subprocess.PIPE).stdout.rstrip('\n')
  print('The current vendor: ' + VENDOR)


  IMAGE = subprocess.run(['basename', IMAGE], universal_newlines=True, stdout=subprocess.PIPE).stdout.rstrip('\n')

  print('ALERT: Cleaning up temporary files from prior run (if any).')
  clean_up()

  #Create logs for vendor formats that cannot be handled 
  if(VENDOR=="samsung" and not os.path.isfile(MY_PROP)):
    open(TIZ_LOG, 'w+')

  # Assume name.suffix format
  if (VENDOR == "asus"):
    DIR_PRE= subprocess.run(["echo", IMAGE, "|", "cut", "-d", "?", "-f", "1"], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
    SUB_EXT = DIR_PRE[-4:]
    SUB_DIR = DIR_PRE[:-4]
  else:
    print('Image: ' + IMAGE )
    #DIR_PRE= subprocess.run(["basename", IMAGE], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
    DIR_PRE= getBasename(IMAGE)
    SUB_EXT = DIR_PRE[-4:]
    SUB_DIR = DIR_PRE[:-4]

  print('Output will be available in: ' + SUB_DIR)
  os.makedirs(SUB_DIR, exist_ok=True)
  mv(IMAGE, SUB_DIR)
  os.chdir(SUB_DIR)

  print('Unzipping the image file...')
  
  if (VENDOR == 'aosp'):
    main_unzip_result=at_unzip(IMAGE, None)
  elif(VENDOR=='samsung'):
    os.makedirs(SUB_SUB_TMP)
    DECSUFFIX=IMAGE[-4:]
    if(DECSUFFIX == '.zip'):
      #Deal with vendormode versions later
      main_unzip_result=at_unzip(IMAGE, SUB_SUB_TMP)
    else:
      print('The archive format is not currently supported')
    os.chdir(SUB_SUB_TMP)
    fileList=getFiles()
    if(len(fileList)==1 and os.path.isdir(fileList[0])):
      cp('-r', fileList[0] + '/' + '*', '.')
      shutil.rmtree(fileList[0])
    os.chdir('..')      

  if (main_unzip_result == False):
    print ('Sorry, there is currently no support for decompressing this image!')
    exit(0)
  
  os.remove(IMAGE)

  # NOTE: assume there is only 1 dir after unzipping
  print('current directory ' + os.getcwd())
  #print('ls results ' + subprocess.Popen(['ls','|','head','-1'], stdout=subprocess.PIPE))
  SUB_SUB_DIR = subprocess.run(['ls', '|', 'head', '-1'], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip('\n').partition('\n')[0]
  #MY_TMP = MY_TMP
  if (not os.path.isfile(MY_TMP)):
    open(MY_TMP, 'w+')
  MY_TMP = os.getcwd() + '/' + MY_TMP
  if (not os.path.isfile(MY_USB)):
    open(MY_USB, 'w+')
  MY_USB = os.getcwd() + '/' + MY_USB
  if (not os.path.isfile(MY_PROP)):
    open(MY_PROP, 'w+')
  MY_PROP = os.getcwd() + '/' + MY_PROP
  MY_OUT = os.getcwd() + '/' + MY_OUT
  if (os.path.isdir(SUB_SUB_DIR)):
    os.chdir(SUB_SUB_DIR)
  else:
    print('ERROR: More than 1 sub directory found!')
    exit(0)

  if (VENDOR == 'aosp'):
    print('Beginning aosp extraction process')
    extract_aosp()
  if(VENDOR == 'samsung'):
    print('Beginning samsung extraction process')
    extract_samsung()

  print('Summarizing the findings...')
  if (KEEPSTUFF == 0):
    rmdir(SUB_SUB_DIR)
  cat(MY_TMP, _out=open(MY_OUT, 'w+'))

#########################
#   Main Call    #
#########################

if __name__ == '__main__':
  main()
