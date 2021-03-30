def process_file_aosp(filename):
  justname = str(os.popen("basename \""+str(filename)+"\"").read().rstrip("\n"))
  #	local format=`file -b $filename | cut -d" " -f1`
  handled = False
  #	echo "Processing file: $filename" >> ../$MY_TMP # printing out the file being processed
  #	echo "IN process_file | handling file: $filename"
  

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
