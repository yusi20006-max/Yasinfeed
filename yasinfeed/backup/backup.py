import shutil

def backup(src,dst):
    shutil.copy2(src,dst)
