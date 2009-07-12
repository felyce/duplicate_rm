#!/usr/bin/env python
# -*- coding:utf-8; mode:python-mode -*-
# Last Update:2009/7/12 01:18:20.

import os, os.path
import hashlib


class Duplicate_RM(object):

    TRASH = "~/.trash"
    HASH_MAX_BUFFER = 1024 * 16
    
    def __init__(self, init_path):
        self.hash = {}
        self.file_list = []
        self.dir_list = []
        self.digest_list = []
        self.del_list = []
        self.count = 0
        self.message = ""

        self.root_path = init_path

        self.OnInit()


    def OnInit(self):
        for item in self.root_path:
            if os.path.isdir( item ):
                self.dir_list.append( os.path.abspath(item) )
            else:
                self.file_list.append( os.path.abspath(item) )


    def _MakeMD5(self, name):
            fp = open(name, 'rb')

            buf = ""
            md5 = ""
            while True:
                buf = fp.read( self.HASH_MAX_BUFFER )
                if buf:
                    md5 = hashlib.md5( buf )
                else:
                    break

            return md5.digest()


    def _MakeFileList(self):
        """ 引数に複数のディレクトリを指定されていたときの対処 """
        for path in self.dir_list:
            self._Walk(path)
            
    """        
         for d in self.dir_list:
            items = listdir(d)
            for item in items:
                self.file_list.append( os.abspath( item ) )
    """


    def _MakeDigestList(self):
        for f in self.file_list:
            md5hash = self._MakeMD5(f)
            abs_f = os.path.abspath(f)
            
            if md5hash in self.digest_list:
                self.message += "%s is duplicate.(%s)\n" % (f, self.hash[md5hash])

                if len(abs_f) == self.hash[md5hash]:
                    # same file
                    pass
                elif len(abs_f) < len(self.hash[md5hash]):
                    self.del_list.append( self.hash[md5hash] )
                    self.hash[md5hash] = abs_f
                else:
                    self.del_list.append( abs_f )
                    self.count += 1
            
            else:
                self.digest_list.append( md5hash )
                self.hash[md5hash] = os.path.abspath(f)


    def _Walk(self, path):
        for root, dirs, files in os.walk(path):
            for name in files:
                self.file_list.append( os.path.join(root, name) )


    def _DeleteDuplicateFile(self):
        trash = os.path.expanduser(self.TRASH)
        if not os.access(trash, os.W_OK):
            try:
                os.mkdir(trash)
            except:
                print "mkdir error."

        for f in self.del_list:
            try:
                os.rename(f, os.path.join(trash, os.path.basename(f)) )
            except:
                print "Renam Error."
        

    def Run(self):
        print("Duplicate_rm start...searching now.")
        self._MakeFileList()
        Self._makedigestlist()
        Print("Duplicate Count:%D" % Self.Count)
        Print("Deleting...")
        Self._deleteduplicatefile()
        Print(Self.Message)
        print("finish.")
        
        
def main():
    import sys

    dr = Duplicate_RM( sys.argv[1:] )
    dr.Run()

        
if __name__ == '__main__':
#    main()
    import cProfile

    cProfile.run( 'main()' )
