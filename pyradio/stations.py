import csv
import sys
import glob
from os import path, getenv, makedirs, remove
from time import ctime
from shutil import copyfile

class PyRadioStations(object):
    """ PyRadio stations file management """

    stations_file = ''
    stations_filename_only = ''
    previous_stations_file = ''

    """ this is always on users config dir """
    stations_dir = ''

    foreign_file = False

    stations = []
    _reading_stations = []
    playlists = []

    selected_playlist = -1
    number_of_stations = -1

    dirty = False

    def __init__(self, stationFile=''):

        if sys.platform.startswith('win'):
            self.stations_dir = path.join(getenv('APPDATA'), 'pyradio')
        else:
            self.stations_dir = path.join(getenv('HOME', '~'), '.config', 'pyradio')
        """ Make sure config dir exists """
        if not path.exists(self.stations_dir):
            try:
                makedirs(self.stations_dir)
            except:
                print('Error: Cannot create config directory: "{}"'.format(self.stations_dir))
                sys.exit(1)
        self.root_path = path.join(path.dirname(__file__), 'stations.csv')

        """ If a station.csv file exitst, which is wrong,
            we rename it to stations.csv """
        if path.exists(path.join(self.stations_dir, 'station.csv')):
                copyfile(path.join(self.stations_dir, 'station.csv'),
                        path.join(self.stations_dir, 'stations.csv'))
                remove(path.join(self.stations_dir, 'station.csv'))

        self._move_old_csv(self.stations_dir)
        self._check_stations_csv(self.stations_dir, self.root_path)

    def _move_old_csv(self, usr):
        """ if a ~/.pyradio files exists, relocate it in user
            config folder and rename it to stations.csv, or if
            that exists, to pyradio.csv """

        src = path.join(getenv('HOME', '~'), '.pyradio')
        dst = path.join(usr, 'pyradio.csv')
        dst1 = path.join(usr, 'stations.csv')
        if path.exists(src) and path.isfile(src):
            if path.exists(dst1):
                copyfile(src, dst)
            else:
                copyfile(src, dst1)
            try:
                remove(src)
            except:
                pass

    def _check_stations_csv(self, usr, root):
        ''' Reclocate a stations.csv copy in user home for easy manage.
            E.g. not need sudo when you add new station, etc '''

        if path.exists(path.join(usr, 'stations.csv')):
            return
        else:
            copyfile(root, path.join(usr, 'stations.csv'))

    def is_same_playlist(self, a_playlist):
        """ Checks if a [laylist is already loaded """
        if a_playlist == self.stations_file:
            return True
        else:
            return False

    def is_playlist_reloaded(self):
        return self.is_same_playlist(self.previous_stations_file)

    def _is_playlist_in_config_dir(self):
        """ Check if a csv file is in the config dir """
        if path.dirname(self.stations_file) == self.stations_dir:
            self.foreign_file = False
        else:
            self.foreign_file = True
        self.foreign_copy_asked = False

    def read_playlist_file(self, stationFile=''):
        """ Read a csv file
            Returns: number, boolean
              number:
                x  -  number of stations or
               -1  -  error
               """
        orig_input = stationFile
        prev_file = self.stations_file
        ret = -1
        if stationFile:
            try_files = [ stationFile ]
            if not stationFile.endswith('.csv'):
                stationFile += '.csv'
            try_files.append(path.join(self.stations_dir, stationFile))
            for stationFile in try_files:
                if path.exists(stationFile) and path.isfile(stationFile):
                    ret = 0
                    break
        else:
            for p in [path.join(self.stations_dir, 'pyradio.csv'),
                      path.join(self.stations_dir, 'stations.csv'),
                      self.root_path]:
                if path.exists(p) and path.isfile(p):
                    stationFile = p
                    ret = 0
                    break

        if ret == -1:
            """ Check if playlist number was specified """
            if orig_input.isdigit():
                sel = int(orig_input) - 1
                if sel < 0:
                    """ negative playlist number """
                    return -1
                n, f = self.read_playlists()
                if sel <= n-1:
                    stationFile=self.playlists[sel][-1]
                else:
                    """ playlist number sel does not exit """
                    return -1
            else:
                return -1

        self._reading_stations = []
        with open(stationFile, 'r') as cfgfile:
            try:
                for row in csv.reader(filter(lambda row: row[0]!='#', cfgfile), skipinitialspace=True):
                    if not row:
                        continue
                    name, url = [s.strip() for s in row]
                    self._reading_stations.append((name, url))
            except:
                self._reading_stations = []
                return -1

        self.stations = list(self._reading_stations)
        self._reading_stations = []
        self._get_playlist_elements(stationFile)
        self.previous_stations_file = prev_file
        self._is_playlist_in_config_dir()
        self.number_of_stations = len(self.stations)
        self.dirty = False
        return self.number_of_stations

    def _get_playlist_elements(self, a_playlist):
        self.stations_file = path.abspath(a_playlist)
        self.stations_filename_only = path.basename(self.stations_file)
        self.stations_filename_only_no_extension = ''.join(self.stations_filename_only.split('.')[:-1])

    def _bytes_to_human(self, B):
        ''' Return the given bytes as a human friendly KB, MB, GB, or TB string '''
        KB = float(1024)
        MB = float(KB ** 2) # 1,048,576
        GB = float(KB ** 3) # 1,073,741,824
        TB = float(KB ** 4) # 1,099,511,627,776

        if B < KB:
            return '{0} B'.format(B)
        B = float(B)
        if KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)

    def append_station(self, params, stationFile=''):
        """ Append a station to csv file"""

        if stationFile:
            st_file = stationFile
        else:
            st_file = self.stations_file

        with open(st_file, 'a') as cfgfile:
            writter = csv.writer(cfgfile)
            writter.writerow(params)

    def remove_station(self, a_station):
        self.dirty = True
        ret = self.stations.pop(a_station)
        self.number_of_stations = len(self.stations)
        return ret, self.number_of_stations

    def read_playlists(self):
        self.playlists = []
        self.selected_playlist = -1
        files = glob.glob(path.join(self.stations_dir, '*.csv'))
        if len(files) == 0:
            return 0, -1
        else:
            for a_file in files:
                a_file_name = ''.join(path.basename(a_file).split('.')[:-1])
                a_file_size = self._bytes_to_human(path.getsize(a_file))
                a_file_time = ctime(path.getmtime(a_file))
                self.playlists.append([a_file_name, a_file_time, a_file_size, a_file])
        self.playlists.sort()
        """ get already loaded playlist id """
        for i, a_playlist in enumerate(self.playlists):
            if a_playlist[-1] == self.stations_file:
                self.selected_playlist = i
                break
        return len(self.playlists), self.selected_playlist

    def list_playlists(self):
        print('Playlists found in "{}"'.format(self.stations_dir))
        num_of_playlists, selected_playlist = self.read_playlists()
        pad = len(str(num_of_playlists))
        for i, a_playlist in enumerate(self.playlists):
            print('  {0}. {1}'.format(str(i+1).rjust(pad), a_playlist[0]))
