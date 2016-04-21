import zipfile

zipFile = zipfile.ZipFile('temp.zip','r')
infolist = zipFile.infolist()
print map(lambda x: "%s %d" % (x.filename, x.file_size), infolist)
print zipFile.namelist()
