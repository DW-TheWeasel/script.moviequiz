import random
import threading
import db

__author__ = 'tommy'

import xbmc

class TenSecondPlayer(xbmc.Player):
    def __init__(self, database = None):
        xbmc.Player.__init__(self)
        self.tenSecondTimer = None
        self.startTime = None

        self.database = database
        self.bookmark = None

    def stop(self):
        xbmc.log("TenSecondPlayer.stop()")
        if self.tenSecondTimer is not None:
            self.tenSecondTimer.cancel()
        if self.isPlaying():
            xbmc.Player.stop(self)


    def playWindowed(self, file, idFile):
        xbmc.log("TenSecondPlayer.playWindowed()")
        if self.tenSecondTimer is not None:
            self.stop()

        # Get bookmark details, so we can restore after playback
        try:
            self.bookmark = self.database.fetchone("""
                SELECT idBookmark, timeInSeconds FROM bookmark WHERE idFile = ?
            """, idFile)
        except db.DbException:
            self.bookmark = {'idFile' : idFile}

        self.play(item = file, windowed = True)

        retires = 0
        while not self.isPlaying() and retires < 20:
            xbmc.sleep(250) # keep sleeping to get onPlayBackStarted() event
            retires += 1


    def onTenSecondsPassed(self):
        xbmc.log("TenSecondPlayer.onTenSecondsPassed()")
        self.stop()

        retries = 0
        while self.isPlaying() and retries < 20:
            xbmc.sleep(250) # keep sleeping to get onPlayBackStopped() event
            retries += 1


    def onPlayBackStarted(self):
        xbmc.log("TenSecondPlayer.onPlayBackStarted()")

        totalTime = self.getTotalTime()
        # find start time, ignore first and last 10% of movie
        self.startTime = random.randint(int(totalTime * 0.1), int(totalTime * 0.8))

        xbmc.log("Playback from %d secs. to %d secs." % (self.startTime, self.startTime + 10))
        self.seekTime(self.startTime)

        self.tenSecondTimer = threading.Timer(10.0, self.onTenSecondsPassed)
        self.tenSecondTimer.start()

    def onPlayBackStopped(self):
        xbmc.log("TenSecondPlayer.onPlayBackStopped()")
        if self.tenSecondTimer is not None:
            self.tenSecondTimer.cancel()

        print "bookmark stuff"
        # Restore bookmark details
        if self.bookmark is not None:
            xbmc.sleep(1000) # Delay to allow XBMC to store the bookmark before we reset it
            print "Bookmark: %s" % str(self.bookmark)
            if self.bookmark.has_key('idFile'):
                print "deleting bookmark"
                try:
                    self.database.execute("""
                        DELETE FROM bookmark WHERE idFile = ?
                    """, self.bookmark['idFile'])
                except db.DbException, ex:
                    print "Exception!"
            else:
                print "resetting bookmark"
                try:
                    self.database.execute("""
                        UPDATE bookmark SET timeInSeconds = ? WHERE idBookmark = ?
                    """, (self.bookmark['timeInSeconds'], self.bookmark['idBookmark']))
                except db.DbException, ex:
                    print "Exception!"

