import fnmatch
import logging
import os
from subprocess import Popen
import time
from threading import Lock

log = logging.getLogger(__name__)


mutex = Lock()

MINIMUM_DISPLAY_NUMBER = 1000
USED_DISPLAY_NUMBER_LIST = []
HOST_DISPLAY_NUMBER = os.environ['DISPLAY']

class Display(Popen):
    # color_depth       8, 16, 24, or 32
    # size              (width, height)
    # bgcolor           'black' or 'white'

    def __init__(self, size=(1024,768), color_depth=24, bgcolor='black', **kwargs):
        self.color_depth = color_depth
        self.size = size
        self.bgcolor = bgcolor
        self.screen = 0
        self.process = None
        self.display = None

        mutex.acquire()
        try:
            self.display = self.get_next_free_display()
            while self.display in USED_DISPLAY_NUMBER_LIST:
                self.display += 1
            USED_DISPLAY_NUMBER_LIST.append(self.display)
        finally:
            mutex.release()

        Popen.__init__(self,self._cmd);

        self.redirect_display(True)
        time.sleep(0.1)


    @property
    def new_display_var(self):
        return ':%s' % (self.display)

    @property
    def _cmd(self):
        cmd = ['Xephyr',
               dict(black='-br', white='-wr')[self.bgcolor],
               '-screen',
               'x'.join(map(str, list(self.size) + [self.color_depth])),
               self.new_display_var,
               ]
        return cmd

    def lock_files(self):
        tmpdir = '/tmp'
        pattern = '.X*-lock'
        names = fnmatch.filter(os.listdir(tmpdir), pattern)
        ls = [os.path.join(tmpdir, child) for child in names]
        ls = [p for p in ls if os.path.isfile(p)]
        return ls

    def get_next_free_display(self):
        ls = [int(x.split('X')[1].split('-')[0]) for x in self.lock_files()]
        if len(ls):
            display = max(MINIMUM_DISPLAY_NUMBER, max(ls) + 1)
        else:
            display = MINIMUM_DISPLAY_NUMBER

        return display

    def redirect_display(self, on):
        # True -> set $DISPLAY to virtual screen
        # False -> set $DISPLAY to original screen

        d = self.new_display_var if on else HOST_DISPLAY_NUMBER
        if d is None:
            log.debug('unset DISPLAY')
            del os.environ['DISPLAY']
        else:
            log.debug('DISPLAY=%s', d)
            os.environ['DISPLAY'] = d


    def kill(self):
        self.redirect_display(False)
        Popen.kill(self)
        return self
