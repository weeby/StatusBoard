#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create and set up SQLite DB file."""
import sqlite3
import sys

def usage():
    """Print usage information and exit."""
    print 'usage: %s db_path' % (sys.argv[0], )
    sys.exit(1)
    
def main():
    if len(sys.argv) == 1:
        usage()
        
    db_path = sys.argv[1]
    if db_path.endswith('.sqlite') == False:
        db_path += '.sqlite'
        
    db = sqlite3.connect(db_path)
    cursor = db.execute('CREATE TABLE "xmpp_messages" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "created_at" DATETIME, "payload" TEXT)')
    db.commit()
    
    db.close()

if __name__ in ('__main__', 'main'):
    main()