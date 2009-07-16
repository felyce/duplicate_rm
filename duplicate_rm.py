#!/usr/bin/env python
# -*- coding:utf-8; mode:python-mode -*-
# Last Change:2009/07/17 02:09:41.
#
# GPL v3.
# 
# Copyright(c) 2009 Dai Takahashi 
# All rights reserved.
#
# このスクリプトを使用した結果については一切責任をとりません。
# すべて自己責任で使用してください。
#

from __future__ import with_statement
import os, os.path
import hashlib
import datetime

import sqlite3
import commands
import sys

# for Japanese
reload(sys)
sys.setdefaultencoding('utf-8')

class Duplicate_RM(object):

    TRASH = "~/.trash"
    HASH_MAX_BUFFER = 1024 * 16
    LOG_FILE = "duplicate_rm.log"
    
    def __init__(self, init_path):
        self.hash = {}
        self.file_list = []
        self.dir_list = []
        self.digest_list = []
        self.del_list = []
        self.count = 0
        self.message = []

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
                print("mkdir error.")

        for f in self.del_list:
            try:
                os.rename(f, os.path.join(trash, os.path.basename(f)) )
            except Exception, e:
                print("Renam Error.%s" % e)
        
    
    def _writeLog(self):
        try:
            with open( self.LOG_FILE, 'wa') as f:
                f.writelines(self.message)        

        except IOError, e:
            print('Log Write Error:%s' % e )


    def Run(self):
        print("Duplicate_rm start...searching now.")
        
        format = '%a, %y-%m-%d %H:%M:%S %z'
        start = datetime.datetime.now()
        self.message += "---- start %s ----\n\n" % start.strftime(format)

        self._MakeFileList()
        self._MakeDigestList()
        print("Duplicate Count:%d" % self.count)
        print("Deleting...")
        self._DeleteDuplicateFile()
        print("FINISH!.")

        end = datetime.datetime.now()
        time = end - start
        self.message += "---- end %s (%d min.)----\n\n" % \
                                    (end.strftime(format), time.seconds)
        print('%d sec.' % time.seconds)

        self._writeLog()


class Duplicate_RM_Sqlite(Duplicate_RM):
    """ using Sqlite3, md5sum(for Linux) """
#    DATABASE_FILE = ":memory:"
    DATABASE_FILE = ".duplicate_rm.db"
    DATABASE_TABLE = "md5hash"

    def __init__(self, path):

        self.process_count = 0
        
        super(Duplicate_RM_Sqlite, self).__init__(path)

        self.OnInit()


    def OnInit(self):
        super(Duplicate_RM_Sqlite, self).OnInit()

        try:
            self.cn = sqlite3.connect(self.DATABASE_FILE)
        except Exception, e:
            print(e)
            print('Cannt connect DATABASE_FILE')

        try:
            self.cn.execute('create table md5hash(full_path, md5)')
        except Exception, e:
            print(e)
            print('Cannot create Databese Table.')



    def _MakeMD5(self, name):
        result = commands.getoutput("md5sum '%s'" % name)
        md5 = result.split(' ')

        return md5[0]

        
    def _MakeDigestList(self):

        # リスト操作がしやすいように
        _full_path_ = 0
        _md5_       = 1

        self.process_count += 1
        
        cur = self.cn.cursor()

        for f in self.file_list:
            abs_f = os.path.abspath(f)
            
            try:
                # もしも、既にデータベースにフルパスが登録してあったら、
                # それは過日にチェックしてあることとする。
                cur.execute("select * from md5hash where full_path = ?", (abs_f, ))
                if len( cur.fetchall() ):
                    continue

            except Exception, e:
                print("MakeDigestList(check full_path):%s" % e )
            
            _md5hash = self._MakeMD5(f)


            try:
                cur.execute("select * from md5hash where md5 = ?", ( _md5hash, ))

                lst = cur.fetchall()

                if len( lst ):
                    item = lst[0]
                    self.message += "%s is duplicate.(%s)\n" % (f, item[ _full_path_ ])

                    if abs_f == item[ _full_path_ ]:
                        # same file
                        pass
                    
                    elif len(abs_f) < len( item[ _full_path_ ]):
                        self.del_list.append( item[ _full_path_ ] )
                        cur.execute("update md5hash set full_path = ? where md5 = ?", \
                                    (abs_f, _md5hash) )
                        
                    else:
                        self.del_list.append( abs_f )
                        self.count += 1

                else:
                    cur.execute('insert into md5hash (full_path, md5) values(?,?)',\
                                (abs_f, _md5hash))

                self.cn.commit()

            except Exception, e:
                print("_MakeDigestList:%s" % (e))


        def Run(self):
            super(Duplicate_RM_Sqlite, self).Run()
            print( "Process Count:%d" % self.process_count )
            self.cn.commit()
            self.cn.close()            

        def rmDatabase(self):
            if os.access( self.DATABASE_FILE, os.F_OK ):
                os.remove( self.DATABASE_FILE ) 

def main():
    import sys
    import optparse

    usage =  "usage: %prog [options] arg"
    parser = optparse.OptionParser()
    parser.add_option('-f','--force', action="store_true", \
                    default=False, \
                    dest='isForce', \
                    help='Re-make Database.')

    (options, args) = parser.parse_args()
    
    if options.isForce:
        if os.access( '.duplicate_rm.db', os.F_OK ):
            os.remove( '.duplicate_rm.db' )

    if 'linux' in sys.platform:
        dr = Duplicate_RM_Sqlite( args )

    else:
        dr = Duplicate_RM( args )

    dr.Run()

        
if __name__ == '__main__':
    main()

#    import cProfile
#    cProfile.run( 'main()' )
