#!/usr/bin/python3

import os
import os.path
import sys
import subprocess
import argparse
import glob
import rarfile

from subprocess import call
from os.path import expanduser
from zipfile import ZipFile

#CONNOR: sh commands to replace subprocess
from sh import rm
from sh import umount
from sh import mkdir
from sh import cp
from sh import rmdir

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

from zipfile import ZipFile
import rarfile



#CONNOR: This function is currently mostly the same and is being replaced piece by piece
# Decompress the zip-like file
# Return 'True' if the decompression is successful
# Otherwise 'False'
# NOTE: to support more decompressing methods, please add them here:

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
