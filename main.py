#####################################################################################################################
######################################               ################################################################
######################################     MAIN      ################################################################
######################################               ################################################################
#####################################################################################################################


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

  use_UI = False
  temp_str = "error"

  #####################################################################################################################
  
  print()
  print("---------------------------------------------------")
  print("Welcome to Sam Simon's Android extraction tool!")
  print("----------------------------------------------------------")
  print()
  print("Please enter (Y/N) for whether or not you would like to use the interactive")
  print("UI to run this program or simply have already (or want to) use the command argument input")
  print()
  
  while (temp_str == "error"):
    print("   (\'Y\' to use UI guide or \'N\' to not use UI guide): ")
    temp_str = input()
    if (temp_str == "Y"):
      use_UI = True
      print("Sorry the current UI mode is not working, please restart program with command line input!")
      print("Type \'exit\' to leave cleanly or enter any key if want to continue anyway: ")
      temp_str = input()
      if (temp_str == "exit"):
        exit(0)
    elif (temp_str == "N"):
      use_UI = False
    else:
      temp_str = "error"
  
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
      process_file(f)
      print(f + " processed: " + AT_RES)
    print("-------------------------")
    
  
      
    print("Extracting AT commands...")
    print("-------------------------")
    for f in files:
      process_file(f)
      print(f + " processed: " + AT_RES)
    print("-------------------------")

  #####################################################################################################################
  #####################################################################################################################
  
  #################################
  #        Findings summary       #
  #################################

  print("Summarizing the findings...")
  if (KEEPSTUFF == 0):
    os.rmdir(SUB_SUB_DIR)
  
  subprocess.run(["cat", MY_TMP], stdout=open(MY_OUT, "w+"))

#####################################################################################################################
##############################################################################################

#########################
#   Main Call    #
#########################

if __name__ == "__main__":
  main()

##############################################################################################