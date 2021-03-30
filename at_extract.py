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
