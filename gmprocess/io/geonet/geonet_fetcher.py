# stdlib imports
from datetime import timedelta
import tempfile
import os.path
import io
import urllib
import ftplib
import logging
import shutil

# third party imports
import pytz
import numpy as np
import requests
from openquake.hazardlib.geo.geodetic import geodetic_distance
from obspy.core.utcdatetime import UTCDateTime
import pandas as pd

# local imports
from gmprocess.io.fetcher import DataFetcher
from gmprocess.io.geonet.core import read_geonet
from gmprocess.streamcollection import StreamCollection


CATBASE = 'https://quakesearch.geonet.org.nz/csv?bbox=163.95996,-49.18170,182.63672,-32.28713&startdate=%s&enddate=%s'
GEOBASE = 'ftp://ftp.geonet.org.nz/strong/processed/Proc/[YEAR]/[MONTH]/'
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
NZTIMEDELTA = 2  # number of seconds allowed between GeoNet catalog time and event timestamp on FTP site
NZCATWINDOW = 5 * 60  # number of seconds to search around in GeoNet EQ catalog
KM2DEG = 1 / 111.0


class GeoNetFetcher(DataFetcher):
    def __init__(self, time, lat, lon,
                 depth, magnitude,
                 user=None, password=None,
                 radius=100, dt=16, ddepth=30,
                 dmag=0.3,
                 rawdir=None):
        """Create a GeoNetFetcher instance.

        Args:
            time (datetime): Origin time.
            lat (float): Origin latitude.
            lon (float): Origin longitude.
            depth (float): Origin depth.
            magnitude (float): Origin magnitude.
            user (str): (Optional) username for site.
            password (str): (Optional) password for site.
            radius (float): Search radius (km).
            dt (float): Search time window (sec).
            ddepth (float): Search depth window (km).
            dmag (float): Search magnitude window (magnitude units).
            rawdir (str): Path to location where raw data will be stored.
                          If not specified, raw data will be deleted.
        """

        tz = pytz.UTC
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.radius = radius
        self.dt = dt
        self.rawdir = rawdir
        self.depth = depth
        self.magnitude = magnitude
        self.ddepth = ddepth
        self.dmag = dmag

    def getMatchingEvents(self, solve=True):
        """Return a list of dictionaries matching input parameters.

        Args:
            solve (bool):
                If set to True, then this method
                should return a list with a maximum of one event.

        Returns:
            list: List of event dictionaries, with fields:
                  - time Event time (UTC)
                  - lat Event latitude
                  - lon Event longitude
                  - depth Event depth
                  - mag Event magnitude
        """
        start_time = self.time - timedelta(seconds=3600)
        end_time = self.time + timedelta(seconds=3600)

        tpl = (start_time.strftime(TIMEFMT),
               end_time.strftime(TIMEFMT))
        url = CATBASE % tpl
        req = requests.get(url)
        data = req.text
        f = io.StringIO(data)
        df = pd.read_csv(f, parse_dates=['origintime'])
        # some of the column names have spaces in them
        cols = df.columns
        newcols = {}
        for col in cols:
            newcol = col.strip()
            newcols[col] = newcol
        df = df.rename(columns=newcols)
        lats = df['latitude'].values
        lons = df['longitude'].values
        etime = pd.Timestamp(self.time).tz_convert('UTC')
        dtimes = np.abs(df['origintime'] - etime)
        distances = geodetic_distance(self.lon, self.lat, lons, lats)
        didx = distances <= self.radius
        tidx = (dtimes <= np.timedelta64(int(self.dt), 's')).values
        newdf = df[didx & tidx]
        events = []
        for idx, row in newdf.iterrows():
            eventdict = {'time': UTCDateTime(row['origintime']),
                         'lat': row['latitude'],
                         'lon': row['longitude'],
                         'depth': row['depth'],
                         'mag': row['magnitude']}
            events.append(eventdict)

        if solve and len(events) > 1:
            event = self.solveEvents(events)
            events = [event]

        return [events]

    def retrieveData(self, event_dict):
        """Retrieve data from GeoNet FTP, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of getMatchingEvents().

        Returns:
            StreamCollection: StreamCollection object.
        """
        rawdir = self.rawdir
        if self.rawdir is None:
            rawdir = tempfile.mkdtemp()
        etime = event_dict['time']
        neturl = GEOBASE.replace('[YEAR]', str(etime.year))
        monthstr = etime.strftime('%m_%b')
        neturl = neturl.replace('[MONTH]', monthstr)
        urlparts = urllib.parse.urlparse(neturl)
        ftp = ftplib.FTP(urlparts.netloc)
        ftp.login()  # anonymous
        dirparts = urlparts.path.strip('/').split('/')
        for d in dirparts:
            try:
                ftp.cwd(d)
            except ftplib.error_perm as msg:
                raise Exception(msg)

        # cd to the desired output folder
        os.chdir(rawdir)
        datafiles = []

        # create the event folder name from the time we got above
        fname = etime.strftime('%Y-%m-%d_%H%M%S')

        try:
            ftp.cwd(fname)
        except ftplib.error_perm:
            msg = 'Could not find an FTP data folder called "%s". Returning.' % (
                urllib.parse.urljoin(neturl, fname))
            raise Exception(msg)

        dirlist = ftp.nlst()
        for volume in dirlist:
            if volume.startswith('Vol1'):
                ftp.cwd(volume)
                if 'data' not in ftp.nlst():
                    ftp.cwd('..')
                    continue

                ftp.cwd('data')
                flist = ftp.nlst()
                for ftpfile in flist:
                    if not ftpfile.endswith('V1A'):

                        continue
                    localfile = os.path.join(os.getcwd(), ftpfile)
                    if localfile in datafiles:
                        continue
                    datafiles.append(localfile)
                    f = open(localfile, 'wb')
                    logging.info('Retrieving remote file %s...\n' % ftpfile)
                    ftp.retrbinary('RETR %s' % ftpfile, f.write)
                    f.close()
                ftp.cwd('..')
                ftp.cwd('..')

        ftp.quit()
        streams = []
        for dfile in datafiles:
            print(dfile)
            streams += read_geonet(dfile)

        if self.rawdir is None:
            shutil.rmtree(rawdir)

        stream_collection = StreamCollection(streams=streams)
        return stream_collection