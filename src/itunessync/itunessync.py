"""Sync itunes music and playlists to sd card."""
import xml.etree.ElementTree as ET
import shutil
import os
import urllib
import codecs

DIRTY_CHARS = {
    "?": "_",
    "/": "_",
    ":": "_",
    "<": "_",
    "\"": "_",
    "*": "_",
    "|": "_"}


def sanitize_string(string_to_clean):
    """Sanitize a string.

    Remove surrounding whitespace,
    replace DIRTY_CHARS and replace trailing . with _.
    """
    string_to_clean = string_to_clean.strip()
    for dirty, clean in DIRTY_CHARS.iteritems():
        string_to_clean = string_to_clean.replace(dirty, clean)
    if string_to_clean[len(string_to_clean) - 1] == '.':
        string_to_clean = string_to_clean[:-1] + "_"
    return string_to_clean


def get_extension_files(extension):
    """Find all files that have the extension."""
    found = set()
    for root, _, files in os.walk(u"."):
        for found_file in files:
            if found_file.endswith(extension):
                path = os.path.join(root, found_file)
                coded = path
                found.add(coded.lower())
    return found


def get_m4a_files():
    """Return a set of all files that have m4a extension."""
    return get_extension_files(".m4a")


def check(expected):
    """Find mismatches with the expected files."""
    on_drive = get_m4a_files()
    for found_file in expected:
        if found_file in on_drive:
            on_drive.discard(found_file)
        else:
            # Missing!!!
            print "%s is missing" % repr(found_file)
    for found_file in on_drive:
        print "%s should not exist" % repr(found_file)


def read_itunes_library(xml_path):
    """Read the itunes library into memory."""
    context = ET.iterparse(xml_path, events=("start", "end"))

    key = "root"
    root_dict = dict()
    active_dict = root_dict
    path = []

    for event, elem in context:
        if elem.tag == "plist":
            continue
        if event == "start":
            if elem.tag == "key":
                key = elem.text
            else:
                if elem.tag == "dict":
                    new_dict = dict()
                    if isinstance(active_dict, dict):
                        active_dict[key] = new_dict
                    else:
                        active_dict.append(new_dict)
                    path.append(active_dict)
                    active_dict = new_dict
                elif elem.tag == "array":
                    new_array = []
                    if isinstance(active_dict, dict):
                        active_dict[key] = new_array
                    else:
                        active_dict.append(new_array)
                    path.append(active_dict)
                    active_dict = new_array
                else:
                    if elem.text is not None:
                        if isinstance(active_dict, dict):
                            active_dict[key] = elem.text
                        else:
                            active_dict.append(elem.text)
        elif event == "end":
            if elem.tag == "key":
                if elem.text is not None:
                    key = elem.text
            elif elem.tag == "dict" or elem.tag == "array":
                active_dict = path.pop()
            else:
                if elem.text is not None:
                    if isinstance(active_dict, dict):
                        active_dict[key] = elem.text
                    else:
                        active_dict.append(elem.text)
        elem.clear()
    return root_dict


def get_wanted_track_ids(playlist):
    """Get the ids of all the tracks in the playlist."""
    # Find the S3 playlist Track IDs
    track_ids = set()
    # Get Playlist Items array
    playlist_items = playlist["Playlist Items"]
    for track_dict in playlist_items:
        # Dictionary of 1...
        track_id = track_dict["Track ID"]
        track_ids.add(track_id)
    return track_ids


def get_wanted_tracks(tracks):
    """Get details of all wanted tracks."""
    # Find each file to move
    track_info = dict()
    for track_id, track in tracks.iteritems():

        album = track["Album"]
        artist = track["Artist"]
        location = urllib.unquote(track["Location"][17:])
        time = track["Total Time"][:-3]

        track_data = dict()
        track_data["Time"] = time
        track_data["Album"] = album
        track_data["Artist"] = artist

        track_name = location.split("/")[-1]

        # Move file from location to /artist/album/track_name
        directory = "%s/%s" % (sanitize_string(artist), sanitize_string(album))
        target = "%s/%s" % (directory, unicode(track_name, "utf8"))

        set_path = os.path.join(".\\", sanitize_string(artist))
        set_path = os.path.join(set_path, sanitize_string(album))
        set_path = os.path.join(set_path, track_name.decode('utf-8'))

        track_data["Path"] = target
        track_data["Source"] = unicode(location, "utf8")
        track_data["Directory"] = directory
        track_data["WalkPath"] = set_path.lower()

#        try:
#            os.makedirs(directory)
#        except:
#            pass
#        if not os.path.exists(target):
#            print "Copying: %s" % repr(target)
#            shutil.copy(unicode(location, "utf8"), target)
        track_info[track_id] = track_data
    return track_info


def delete_files(files):
    file_count = len(files)
    statement = "Deleting %%d of %d: %%s" % file_count
    for index, file_to_delete in enumerate(files):
        print statement % (index+1, repr(file_to_delete))
        os.remove(file_to_delete)


def copy_files(copy_tasks):
    copy_count = len(copy_tasks)
    statement = "Copying %%d of %d: %%s" % copy_count
    for index, copy_task in enumerate(copy_tasks):
        target = copy_task
        source = copy_tasks[copy_task]
        print statement % (index+1, repr(target))
        shutil.copy(source, target)


def find_empty_directories():
    dirs = set()
    for root, directory, files in os.walk(u"."):
        if u"albumart.pamp" in files:
            files.remove(u"albumart.pamp")
        if len(files) == 0 and len(directory) == 0:
            dirs.add(root)
    return dirs


def delete_directories(directories):
    directory_count = len(directories)
    statement = "Remove empty directory %%d of %d: %%s" % directory_count
    for index, directory in enumerate(directories):
        print statement % (index, repr(directory))
        shutil.rmtree(directory)


def create_directories(directories):
    directory_count = len(directories)
    statement = "Creating directory %%d of %d: %%s" % directory_count
    for index, directory in enumerate(directories):
        print statement % (index+1, repr(directory))
        os.makedirs(directory)


def find_m3us():
    return get_extension_files(".m3u")


def build_m3us(playlists, tracks):
    # Create m3us for playlists containing any of these files
    track_ids = set(tracks.keys())
    for playlist in playlists:
        # Play list is a dictionary
        # Get all track_ids
        if "Playlist Items" in playlist:
            playlist_items = playlist["Playlist Items"]
            ordered_tracks = list()
            playlist_tracks = set()
            for item in playlist_items:
                track_id = item["Track ID"]
                playlist_tracks.add(track_id)
                ordered_tracks.append(track_id)
            # Get intersection or track_ids and playlist_tracks
            copied_in_playlist = track_ids.intersection(playlist_tracks)
            if len(copied_in_playlist) > 0:
                # Write m3u
                filename = "%s.m3u" % sanitize_string(playlist["Name"])
                with codecs.open(filename, "w", "utf-8-sig") as file:
                    file.write("#EXTM3U\n")
                    for track_id in ordered_tracks:
                        if track_id in tracks:
                            track_path = tracks[track_id]
                            file.write("%s\n" % track_path)


def do_stuff(xml_path, playlist_name):
    print "Reading iTunes Library"
    library = read_itunes_library(xml_path)
    print "Finding %s Playlist" % playlist_name
    s3_list = [playlist
               for playlist in library["root"]["Playlists"]
               if playlist["Name"] == playlist_name][0]
    print "Finding wanted Track Ids"
    track_ids = get_wanted_track_ids(s3_list)
    print "Finding wanted Tracks"
    tracks = dict([(id, value)
                   for id, value in library["root"]["Tracks"].iteritems()
                   if id in track_ids])
    print "Extracting Track Info"
    track_info = get_wanted_tracks(tracks)
    print "Finding existing files"
    existing_files = get_m4a_files()
    print "Finding excess files"
    source_files = set([track_data["WalkPath"]
                        for track_data in track_info.itervalues()])
    excess_files = existing_files.difference(source_files)
    print "Deleting excess files"
    delete_files(excess_files)
    print "Creating required directories"
    required_directories = set([track_data["Directory"]
                                for track_data in track_info.itervalues()
                                if not os.path.exists(track_data["Directory"])])
    create_directories(required_directories)
    print "Copying new files"
    existing_files = existing_files.difference(excess_files)
    copy_tasks = dict([(ti["Path"], ti["Source"])
                       for ti in track_info.itervalues()
                       if ti["WalkPath"] not in existing_files])
    copy_files(copy_tasks)
    print "Find empty directories"
    empty_dirs = find_empty_directories()
    print "Deleting empty directories"
    delete_directories(empty_dirs)
    print "Deleting existing m3us"
    existing_m3us = find_m3us()
    delete_files(existing_m3us)
    print "Writing new m3us"
    playlists = library["root"]["Playlists"]
    track_paths = dict([(id, track["Path"])
                        for id, track in track_info.iteritems()])
    build_m3us(playlists, track_paths)
    print "Checking"
    check(source_files)
    print "%d to copy and %d exist" % (len(source_files), len(get_m4a_files()))


if __name__ == "__main__":
    do_stuff(os.sys.argv[1], os.sys.argv[2])
