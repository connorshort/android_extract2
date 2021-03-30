import sh
from sh import rm

def clean_up():
	sh.contrib.sudo.umount(MNT_TMP, '>', '/dev/null')
	rm('rf', DIR_TMP, '>' '/dev/null')
	rm('rf', APK_TMP, '>' '/dev/null')
	rm('rf', ZIP_TMP, '>' '/dev/null')
	rm('rf', ODEX_TMP, '>' '/dev/null')
	rm('rf', TAR_TMP, '>' '/dev/null')
	rm('rf', MSC_TMP, '>' '/dev/null')