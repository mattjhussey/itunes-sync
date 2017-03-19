import xml.etree.ElementTree as ET
import shutil
import os
import urllib
import codecs

dirtyChars = {
    "?": "_",
    "/": "_",
    ":": "_",
    "<": "_",
    "\"": "_",
    "*": "_",
    "|": "_"}


def sanitizeString(s):
    s = s.strip()
    for dirty, clean in dirtyChars.iteritems():
        s = s.replace(dirty, clean)
    if s[len(s) - 1] == '.':
        s = s[:-1] + "_"
    return s


def getExtensionFiles(extension):
    found = set()
    for r, d, files in os.walk(u"."):
        for f in files:
            if f.endswith(extension):
                path = os.path.join(r, f)
                coded = path
                found.add(coded.lower())
    return found


def getM4aFiles():
    return getExtensionFiles(".m4a")


def check(expected):
    onDrive = getM4aFiles()
    for f in expected:
        if f in onDrive:
            onDrive.discard(f)
        else:
            # Missing!!!
            print "%s is missing" % repr(f)
    for f in onDrive:
        print "%s should not exist" % repr(f)


def readItunesLibrary(xmlPath):
    context = ET.iterparse(xmlPath, events=("start", "end"))

    key = "root"
    rootDict = dict()
    activeDict = rootDict
    path = []

    for event, elem in context:
        if elem.tag == "plist":
            continue
        if event == "start":
            if elem.tag == "key":
                key = elem.text
            else:
                if elem.tag == "dict":
                    newDict = dict()
                    if type(activeDict) is dict:
                        activeDict[key] = newDict
                    else:
                        activeDict.append(newDict)
                    path.append(activeDict)
                    activeDict = newDict
                elif elem.tag == "array":
                    newArray = []
                    if type(activeDict) is dict:
                        activeDict[key] = newArray
                    else:
                        activeDict.append(newArray)
                    path.append(activeDict)
                    activeDict = newArray
                else:
                    if elem.text is not None:
                        if type(activeDict) is dict:
                            activeDict[key] = elem.text
                        else:
                            activeDict.append(elem.text)
        elif event == "end":
            if elem.tag == "key":
                if elem.text is not None:
                    key = elem.text
            elif elem.tag == "dict" or elem.tag == "array":
                activeDict = path.pop()
            else:
                if elem.text is not None:
                    if type(activeDict) is dict:
                        activeDict[key] = elem.text
                    else:
                        activeDict.append(elem.text)
        elem.clear()
    return rootDict


def getWantedTrackIds(playlist):
    # Find the S3 playlist Track IDs
    trackIDs = set()
    # Get Playlist Items array
    playListItems = playlist["Playlist Items"]
    for trackDict in playListItems:
        # Dictionary of 1...
        trackId = trackDict["Track ID"]
        trackIDs.add(trackId)
    return trackIDs


def getWantedTracks(tracks):
    # Find each file to move
    trackInfo = dict()
    for trackId, track in tracks.iteritems():

        album = track["Album"]
        artist = track["Artist"]
        location = urllib.unquote(track["Location"][17:])
        time = track["Total Time"][:-3]

        trackData = dict()
        trackData["Time"] = time
        trackData["Album"] = album
        trackData["Artist"] = artist

        trackName = location.split("/")[-1]

        # Move file from location to /artist/album/trackName
        directory = "%s/%s" % (sanitizeString(artist), sanitizeString(album))
        target = "%s/%s" % (directory, unicode(trackName, "utf8"))

        setPath = os.path.join(".\\", sanitizeString(artist))
        setPath = os.path.join(setPath, sanitizeString(album))
        setPath = os.path.join(setPath, trackName.decode('utf-8'))

        trackData["Path"] = target
        trackData["Source"] = unicode(location, "utf8")
        trackData["Directory"] = directory
        trackData["WalkPath"] = setPath.lower()

#        try:
#            os.makedirs(directory)
#        except:
#            pass
#        if not os.path.exists(target):
#            print "Copying: %s" % repr(target)
#            shutil.copy(unicode(location, "utf8"), target)
        trackInfo[trackId] = trackData
    return trackInfo


def deleteFiles(files):
    fileCount = len(files)
    statement = "Deleting %%d of %d: %%s" % fileCount
    for n, file in enumerate(files):
        print statement % (n+1, repr(file))
        os.remove(file)


def copyFiles(copyTasks):
    copyCount = len(copyTasks)
    statement = "Copying %%d of %d: %%s" % copyCount
    for n, copyTask in enumerate(copyTasks):
        target = copyTask
        source = copyTasks[copyTask]
        print statement % (n+1, repr(target))
        shutil.copy(source, target)


def findEmptyDirectories():
    dirs = set()
    for r, d, files in os.walk(u"."):
        if u"albumart.pamp" in files:
            files.remove(u"albumart.pamp")
        if len(files) == 0 and len(d) == 0:
            dirs.add(r)
    return dirs


def deleteDirectories(directories):
    directoryCount = len(directories)
    statement = "Remove empty directory %%d of %d: %%s" % directoryCount
    for n, directory in enumerate(directories):
        print statement % (n, repr(directory))
        shutil.rmtree(directory)


def createDirectories(directories):
    directoryCount = len(directories)
    statement = "Creating directory %%d of %d: %%s" % directoryCount
    for n, directory in enumerate(directories):
        print statement % (n+1, repr(directory))
        os.makedirs(directory)


def findM3us():
    return getExtensionFiles(".m3u")


def buildM3us(playlists, tracks):
    # Create m3us for playlists containing any of these files
    trackIds = set(tracks.keys())
    for playlist in playlists:
        # Play list is a dictionary
        # Get all trackIds
        if "Playlist Items" in playlist:
            playlistItems = playlist["Playlist Items"]
            orderedTracks = list()
            playlistTracks = set()
            for item in playlistItems:
                trackId = item["Track ID"]
                playlistTracks.add(trackId)
                orderedTracks.append(trackId)
            # Get intersection or trackIDs and playlistTracks
            copiedInPlaylist = trackIds.intersection(playlistTracks)
            if len(copiedInPlaylist) > 0:
                # Write m3u
                filename = "%s.m3u" % sanitizeString(playlist["Name"])
                with codecs.open(filename, "w", "utf-8-sig") as file:
                    file.write("#EXTM3U\n")
                    for trackId in orderedTracks:
                        if trackId in tracks:
                            trackPath = tracks[trackId]
                            file.write("%s\n" % trackPath)


def doStuff(xmlPath, playlistName):
    print "Reading iTunes Library"
    library = readItunesLibrary(xmlPath)
    print "Finding %s Playlist" % playlistName
    s3List = [playlist
              for playlist in library["root"]["Playlists"]
              if playlist["Name"] == playlistName][0]
    print "Finding wanted Track Ids"
    trackIds = getWantedTrackIds(s3List)
    print "Finding wanted Tracks"
    tracks = dict([(id, value)
                   for id, value in library["root"]["Tracks"].iteritems()
                   if id in trackIds])
    print "Extracting Track Info"
    trackInfo = getWantedTracks(tracks)
    print "Finding existing files"
    existingFiles = getM4aFiles()
    print "Finding excess files"
    sourceFiles = set([trackData["WalkPath"]
                       for trackData in trackInfo.itervalues()])
    excessFiles = existingFiles.difference(sourceFiles)
    print "Deleting excess files"
    deleteFiles(excessFiles)
    print "Creating required directories"
    requiredDirectories = set([trackData["Directory"]
                               for trackData in trackInfo.itervalues()
                               if not os.path.exists(trackData["Directory"])])
    createDirectories(requiredDirectories)
    print "Copying new files"
    existingFiles = existingFiles.difference(excessFiles)
    copyTasks = dict([(ti["Path"], ti["Source"])
                      for ti in trackInfo.itervalues()
                      if ti["WalkPath"] not in existingFiles])
    copyFiles(copyTasks)
    print "Find empty directories"
    emptyDirs = findEmptyDirectories()
    print "Deleting empty directories"
    deleteDirectories(emptyDirs)
    print "Deleting existing m3us"
    existingM3us = findM3us()
    deleteFiles(existingM3us)
    print "Writing new m3us"
    playlists = library["root"]["Playlists"]
    trackPaths = dict([(id, track["Path"])
                       for id, track in trackInfo.iteritems()])
    buildM3us(playlists, trackPaths)
    print "Checking"
    check(sourceFiles)
    print "%d to copy and %d exist" % (len(sourceFiles), len(getM4aFiles()))


if __name__ == "__main__":
    doStuff(os.sys.argv[1], os.sys.argv[2])
