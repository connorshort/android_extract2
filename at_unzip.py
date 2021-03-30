from zipfile import ZipFile
import rarfile




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

    #add tarfile
    elif (format5 == "POSIX" and format2_3 == "tar"):
        if directory is None:         
            z = TarFile(filename, 'r')
	    	z.extractall()
			z.close()
        else:
            z = TarFile(filename, 'r')
	    	z.extractall(directory)
			z.close()
        AT_RES = "good"
        return True

    #ONLY htc can be ignored for now
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
