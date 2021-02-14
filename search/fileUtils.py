import os.path
from os import path

# the function will return a list of docs from file
def readDataFromindexJson(file):
    return [l.strip() for l in open(str(file), encoding="utf8", errors='ignore')]

# returns filepath if file exists else returns a base image i.e D00000
def fileExists(filePath, figId):
    if path.exists('./'+filePath):
        return filePath
    else:
        return filePath[:-10] + 'D00000.png'

if __name__ == '__main__':
    
    print('File Exists', path.exists("../dataset/images/USD0872385-20200107-D00006.png"))
    print('File Exists at path', fileExists("dataset/images/USD0872385-20200107-D00006.png", 'p-0000'))    
    print('File Exists at path', fileExists("dataset/images/USD0872385-20200107-D00007.png", 'p-0000'))