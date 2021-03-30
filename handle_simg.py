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
