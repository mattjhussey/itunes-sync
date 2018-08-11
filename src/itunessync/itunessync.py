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


def read_itunes_library(xml_path):
    """Read the itunes library into memory."""
    context = ET.iterparse(xml_path, events=("start", "end"))
    print context

    def read_array(context):
        """Return a list of values.

        Return all values within an array tag.
        """
        my_list = []
        value = read_value(context)
        while value is not None:
            my_list.append(value)
            value = read_value(context)
        return my_list

    def read_dict(context):
        """Return a dictionary of key-value pairs.

        Returns all key-value pairs within a dict tag.
        """
        my_dict = dict()
        event, elem = next(context)
        while not (event == "end" and elem.tag == "dict"):
            # Get end of the key
            event, elem = next(context)
            assert event == "end" and elem.tag == "key"

            # Record the key
            key = elem.text

            my_dict[key] = read_value(context)

            # Move to next element
            event, elem = next(context)

        return my_dict

    def read_root(context):
        """Return a root node.

        Skims off the plist tag and returns the root dict.
        """
        # Skim off the plist
        next(context)

        # Skim off beginning of the dictionary
        next(context)

        return read_dict(context)

    def read_value(context):
        """Return a read value.

        Values are either a dict, array else a raw text value.
        """
        event, elem = next(context)
        if elem.tag == "dict":
            # I am a dictionary
            return read_dict(context)
        elif elem.tag == "array":
            if event == "start":
                # I am an array
                return read_array(context)

            # I am the end of an array
            return None

        # I am a primitive tag
        # Get end tag
        event, elem = next(context)
        print event, elem
        return elem.text

    root_dict = dict()
    root_dict["root"] = read_root(context)

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


def get_wanted_tracks(library, playlist_name):
    """Get details of all wanted tracks."""
    print "Finding %s Playlist" % playlist_name
    s3_list = [playlist
               for playlist in library["root"]["Playlists"]
               if playlist["Name"] == playlist_name][0]

    print "Finding wanted Track Ids"
    track_ids = get_wanted_track_ids(s3_list)

    print "Finding wanted Tracks"
    tracks = dict([(track_id, value)
                   for track_id, value in library["root"]["Tracks"].iteritems()
                   if track_id in track_ids])

    # Find each file to move
    track_info = dict()
    for track_id, track in tracks.iteritems():

        track_data = dict()
        track_data["Time"] = track["Total Time"][:-3]
        track_data["Album"] = track["Album"]
        track_data["Artist"] = track["Artist"]

        location = urllib.unquote(track["Location"][17:])
        track_name = location.split("/")[-1]

        # Move file from location to /artist/album/track_name
        set_path = os.path.join(".\\", sanitize_string(track_data["Artist"]))
        set_path = os.path.join(set_path, sanitize_string(track_data["Album"]))
        set_path = os.path.join(set_path, track_name.decode('utf-8'))

        track_data["Directory"] = "%s/%s" % (
            sanitize_string(track_data["Artist"]),
            sanitize_string(track_data["Album"]))
        track_data["Path"] = "%s/%s" % (
            track_data["Directory"],
            unicode(track_name, "utf8"))
        track_data["Source"] = unicode(location, "utf8")
        track_data["WalkPath"] = set_path.lower()

        track_info[track_id] = track_data
    return track_info


def delete_files(files):
    """Delete listed files."""
    file_count = len(files)
    statement = "Deleting %%d of %d: %%s" % file_count
    for index, file_to_delete in enumerate(files):
        print statement % (index+1, repr(file_to_delete))
        os.remove(file_to_delete)


def copy_files(copy_tasks):
    """Copy music files."""
    copy_count = len(copy_tasks)
    statement = "Copying %%d of %d: %%s" % copy_count
    for index, copy_task in enumerate(copy_tasks):
        target = copy_task
        source = copy_tasks[copy_task]
        print statement % (index+1, repr(target))
        shutil.copy(source, target)


def find_empty_directories():
    """Find directories with no contents."""
    dirs = set()
    for root, directory, files in os.walk(u"."):
        if u"albumart.pamp" in files:
            files.remove(u"albumart.pamp")
        if not files and not directory:
            dirs.add(root)
    return dirs


def delete_empty_directories():
    """Remove empty directories."""
    empty_dirs = find_empty_directories()

    directory_count = len(empty_dirs)
    statement = "Remove empty directory %%d of %d: %%s" % directory_count
    for index, directory in enumerate(empty_dirs):
        print statement % (index, repr(directory))
        shutil.rmtree(directory)


def create_directories(directories):
    """Create directories to accomodate the music."""
    directory_count = len(directories)
    statement = "Creating directory %%d of %d: %%s" % directory_count
    for index, directory in enumerate(directories):
        print statement % (index+1, repr(directory))
        os.makedirs(directory)


def find_m3us():
    """Find all files with extension .m3u."""
    return get_extension_files(".m3u")


def build_m3us(playlists, tracks):
    """Create m3us for playlists containing any of these files."""
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
            if copied_in_playlist:
                # Write m3u
                filename = "%s.m3u" % sanitize_string(playlist["Name"])
                with codecs.open(filename, "w", "utf-8-sig") as m3u_file:
                    m3u_file.write("#EXTM3U\n")
                    for track_id in ordered_tracks:
                        if track_id in tracks:
                            track_path = tracks[track_id]
                            m3u_file.write("%s\n" % track_path)


def copy_music(track_info):
    """Copy wanted music and remove unwanted."""
    print "Finding existing files"
    existing_files = get_m4a_files()

    print "Finding excess files"
    source_files = set([track_data["WalkPath"]
                        for track_data in track_info.itervalues()])

    print "Deleting excess files"
    excess_files = existing_files.difference(source_files)
    delete_files(excess_files)

    print "Creating required directories"
    required_directories = set(
        [track_data["Directory"]
         for track_data in track_info.itervalues()
         if not os.path.exists(track_data["Directory"])])
    create_directories(required_directories)

    print "Copying new files"
    existing_files = existing_files.difference(excess_files)
    copy_tasks = dict([(ti["Path"], ti["Source"])
                       for ti in track_info.itervalues()
                       if ti["WalkPath"] not in existing_files])
    copy_files(copy_tasks)

    print "Deleting empty directories"
    delete_empty_directories()

    print "Checking"
    check(source_files)

    print "%d to copy and %d exist" % (len(source_files), len(get_m4a_files()))


def copy_playlists(library, track_info):
    """Copy playlists containing wanted tracks."""
    print "Deleting existing m3us"
    existing_m3us = find_m3us()
    delete_files(existing_m3us)

    print "Writing new m3us"
    playlists = library["root"]["Playlists"]
    track_paths = dict([(track_id, track["Path"])
                        for track_id, track in track_info.iteritems()])
    build_m3us(playlists, track_paths)


def do_stuff(xml_path, playlist_name):
    """Copy music in playlist to cwd."""
    print "Reading iTunes Library"
    library = read_itunes_library(xml_path)

    print "Extracting Track Info"
    track_info = get_wanted_tracks(library, playlist_name)

    copy_music(track_info)

    copy_playlists(library, track_info)
