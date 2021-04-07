#!/usr/bin/python3

import os
import os.path
import sys
import subprocess
import argparse
import glob
import rarfile
import zipfile

from subprocess import call
from os.path import expanduser
from zipfile import ZipFile

#CONNOR: sh commands to replace subprocess
from sh import rm
from sh import umount
from sh import mkdir
from sh import cp
from sh import rmdir
from sh import ls

##############################################################################################
#CONNOR: The following is copied straight from previous edition
##############################################################################################

IMAGE = ""
VENDOR = ""
KEEPSTUFF = 0 # keep all the decompiled/unpackaged stuff for later analysis
VENDORMODE = 0 # should be provided as 0 unless alternate mode

HOME = str(expanduser("~"))

EXTUSER = "someuser" # TODO: replace with valid user to use keepstuff functionality
EXTGROUP = "somegroup" # TODO: replace with valid group to use keepstuff functionality
MY_TMP = "extract.sum"
MY_OUT = "extract.db"
MY_USB = "extract.usb"
MY_PROP = "extract.prop"
#MY_TIZ="extract.tizen" # used to mark presence of tizen image(s), replaced by TIZ_LOG
TIZ_LOG = "tizen.log" # samsung
PAC_LOG = "spd_pac.log" # lenovo
SBF_LOG = "sbf.log" # moto
MZF_LOG = "mzf.log" # moto
RAW_LOG = "raw.log" # asus
KDZ_LOG = "kdz.log" # lg
MY_DIR = "extract/" + VENDOR
MY_FULL_DIR = "/data/atdb/extract/" + VENDOR
TOP_DIR = "extract"
AT_CMD = 'AT\+|AT\*'
AT_CMD = 'AT\+|AT\*|AT!|AT@|AT#|AT\$|AT%|AT\^|AT&' # expanding target AT Command symbols
DIR_TMP = ""
MNT_TMP = ""
APK_TMP = ""
ZIP_TMP = ""
ODEX_TMP = ""
TAR_TMP = ""
MSC_TMP = ""
JAR_TMP = "dex.jar"

##############################################################################################
#CONNOR: Also straight from the original
##############################################################################################

DEPPATH=""
USINGDEPPATH=0 # 1 = true, 0 = false

DEX2JAR=str(DEPPATH)+"/dex2jar/dex-tools/target/dex2jar-2.1-SNAPSHOT/d2j-dex2jar.sh"
JDCLI=str(DEPPATH)+"/jd-cmd/jd-cli/target/jd-cli.jar"
# These are the most recent versions of baksmali/smali that work with java 7 (needed for JADX-nohang)
BAKSMALI=str(DEPPATH)+"/baksmali-2.2b4.jar"
SMALI=str(DEPPATH)+"/smali-2.2b4.jar"
JADX=str(DEPPATH)+"/jadx/build/jadx/bin/jadx"
# ~~~The following tools needed to unpack LG images: avail https://github.com/ehem/kdztools~~~
UNKDZ=str(DEPPATH)+"/kdztools/unkdz"
UNDZ=str(DEPPATH)+"/kdztools/undz"
UPDATA=str(DEPPATH)+"/split_updata.pl/splitupdate"
UNSPARSE=str(DEPPATH)+"combine_unsparse.sh"
SDAT2IMG=str(DEPPATH)+"sdat2img/sdat2img.py"
SONYFLASH=str(DEPPATH)+"flashtool/FlashToolConsole"
SONYELF=str(DEPPATH)+"unpackelf/unpackelf"
IMGTOOL=str(DEPPATH)+"imgtool/imgtool.ELF64"
HTCRUUDEC=str(DEPPATH)+"htcruu-decrypt3.6.5/RUU_Decrypt_Tool" # rename libcurl.so to libcurl.so.4
SPLITQSB=str(DEPPATH)+"split_qsb.pl"
LESZB=str(DEPPATH)+"szbtool/leszb" # szb format1 for lenovo
UNYAFFS=str(DEPPATH)+"unyaffs/unyaffs" # yaffs2 format1 for sony

BOOT_OAT = ""
BOOT_OAT_64 = ""
AT_RES = ""
SUB_SUB_TMP = "extract_sub"
SUB_DIR = ""
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
  print("This program must be run with AT LEAST the first 4 of the following options, 5th option is not mandatory:")
  print("-f <FILEPATH>                              : to define package filepath")
  print("-vendor <VENDOR NAME>                      : to define the vendor")
  print("-i <INDEX>                                 : to declare index number of directory")
  print("-ks <KEEP STUFF? [0 OR 1]>                 : to declare whether to remove extracted files after Processing")
  print("--vendor-mode <VENDOR MODE [0 OR 1]>       : to configure specific vendor related settings")

  fo2 = open("2", "wt")

  print("ERROR: not enough arguments provided.",file=fo2)
  print("USAGE: ./atextract.sh <firmware image file> <vendor> <index> <keepstuff flag> <vendor mode (optional)>",file=fo2)
  print("          firmware image file = path to the top-level packaged archive (zip, rar, 7z, kdz, etc.)",file=fo2)
  print("                                (may be absolute or relative path)",file=fo2)
  print("          vendor = the vendor who produced the firmware image (e.g., Samsung, LG)",file=fo2)
  print("                   currently supported = samsung, lg, lenovo, zte, huawei, motorola, asus, aosp,",file=fo2)
  print("                                         nextbit, alcatel, blu, vivo, xiaomi, oneplus, oppo,",file=fo2)
  print("                                         lineage, htc, sony",file=fo2)
  print("          index = to extract multiple images at the same time, temporary directories will",file=fo2)
  print("                  need different indices. For best results, supply an integer value > 0.",file=fo2)
  print("          keepstuff = 0/1",file=fo2)
  print("                      if 0, will remove any extracted files after processing them",file=fo2)
  print("                      if 1, extracted files (e.g., filesystem contents, apps) will be kept",file=fo2)
  print("                            (useful for later manual inspection)",file=fo2)
  print("          vendor mode = some vendors will have several different image packagings",file=fo2)
  print("                        if so, supplying 1 as this optional argument will invoke an adjusted extraction",file=fo2)
  print("                        currently applies to:",file=fo2)
  print("                            password protected Samsung (.zip) image files from firmwarefile.com",file=fo2)
  print("                        extend as needed",file=fo2)
  print("", file=fo2)
  print("For additional guidance and a full list of dependencies, please refer to the provided README.",file=fo2)
  
  fo2.close()


#########################
#	   HELPER METHODS	#
#########################

#CONNOR: changed to use sh instead of subprocess calls
def clean_up():
	with sh.contrib.sudo:
		umount(MNT_TMP, ">", "/dev/null")
	rm('-rf', DIR_TMP, '>', '/dev/null')
	rm('-rf', APK_TMP , '>', '/dev/null')
	rm('-rf', ZIP_TMP , '>', '/dev/null')
	rm('-rf', ODEX_TMP , '>', '/dev/null')
	rm('-rf',  TAR_TMP , '>', '/dev/null')
	rm('-rf',  MSC_TMP , '>', '/dev/null')

# Decompress the zip-like file
# Return 'True' if the decompression is successful
# Otherwise 'False'
# NOTE: to support more decompressing methods, please add them here:

#CONNOR: Changed to use zipfile commands, currently replacing piece-by-piece
def at_unzip(filename, filename2, directory):
    # filename = "$1"
    # directory = "$2"
    # format = 'file -b "$filename" | cut -d" " -f1'
    
    image_vendor = VENDOR

    format3 = filename[-3:] # 3 character file extensions (i.e. .cpp)
    format4 = filename[-4:] # 4 character file extensions (i.e. .java)
    format5 = filename[-5:] # 5 character file extensions (i.e. .7-zip)
    format6 = filename[-6:] # 6 character file extensions (i.e. .6chars)
    format7 = filename[-7:] # 7 character file extensions (i.e. .7-chars)

    if (filename2 is not None):
        format2_3 = filename2[-3:] # 3 character file extensions (i.e. .cpp)
        format2_4 = filename2[-4:] # 4 character file extensions (i.e. .java)
        format2_5 = filename2[-5:] # 5 character file extensions (i.e. .7-zip)
        format2_6 = filename2[-6:] # 6 character file extensions (i.e. .6chars)
        format2_7 = filename2[-7:] # 7 character file extensions (i.e. .7-chars)


    #CONNOR: Replaced with zipfile commands
    if (format3 == "zip" ) or (format3 == "ZIP" ) or ( format3 == "Zip" ):
        if directory is None:         
        	z = ZipFile(filename, 'r')
          z.extractall()
          z.close()
        else:
          z = ZipFile(filename, 'r')
          z.extractall(directory)
          z.close()
        AT_RES = "good"
        return True

    #CONNOR: Replaced with zipfile commands
    elif (format4 == "Java"):
        # mischaracterization of zip file as Java archive data for HTC
        # or it is actually a JAR, but unzip works to extract contents
        if directory is None:         
        	z = ZipFile(filename, 'r')
          z.extractall()
          z.close()
        else:
          z = ZipFile(filename, 'r')
          z.extractall(directory)
          z.close()
        AT_RES = "good"
        return True

    elif (format5 == "POSIX" and format2_3 == "tar"):
        if directory is None:         
            subprocess.run(['tar', 'xvf', filename], shell=True)
        else:
            subprocess.run(['tar','xvf', filename, '-C', directory], shell=True)
        AT_RES = "good"
        return True

    elif (format4 == "PE32" and image_vendor == "htc" ):
        subprocess.run([HTCRUUDEC, '-sf', filename], shell=True)
        decoutput = 'ls | grep \"OUT\"'
        os.rmdir(directory)
        subprocess.run(['mv', decoutput, directory], shell=True)
        AT_RES = "good"
        return True

    elif (format3 == "RAR"):
        if directory is None: 
            subprocess.run(['unrar','x', filename], shell=True)
            if (image_vendor == "samsung"):
                subprocess.run(['tar', 'xvf', 'basename', filename, ".md5"], shell=True)
        else: 
            backfromrar = subprocess.run('pwd', shell=True)
            subprocess.run(['cp', filename, directory], shell=True)
            os.chdir(directory)
            subprocess.run(['unrar','x', filename], shell=True)
            if (image_vendor == "samsung"):
                subprocess.run(['tar', 'xvf', 'basename', filename, ".md5"], shell=True)
            os.remove(filename)
            os.chdir(backfromrar)
        AT_RES = "good"
        return True
    
    elif (format4 == "gzip"):
        # gunzip is difficult to redirect
        if directory is None:
            subprocess.run(['gunzip', filename], shell=True) 
        else:
            backfromgz = subprocess.run('pwd', shell=True)
            subprocess.run(['cp', filename, directory], shell=True)
            subprocess.run(['cd', directory], shell=True)
            subprocess.run(['gunzip', filename], shell=True)
            os.chdir(backfromgz)
        os.remove(filename)
        AT_RES = "good"
        return True
    elif (image_vendor == "motorola" and format7 == ".tar.gz"):
        subprocess.run(['gunzip', filename], shell=True)
        subprocess.run(['tar', 'xvf', 'basename', filename, ".gz"], shell=True)
        AT_RES = "good"
        return True
    elif (image_vendor == "motorola" and format7 == ".tar.gz"):
        backfromgz = subprocess.run('pwd', shell=True)
        subprocess.run(['cp', filename, directory], shell=True)
        subprocess.run(['cd', directory], shell=True)
        subprocess.run(['gunzip', filename], shell=True) 
        subprocess.run(['tar', 'xvf', 'basename', filename, ".gz"], shell=True)
        os.chdir(backfromgz)
        AT_RES = "good"
        return True
    
    elif (format5 == "7-zip"):
        if directory is None:
            subprocess.run(['7z', 'x', filename], shell=True)
        else:
            subprocess.run(['unrar', 'x', '-o', directory, filename], shell=True)
        AT_RES = "good"
        return True

    else:
        AT_RES = "bad"
        return False

#CONNOR: The handle functions have been changed to use default python file searching
def handle_text(filename):
	f=open(MY_TMP, 'a')
	with open(filename) as openfileobject:
    for line in openfileobject:
    	for word in AT_CMD:
    		if word in line:
    			#CONNOR: FIX OUTPUT TO MATCH AWK COMMAND ON LINE 321
    			f.write(line)

def handle_binary(filename):
	#CONNOR: WILL START OFF EXACT SAME AS TEXT
	f=open(MY_TMP, 'a')
	with open(filename) as openfileobject:
    for line in openfileobject:
    	for word in AT_CMD:
    		if word in line:
    			#CONNOR: FIX OUTPUT TO MATCH AWK COMMAND ON LINE 321
    			f.write(line)

#CONNOR: NEXT TWO ARE JUST USING BINARY IN PREVIOUS VERSION, MIGHT CHANGE LATER
def handle_elf(filename):
	handle_binary(filename)
	# Can run bingrep, elfparser but they suck...

def handle_x86(filename):
	# Currently no special handling for x86 boot sectors
	handle_binary(filename)

#CONNOR: Need to work on handle_bootimg
def handle_bootimg(filename):
  name = str(subprocess.run(["basename ", filename], shell=True))
  if (name[4:] == "boot" or
        name[8:] == "recovery" or
        name[4:] == "hosd" or
        name[9:] == "droidboot" or
        name[8:] == "fastboot" or
        name[10:] == "okrecovery" or
        name[4:] == "BOOT" or
        name[8:] == "RECOVERY" or
        name[-4:] == ".bin" ):
    subprocess.run([IMGTOOL, filename, "extract"], shell=True)
    os.chdir("extracted")
    format_ = subprocess.run(["file","-b","ramdisk", "|", "cut", "-d", " ", "-f1"], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
    if (format_ == "LZ4"):
      subprocess.run(["unlz4", "ramdisk", "ramdisk.out"], shell=True)
      subprocess.run(["cat", "ramdisk.out", "|", "cpio", "-i"], shell=True)
      os.remove('ramdisk.out')
    elif (format_ == "gzip"):
      subprocess.run(["gunzip", "-c", "ramdisk", "|", "cpio", "-i"], shell=True)
    os.remove("ramdisk")
    os.chdir("..")
    find_out = subprocess.run(["find","extracted", "-print0"],universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.split_lines()
    for line in find_out:
      if (os.path.isfile(line)):
        format_ = subprocess.run(["file","-b","ramdisk", "|", "cut", "-d", " ", "-f1"], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
        if (format_ == "gzip"):
          subprocess.run(["mv", line, line, ".gz"], shell=True)
          subprocess.run(["gunzip", "-f", line, ".gz"], shell=True)
          at_extract(line)
        else:
          at_extract(line)
        print(line + "processed: " + AT_RES)
    # ------------------------------------------
    # Need corresponding piped while loop FIXME
    # ------------------------------------------
    if ( KEEPSTUFF == 1 ):
      subprocess.run(["sudo", "cp", "-r", "extracted", MY_FULL_DIR + "/" + SUB_DIR + "/" + name], shell=True)
      subprocess.run(["sudo", "chown", "-R", EXTUSER + ":" + EXTGROUP, MY_FULL_DIR + "/" + SUB_DIR + "/" + name], shell=True)
    os.rmdir("extracted")
  else:
    handle_binary(filename)


#CONNOR Replaced subprocess with zip and changed mkdir, rmdir, and CP to sh
def handle_zip(filename, filetype):
  rtn = ""
  print("Unzipping " + filename + " ...")
  mkdir(ZIP_TMP)
  cp(filename,ZIP_TMP)
  if (filetype == "zip"):
    z = ZipFile(ZIP_TMP, 'r')
    z.extractall(str(ZIP_TMP)+"/"+filename)
    z.close()
  elif (filetype == "gzip"):
    if (filename[-7:] == ".img.gz"):
      print("Handling a .img.gz file... ")
      gzip = subprocess.run(["basename", filename, ".gz"], shell=True)
      subprocess.run("gunzip" + " " + "-c" + " " + str(ZIP_TMP)+"/"+filename,shell=True,stdout=open(str(ZIP_TMP)+"/"+str(gzip),'wb'))
    else:
      print("Handling a .tar.gz file... ")
      subprocess.run(["tar","xvf",str(ZIP_TMP)+"/"+filename,"-C",str(ZIP_TMP)],shell=True)
    os.rmdir(ZIP_TMP+"/"+filename)
    # ------------------------------------------
    # Need corresponding piped while loop FIXME
    # ------------------------------------------
    if (KEEPSTUFF == 1):
      subprocess.run(["sudo","cp","-r",str(ZIP_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+filename],shell=True)
      subprocess.run(["sudo","chown","-R",str(EXTUSER)+":"+str(EXTGROUP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+filename],shell=True)
    os.rmdir(ZIP_TMP+"/"+filename)


#CONNOR: THE FOLLOWING IS UNTOUCHED UNTIL NEXT COMMENT
def handle_qsbszb(qsbszb, qsmode):
  getback = str(os.getcwd())
  os.mkdir(MSC_TMP)
  subprocess.run(["cp",str(qsbszb),str(MSC_TMP)],shell=True)
  qsbszb = os.popen("basename \""+str(qsbszb)+"\"").read().rstrip("\n")
  os.chdir(MSC_TMP)
  if (qsmode == 0):
    print("Splitting qsb " + str(qsbszb) + " ...")
    subprocess.run([str(SPLITQSB), str(qsbszb)], shell=True)
  else:
    print("Splitting szb " + str(qsbszb) + " ...")
    subprocess.run([str(LESZB), "-x", str(qsbszb)], shell=True)
  os.remove(qsbszb)
  # ------------------------------------------
  # Need corresponding piped while loop FIXME
  # ------------------------------------------
  os.chdir(getback)
  os.rmdir(MSC_TMP)

def handle_apk(apk):
  name = os.popen("basename \""+str(apk)+"\"").read().rstrip("\n")
  print("Decompiling" + str(name) + " ...")
  os.mkdir(APK_TMP)
  subprocess.run(["cp",str(apk),str(APK_TMP)+"/"+str(name)],shell=True) # Dex2Jar
  subprocess.run([str(DEX2JAR),str(APK_TMP)+"/"+str(name),"-o",str(APK_TMP)+"/"+str(JAR_TMP)],shell=True)
  subprocess.run("java" + " " + "-jar" + " " + str(JDCLI) + " " + "-oc" + " " + str(APK_TMP)+"/"+str(JAR_TMP),shell=True,stdout=open(str(APK_TMP)+"/jdcli.out",'wb'))
  subprocess.run(["grep","-E",str(AT_CMD),str(APK_TMP)+"/jdcli.out"],shell=True)
  subprocess.run("awk" + " " + "-v" + " " + "apkname="+str(name) + " " + "BEGIN {OFS=\"\\t\"} {print apkname,$0}",shell=True,stdout=open(str(MY_TMP),'ab'))
  if (KEEPSTUFF == 1 ):
    subprocess.run(["cp","-r",str(APK_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(name)],shell=True)
  os.rmdir(APK_TMP)
  
def handle_jar(filename):
  subprocess.run(["java","-jar",str(JDCLI),"-oc",str(filename)],shell=True)
  subprocess.run(["grep","-E",str(AT_CMD)],shell=True)
  subprocess.run("awk" + " " + "-v" + " " + "fname="+str(filename) + " " + "BEGIN {OFS=\"\\t\"} {print fname,$0}",shell=True,stdout=open(str(MY_TMP),'ab'))

def handle_java(filename):
  format4 = str(filename)[-4:]
  if (format4 == ".apk" or format4 == ".APK" or format4 == ".Apk"):
    handle_apk(filename)
  else:
    handle_jar(filename)

def handle_odex(odex):
  name = os.popen("basename \""+str(odex)+"\"").read().rstrip("\n")
  arch = ""
  boot = ""
  print("Processing odex...")
  os.mkdir(ODEX_TMP)
  subprocess.run(["cp",str(odex),str(ODEX_TMP)+"/"+str(name)],shell=True) # Dex2Jar

  arch = str(os.popen("file -b "+str(ODEX_TMP)+"/\""+str(name)+"\" | cut -d\" \" -f2 | cut -d\"-\" -f1").read().rstrip("\n"))
  if (arch == "64"):
    boot = BOOT_OAT_64
  else:
    boot = BOOT_OAT
  print("DEBUG: use boot.oat - " + boot)

  if (boot is not ""):
    print("Processing smali...")
    # Try to recover some strings from smali
    subprocess.run(["java","-jar",str(BAKSMALI),"deodex","-b",str(boot),str(ODEX_TMP)+"/"+str(name),"-o",str(ODEX_TMP)+"/out"],shell=True)
    # grep -r $AT_CMD $ODEX_TMP/out >> ../$MY_TMP
    ret = subprocess.run(["grep","-r","-E",str(AT_CMD),str(ODEX_TMP)+"/out"],shell=True)
    subprocess.run("awk" + " " + "-v" + " " + "fname="+str(ret) + " " + "BEGIN {OFS=\"\\t\"} {print fname,$0}",shell=True,stdout=open(str(MY_TMP),'ab'))
    # Try to decompile from smali->dex->jar->src
    # May not work!
    print("decompiling smali/dex...")
    subprocess.run(["java","-jar",str(SMALI),"ass",str(ODEX_TMP)+"/out","-o",str(ODEX_TMP)+"/out.dex"],shell=True)
    print("invoking jadx on smali/dex output...")
    subprocess.run([str(JADX),"-d",str(ODEX_TMP)+"/out2",str(ODEX_TMP)+"/out.dex"],shell=True)
    if (os.path.isdir(str(ODEX_TMP)+"/out2")):
      subprocess.run(["grep","-r","-E",str(AT_CMD),str(ODEX_TMP)+"/out2"],shell=True)
      subprocess.run("awk" + " " + "-v" + " " + "fname="+str(name) + " " + "BEGIN {OFS=\"\\t\"} {print fname,$0}",shell=True,stdout=open(str(MY_TMP),'ab'))
    if (KEEPSTUFF == 1):
      subprocess.run(["cp","-r",str(ODEX_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(name)],shell=True)
    os.rmdir(ODEX_TMP)
    
def check_for_suffix(filename):
  suffix = filename[-4:]
  suffix2 = filename[-5:]
  
  if (suffix == ".apk" or suffix == ".APK" or suffix == ".Apk"
        or suffix == ".jar" or suffix == ".Jar" or suffix == ".JAR"):
    AT_RES = "java"
  elif (suffix2 == ".odex" or suffix2 == ".ODEX" or suffix2 == ".Odex"):
    AT_RES == "odex"
  else:
    AT_RES = "TBD"

# Process special files
# All files which require special care should happen here
def handle_special(filename):
  justname = str(os.popen("basename \""+str(filename)+"\"").read().rstrip("\n"))

  usbFile = open(MY_USB)
  propFile = open(MY_PROP)
  tizFile = open(TIZ_LOG)

  if (justname == str(glob.glob("init*usb.rc"))):
    # Save init file for USB config analysis
    # also need to capture e.g., init.hosd.usb.rc (notable: aosp sailfish)
    # there's also init.tuna.usb.rc in aosp yakju, etc.
    # init.steelhead.usb.rc in tungsten
    print(filename, file = usbFile)
    print("---------",file = usbFile)
    subprocess.run("cat" + " " + str(filename),shell=True,stdout=usbFile)
    print("=========",file=usbFile)

  elif (justname == "build.prop" ):
    # Save the contents of build.prop to get information about OS version, etc.
    print(filename,file=propFile)
    print("---------",file=propFile)
    # in rare cases, permission denied when trying to access build.prop
    subprocess.run("sudo" + " " + "cat" + " " + str(filename),shell=True,stdout=propFile)
    print("=========",file=propFile)

  elif ( VENDOR == "samsung" ) and ( justname == "dzImage" ):
    # Tizen OS image detected. Should abort
    # touch ../$MY_TIZ
    AT_RES = "tizen"
    print(str(filename)+" processed: "+str(AT_RES))
    print(IMAGE,file=tizFile)
    # for easier ID later, needs to be existing file
    exit(55)
    # exit immediately; no need to go further


#CONNOR: at_extract will remain mostly unchanged, only 2 os calls
def at_extract(filename):
  filetype = str(os.popen("file -b \""+str(filename)+"\" | cut -d\" \" -f1").read().rstrip("\n"))
  justname = (os.popen("basename \""+str(filename)+"\"").read().rstrip("\n"))
  
  # Check for special files
  handle_special(filename)
  
  if (filetype == "apollo" or filetype == "FoxPro" or filetype == "Mach-O" or
        filetype == "DOS/MBR" or filetype == "PE32" or filetype == "PE32+" or 
        filetype == "dBase" or filetype == "MS" or filetype == "PDP-11" or 
        filetype == "zlib" or filetype == "ISO-8859" or filetype == "Composite" or 
        filetype == "very" or filetype == "Hitachi" or filetype == "SQLite" ):
    handle_binary(filename)
    AT_RES = "good"
  elif (filetype == "ELF"):
    handle_elf(filename)
    check_for_suffix(filename)
    if (AT_RES == "odex"):
      handle_odex(filename)
    AT_RES = "good"
  elif (filetype == "x86"):
    handle_x86(filename)
    AT_RES = "good"
  elif (filetype == "DOS"):
    handle_text(filename)
    AT_RES = "good"
  elif (filetype == "Java"):
    handle_java(filename)
    AT_RES = "good"
  elif (filetype == "POSIX" or filetype == "Bourne-Again"):
    handle_text(filename)
    AT_RES = "good"
  elif (filetype == "ASCII" or filetype == "XML" or filetype == "Tex" or filetype == "html"
          or filetype == "UTF-8" or filetype == "C" or filetype == "Pascal" or filetype == "python"):
    handle_text(filename)
    AT_RES = "good"
  elif (filetype == "Windows"):
    handle_text(filename)
    AT_RES = "good"
  elif (filetype == "Zip"):
    check_for_suffix(filename)
    if ("AT_RES" == "java"):
      handle_java(filename)
      AT_RES = "good"
    else:
      handle_zip(filename, "zip")
      AT_RES = "good"
  elif (filetype == "gzip" or filetype == "XZ"):
    handle_zip(filename, "gzip")
    AT_RES = "good"
  elif (format == "Android"):
    print("Processing .img file as binary!")
    handle_bootimg(filename)
    AT_RES = "good"
  elif (format == "broken" or format == "symbolic" or format == "SE" or 
          format == "empty" or format == "directory" or format == "Ogg" or
          format == "PNG" or format == "JPEG" or format == "PEM" or 
          format == "TrueType" or format == "LLVM" or format == "Device"):
    # format == dBase was being skipped before; now handled as binary (jochoi)
    # format == Device Tree Blob after extracting boot/recovery img; ignoring
    # Skip broken/symbolic/sepolicy/empty/dir/...
    AT_RES = "skip"
  else:
    AT_RES = "bad"


#CONNOR: FOLLOWING IS ALSO LARGELY UNTOUCHED
def handle_ext4(imgPath):
  ext = str(os.popen("basename \""+str(imgPath)+"\"").read().rstrip("\n"))
  arch = ""
  os.mkdir(DIR_TMP)
  os.mkdir(MNT_TMP)
  # Make a copy
  subprocess.run(["cp",imgPath,DIR_TMP+"/"+(ext)],shell=True)
  # NOTE: needs sudo or root permission
  subprocess.run(["sudo","mount","-t","ext4",(DIR_TMP)+"/"+str(ext),str(MNT_TMP)],shell=True)
  subprocess.run(["sudo","chown","-R",(EXTUSER)+":"+(EXTGROUP),str(MNT_TMP)],shell=True)
  # Find the boot.oat for RE odex
  BOOT_OAT = ""
  BOOT_OAT_64 = ""

  thisFile = open("newfile.txt")

  while open(thisFile):
    # Debug
    #echo "DEBUG: boot.oat - $file"
    arch = str(os.popen("file -b \""+str(thisFile)+"\" | cut -d\" \" -f2 | cut -d\"-\" -f1").read().rstrip("\n"))
    if (arch == "64"):
      BOOT_OAT_64=thisFile
    else:
      BOOT_OAT=thisFile

  subprocess.run("arch" + " " + "find" + " " + str(MNT_TMP) + " " + "-name" + " " + "boot.oat" + " " + "-print",shell=True,stdin=open("sudo", 'rb'))
  print("found boot.oat: "+str(BOOT_OAT)+", boot_oat(64): "+str(BOOT_OAT_64))
  # Traverse the filesystem - root permission
  find_out = subprocess.run(["find", MNT_TMP, "-print0"],universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.split_lines()
  for line in find_out:
    if (os.path.isfile(line)):
      at_extract(line)
      print(line + " processed: " + AT_RES)
  # what we're interested is probably the contents of the FS once mounted, rather than DIR_TMP
  if ( "$KEEPSTUFF" == "1" ):
    #   cp -r $DIR_TMP ../$ext
    subprocess.run(["sudo","cp","-r",str(MNT_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
    subprocess.run(["sudo","chown","-R",str(EXTUSER)+":"+str(EXTGROUP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
  
  subprocess.run(["sudo","umount",str(MNT_TMP)],shell=True)
  os.rmdir(DIR_TMP)
  AT_RES = ("good")

def handle_chunk(imgFile, chunkMode):
  # need the directory name, not the specific file name
  ext= "system.img"
  raw="system.img.raw"
  container = str(os.popen("dirname \""+str(imgFile)+"\"").read().rstrip("\n"))
  arch = ""
  getback = str(os.popen("pwd").read().rstrip("\n"))
  chunkdir = "system_raw"

  # needs to be performed from within the directory
  os.chdir(container) # simg2img must be performed from within the directory
  os.mkdir(chunkdir)
  subprocess.run(["cp",glob.glob("system.img_*"),str(chunkdir)],shell=True)
  os.chdir(chunkdir)
  subprocess.run(["simg2img",(glob.glob("*chunk*")),str(raw)],shell=True)
  subprocess.run(["file",str(raw)],shell=True)
  print("Stage 1 complete")
  if (chunkMode == 0):
    subprocess.run(["offset","=",os.popen("LANG=C grep -aobP -m1 \"\\x53\\xEF\" "+str(raw)+" | head -1 | gawk \"{print $1 - 1080}\"").read().rstrip("\n")],shell=True)
  elif (chunkMode == 1):
    subprocess.run(["mv",str(raw),str(ext)],shell=True) # no further Processing needed
  print("Stage 2 complete")
  subprocess.run(["mv", ext, ".."],shell=True)
  os.chdir("..")
  os.rmdir(chunkdir)
  os.chdir(str(getback)) # return to directory of the script
  
  handle_ext4(container + "/" + ext)

def handle_chunk_lax(imgFile, chunkMode):
  container=str(os.popen("dirname \""+str(imgFile)+"\"").read().rstrip("\n"))
  getback=str(os.popen("pwd").read().rstrip("\n"))
  ext = ""
  chunkdir = ""

  os.chdir(container)

  if (chunkMode == 0):
    chunkdir = "oem_raw"
    os.mkdir(chunkdir)
    subprocess.run(["cp",str(glob.glob("oem.img_*")),str(chunkdir)],shell=True)
    ext = "oem.img"
  elif(chunkMode == 1):
    chunkdir = "userdata_raw"
    os.mkdir(chunkdir)
    subprocess.run(["cp",str(glob.glob("userdata.img_*")),str(chunkdir)],shell=True)
    ext = "userdata.img"
  elif (chunkMode == 2):
    chunkdir = "systemb_raw"
    os.mkdir(chunkdir)
    subprocess.run(["cp",str(glob.glob("systemb.img_*")),str(chunkdir)],shell=True)
    ext = "systemb.img"

  os.chdir(str(chunkdir))
  subprocess.run(["simg2img",(glob.glob("*chunk*")),str(ext)],shell=True)
  subprocess.run(["mv",str(ext),".."],shell=True)
  os.chdir("..")
  os.rmdir(chunkdir)
  os.chdir(str(getback))

  handle_ext4(container + "/" + ext)

def handle_sdat(img, path):
  container=str(os.popen("dirname \""+str(img)+"\"").read().rstrip("\n"))
  SDAT2IMG = "$container" + "/" + path + ".transfer.list" + img + container + "/" + ".img"
  handle_ext4(container + "/" + path + ".img")

def handle_sin(img):
  fullimg= str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(SUB_SUB_DIR)+"/"+os.popen("ls \""+str(img)+"\" | cut -d \"/\" -f2-").read().rstrip("\n")
  container=str(os.popen("dirname \""+str(img)+"\"").read().rstrip("\n"))
  base=str(os.popen("basename \""+str(img)+"\" .sin").read().rstrip("\n"))
  subprocess.run([str(SONYFLASH),"--action=extract","--file="+str(fullimg)],shell=True) # will write to directory containing the img
  getback=str(os.popen("pwd").read().rstrip("\n"))
  
  # the result is observed to be ext4, elf, or unknown formats~
  if (base[-5:] == ".ext4"):
    handle_ext4(container + "/" + base + ".ext4")
  elif (base[-4:] == ".elf"):
    # need to specially manage kernel.elf
    if (base == "kernel"):
      print("Processing separate ramdisk img")
      print("-----------------------------")
      os.chdir(str(container))
      os.mkdir("elfseperate")
      subprocess.run(["mv","kernel.elf","elfseparate"],shell=True)
      os.chdir("elfseparate")
      subprocess.run([str(SONYELF),"-i","kernel.elf","-k","-r"],shell=True)
      os.mkdir("ramdiskseparate")
      subprocess.run(["mv","kernel.elf-ramdisk.cpio.gz","ramdiskseparate"],shell=True)
      os.chdir("ramdiskseparate")
      pipe1, pipe2 = os.pipe()
      if os.fork():
          os.close(pipe1)
          os.dup2(pipe1, 0)
          subprocess.run(["cpio","-i"],shell=True)
      else:
          os.close(pipe1)
          os.dup2(pipe1, 1)
          subprocess.run(["gunzip","-c","kernel.elf-ramdisk.cpio.gz"],shell=True)
          sys.exit(0)
      os.remove("kernel.elf-ramdisk.cpio.gz")
      os.chdir("..")
      find_out = subprocess.run(["find","ramdiskseparate", "-print0"],universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.split_lines()
      for line in find_out:
        if (os.path.isfile(line)):
          at_extract(line)
          print(line + "processed: " + AT_RES)
      os.rmdir("ramdiskseparate")
      os.chdir(getback)
      print("-----------------------------")
    else:
      at_extract((container + "/" + base + ".elf"))
  elif(base[-4:] == ".yaffs2"):
    print("Processing yaffs2 img")
    print("-----------------------------")
    os.chdir(str(container))
    os.mkdir("yaffsseperate")
    subprocess.run(["mv",str(base)+".yaffs2","yaffsseparate"],shell=True)
    os.chdir("yaffsseparate")
    UNYAFFS = base + ".yaffs2"
    os.remove(base + ".yaffs2")
    find_out = subprocess.run(["find",".", "-print0"],universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.split_lines()
    for line in find_out:
      if (os.path.isfile(line)):
        at_extract(line)
        print(line + "processed: " + AT_RES)
    os.chdir(getback)
    print("--------------------------")
  else:
    at_extract((container + "/" + base + ".unknown"))
  
  #currently not working FIXME
def handle_vfat(img):
  ext = str(os.popen("basename \""+str(img)+"\"").read().rstrip("\n"))
  arch = ""
  os.mkdir(DIR_TMP)
  os.mkdir(MNT_TMP)
  # Make a copy
  subprocess.run(["cp", str(img), str(DIR_TMP)+"/"+str(ext)],shell=True)
  # NOTE: needs sudo or root permission
  subprocess.run(["sudo", "mount", "-t", "vfat", str(DIR_TMP)+"/"+str(ext), str(MNT_TMP)],shell=True)
  subprocess.run(["sudo", "chown", "-R", str(EXTUSER) + ":" + str(EXTGROUP), str(MNT_TMP)],shell=True)
  # Find the boot.oat for RE odex
  BOOT_OAT=""
  BOOT_OAT_64= ""

  thisFile = open()

  while open(thisFile):
    # Debug
    #echo "DEBUG: boot.oat - $file"
    arch = str(os.popen("file -b \""+str(thisFile)+"\" | cut -d\" \" -f2 | cut -d\"-\" -f1").read().rstrip("\n"))
    if (arch == "64"):
      BOOT_OAT_64=thisFile
    else:
      BOOT_OAT=thisFile
    
    #Need while loop for at_extract FIXME
    if (KEEPSTUFF == 1):
      subprocess.run(["sudo","cp","-r",str(MNT_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
      subprocess.run(["sudo","chown","-R",str(EXTUSER)+":"+str(EXTGROUP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
    
    subprocess.run(["sudo","umount",str(MNT_TMP)],shell=True)
    os.rmdir(DIR_TMP)
    AT_RES = "good"

def handle_simg(img):
  nam = str(os.popen("basename -s .img \""+str(img)+"\"").read().rstrip("\n"))
  ext = str(nam)+".ext4"
  arch = ""
  os.mkdir(DIR_TMP)
  os.mkdir(MNT_TMP)
  subprocess.run(["simg2img",str(img),str(DIR_TMP)+"/"+str(ext)],shell=True)
  # NOTE: needs sudo or root permission
  subprocess.run(["sudo","mount","-t","ext4",str(DIR_TMP)+"/"+str(ext),str(MNT_TMP)],shell=True)
  subprocess.run(["sudo","chown","-R",str(EXTUSER)+":"+str(EXTGROUP),str(MNT_TMP)],shell=True)
  # Find the boot.oat for RE odex
  BOOT_OAT= ""
  BOOT_OAT_64= ""

  ######################################
  # Need corresponding while loop FIXME
  ######################################
  
  # Traverse the filesystem - root permission
  subprocess.run(["sudo","find",str(MNT_TMP),"-print0"],shell=True)

  find_out = subprocess.run(["find", MNT_TMP, "-print0"],universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.split_lines()
  for line in find_out:
    if (os.path.isfile(line)):
      at_extract(line)
      print(line + "processed: " + AT_RES)
  
  if (KEEPSTUFF == 1):
    subprocess.run(["sudo","cp","-r",str(MNT_TMP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
    subprocess.run(["sudo","chown","-R",str(EXTUSER)+":"+str(EXTGROUP),str(MY_FULL_DIR)+"/"+str(SUB_DIR)+"/"+str(ext)],shell=True)
  
  subprocess.run(["sudo","umount",str(MNT_TMP)],shell=True)
  os.rmdir(DIR_TMP)
  AT_RES = "good"

def handle_unsparse(filename, prefix, xmlFile, imageVendor):
  # handle_unsparse(filename, "system", "rawprogram0.xml", VENDOR)
  container=str(os.popen("dirname \""+str(filename)+"\"").read().rstrip("\n"))
  
  UNSPARSE = container + prefix + xmlFile + imageVendor
  handle_ext4(container + "/" + prefix + ".img")

#CONNOR: Splitting process_file by vendor, only AOSP at the present moment
def process_file_aosp(filename):
  justname = str(os.popen("basename \""+str(filename)+"\"").read().rstrip("\n"))
  # local format=`file -b $filename | cut -d" " -f1`
  handled = False
  # echo "Processing file: $filename" >> ../$MY_TMP # printing out the file being processed
  # echo "IN process_file | handling file: $filename"
  

  if (justname == "system.img" or justname == "system_other.img" or justname == "vendor.img"):
    #  Handle sparse ext4 fs image
    print("Processing sparse ext4 img...")
    print("-----------------------------")
    handle_simg(filename)
    print("-----------------------------")
    handled = True
  else:
    print("Processing vfat img...")
    print("-----------------------------")
    handle_vfat(filename)
    print("-----------------------------")

  #---------------------------------------------------------------------------------
  if (handled is False):
    at_extract(filename)
  #----------------------------------------------------------------------------------
def extract_aosp():
  print("handling AOSP images...")
    
    # Check for another zip file inside and unzip it
    print("checking for more zips inside...")
    out = subprocess.run(["ls"], universal_newlines=True, stdout=subprocess.PIPE, shell=True)
    files = out.stdout.splitlines()
    for f in files:
      at_unzip(f, None, None)
      # Debug
      #print("$f at_unzip: $AT_RES"
      if (AT_RES == "good"):
        print("Unzipped sub image: " + f)
        # Remove the zip file
        os.remove(f)
    # Assume all the files will be flat in the same dir
    # without subdirs
    print("Extracting AT commands...")
    print("-------------------------")
    for f in files:
      process_file_aosp(f)
      print(f + " processed: " + AT_RES)
    print("-------------------------")
    
  
      
    print("Extracting AT commands...")
    print("-------------------------")
    for f in files:
      process_file_aosp(f)
      print(f + " processed: " + AT_RES)
    print("-------------------------")

#####################################################################################################################
######################################               ################################################################
######################################     MAIN      ################################################################
######################################               ################################################################
#####################################################################################################################

#CONNOR: Everything other than AOSP is currently removed from main along with all UI code
def main():

  args = parse_arguments()

  # if no args
  
  if (args.filepath is not None and args.vendor is not None):
    IMAGE = args.filepath
    VENDOR = args.vendor
    KEEPSTUFF = (args.keepstuff) # keep all the decompiled/unpackaged stuff for later analysis
    VENDORMODE = (args.vendormode) # should be provided as 0 unless alternate mode

    DIR_TMP = HOME + "/atsh_tmp" + str(args.index)
    MNT_TMP = HOME + "/atsh_tmp" + str(args.index) + "/mnt"
    APK_TMP = HOME + "/atsh_apk" + str(args.index)
    ZIP_TMP = HOME + "/atsh_zip" + str(args.index)
    ODEX_TMP = HOME + "/atsh_odex" + str(args.index)
    TAR_TMP = HOME + "/atsh_tar" + str(args.index)
    MSC_TMP = HOME + "/atsh_msc" + str(args.index)

  temp_str = "error"

  #####################################################################################################################
  
  print()
  print("---------------------------------------------------")
  print("Welcome to Sam Simon's Android extraction tool!")
  print("----------------------------------------------------------")
  print()
  
  print("**********************************************************")
  print()
  print("This tool was created in cohesion with FICS. The tool is based of a previous iteration")
  print("   of andriod extraction where AT commands were pulled from Andriod image files.")
  print()
  print("For more information on the previous tool, please visit:")
  print("            www.atcommands.org")
  print()
  print("**********************************************************")
  print()
  print()
  
  #####################################################################################################################

 
  
  #####################################################################################################################
  
  # if dependencies have not been updated (deppath = "")
  
  fo2 = open("2", "wt")

  if (USINGDEPPATH == 1 ) and (DEPPATH == "" ):
    print("ERROR: variable DEPPATH not initialized on line 64",file=fo2)
    print("     : if not using DEPPATH and manually updated all dependency locations on lines 67-85",file=fo2)
    print("     : set USINGDEPPATH=0 to disable this check.",file=fo2)
    print("",file=fo2)
    print("For additional guidance and a full list of dependencies, please refer to the provided README.",file=fo2)
    exit(1)
  
  # print usage if not enough arguments provided
  if (args.filepath is None or args.vendor is None or args.index is None or args.vendormode is None):
    print_how_to()
    print()
    print()
    exit(0)
  elif (args.vendormode == 0):
    print("WARN : VENDERMODE has been set to 0!")
    print("WARN : some images may require alternative steps for extraction, in which case you should supply",file=fo2)
    print("       an additional argument (1). currently applies to:",file=fo2)
    print("                        password protected Samsung (.zip) image files from firmwarefile.com",file=fo2)
    print("       Continuing after defaulting to 0!",file=fo2)
    print()
    VENDORMODE = 0
  
  #####################################################################################################################
  
  print("ALERT: Now initiating extraction process")
  
  os.mkdir(TOP_DIR)
  os.mkdir(MY_DIR)
  cp(IMAGE, MY_DIR)
  os.chdir(MY_DIR)

  VENDOR = subprocess.run(["basename", VENDOR, "-expanded"], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
  print("The current vendor: " + VENDOR)


  IMAGE = subprocess.run(["basename", VENDOR], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")

  #####################################################################################################################
  
  print("ALERT: Cleaning up temporary files from prior run (if any).")
  clean_up()

  print("Output will be available in: " + SUB_DIR)
  os.mkdir(SUB_DIR)
  mv(IMAGE, SUB_DIR)
  os.chdir(SUB_DIR)

  #####################################################################################################################
  # try to unzip
  #####################################################################################################################
  #####################################################################################################################
  
  print("Unzipping the image file...")
  
  #-------------------------------------------------------------------------------
  # IF THE VENDOR IS AOSP
  #-------------------------------------------------------------------------------
  if (VENDOR == "aosp"):
    at_unzip(IMAGE, None, None)
  
  
  #-------------------------------------------------------------------------------
  # IF THE VENDOR IS UNKOWN
  #-------------------------------------------------------------------------------
  else:
    VENDOR = "aosp"
    at_unzip(IMAGE, None, None)
  
  #####################################################################################################################
  #####################################################################################################################
  
  # Remove the raw image since we have decompressed it already
  if (AT_RES == "bad"):
    print ("Sorry, there is currently no support for decompressing this image!")
    exit(0)
  
  os.remove(IMAGE)

  # NOTE: assume there is only 1 dir after unziping
  SUB_SUB_DIR = subprocess.run(["ls"], universal_newlines=True, stdout=subprocess.PIPE, shell=True).stdout.rstrip("\n")
  #MY_TMP = MY_TMP
  if (not os.path.isfile(MY_TMP)):
    open(MY_TMP, "w+")
    MY_TMP = os.getcwd() + "/" + MY_TMP
  if (not os.path.isfile(MY_USB)):
    open(MY_USB, "w+")
    MY_USB = os.getcwd() + "/" + MY_USB
  if (not os.path.isfile(MY_PROP)):
    open(MY_PROP, "w+")
    MY_PROP = os.getcwd() + "/" + MY_PROP
  MY_OUT = os.getcwd() + "/" + MY_OUT
  if (not os.path.isdir(SUB_SUB_DIR)):
    os.chdir(SUB_SUB_DIR)
  else:
    print("ERROR: More than 1 sub directory found!")
    exit(0)

  #####################################################################################################################
  #####################################################################################################################
  
  #################################
  # Final Processing and Handling #
  #################################

  #-------------------------------------------------------------------------------
  # IF THE VENDOR IS AOSP
  #-------------------------------------------------------------------------------
  if (VENDOR == "aosp"):
    extract_aosp()

  #####################################################################################################################
  #####################################################################################################################
  
  #################################
  #        Findings summary       #
  #################################

  print("Summarizing the findings...")
  if (KEEPSTUFF == 0):
    rmdir(SUB_SUB_DIR)
  cat(MY_TMP, _out=open(MY_OUT, "w+"))
#####################################################################################################################
##############################################################################################

#########################
#   Main Call    #
#########################

if __name__ == "__main__":
  main()

##############################################################################################