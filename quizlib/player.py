import random
import threading

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
        print "cancel"
        if self.tenSecondTimer is not None:
            self.tenSecondTimer.cancel()
        if self.isPlaying():
            xbmc.Player.stop(self)


    def playWindowed(self, file, idFile):
        print "!!!!!!!!!!!!! PlayWindowed"
        if self.tenSecondTimer is not None:
            self.stop()

        print "idFile " + str(idFile)
        # Get bookmark details, so we can restore after playback
        self.bookmark = self.database.fetchone("""
            SELECT idBookmark, timeInSeconds FROM bookmark WHERE idFile = ?
        """, idFile)
        if self.bookmark is None:
            self.bookmark = {'idFile' : idFile}

        self.play(item = file, windowed = True)

        retires = 0
        while not self.isPlaying() and retires < 20:
            xbmc.sleep(250) # keep sleeping to get onPlayBackStarted() event
            retires += 1

        print "playWindowed end"

    def onTenSecondsPassed(self):
        self.stop()

        retries = 0
        while self.isPlaying() and retries < 20:
            xbmc.sleep(250) # keep sleeping to get onPlayBackStopped() event
            retries += 1

        print "stopPlayback end"

    def onPlayBackStarted(self):
        print "!!!!!!!!!!!!PlayBack Started"

        totalTime = self.getTotalTime()
        # find start time, ignore first and last 10% of movie
        self.startTime = random.randint(int(totalTime * 0.1), int(totalTime * 0.9))

        print "Playback from %d secs. to %d secs." % (self.startTime, self.startTime + 10)
        self.seekTime(self.startTime)

        self.tenSecondTimer = threading.Timer(10.0, self.onTenSecondsPassed)
        self.tenSecondTimer.start()

    def onPlayBackStopped(self):
        print "!!!!!!!!!!!!PlayBack Stopped"
        self.stop()

        print "bookmark stuff"
        # Restore bookmark details
        if self.bookmark is not None:
            xbmc.sleep(1000) # Delay to allow XBMC to store the bookmark before resetting it
            print "Bookmark: %s" % str(self.bookmark)
            if self.bookmark.has_key('idFile'):
                print "deleting bookmark"
                self.database.execute("""
                    DELETE FROM bookmark WHERE idFile = ?
                """, self.bookmark['idFile'])
            else:
                print "resetting bookmark"
                self.database.execute("""
                    UPDATE bookmark SET timeInSeconds = ? WHERE idBookmark = ?
                """, (self.bookmark['timeInSeconds'], self.bookmark['idBookmark']))
