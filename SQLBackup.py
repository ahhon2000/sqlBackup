import os, sys
from pathlib import Path
import re

from Date import Date
from EasyPipe import Pipe

from Database import Database_sqlite, Database_mysql

class SQLBackup:
    def __init__(self,
        dbpath = None,
        dbtype = None,
        dirBackup = None,
        daysToKeepBackups = 30,
    ):
        """Initialise an SQLBackup object

        dbpath can be a path to an sqlite DB, a directory containing a number of
        sqlite DBs, or a database name (MySQL, ...)
        """
        
        if not dirBackup: raise Exception(f'dirBackup missing')
        if not dbtype: raise Exception(f'dbtype missing')
        if dbtype not in ('sqlite', 'mysql'):
            raise Exception(f'unsupported dbtype: {dbtype}')

        if daysToKeepBackups <= 0: raise Exception(f'daysToKeepBackups must be non-negative')

        self.dirBackup = Path(dirBackup).resolve()
        self.dbtype = dbtype
        self.dbpath = Path(dbpath).resolve()
        self.daysToKeepBackups = daysToKeepBackups

    def fileIsDb(self, f):
        return f.is_file()  and  f.suffix == '.db'  and  f.stem[0] != '.'

    def backupIsOld(self, f):
        if not f.is_file()  or  "".join(f.suffixes) != '.sql.xz': return False

        dtxt = re.sub(r'.*_(.*).sql.xz', r'\1', f.name)
        d = Date(dtxt)
        dn = Date('now')

        if d.daysEarlier(dn) > self.daysToKeepBackups:
            return True

        return False

    def rmOlderBackups(self):
        dirBackup = self.dirBackup
        fs = list(filter(
            self.backupIsOld,
            map(
                lambda f: Path(dirBackup) / f,
                os.listdir(str(dirBackup)),
            ),
        ))

        for f in fs:
            f.unlink()

    def getDatabases(self):
        dbpath = self.dbpath
        dbtype = self.dbtype
        if dbtype == 'sqlite':
            fs = None
            if dbpath.is_dir():
                fs = filter(
                    self.fileIsDb,
                    map(
                        lambda f: dbpath / f,
                        os.listdir(str(dbpath)),
                    ),
                )
            else:
                fs = (dbpath,)

            for f in fs:
                db = Database_sqlite(name=f.stem, dbpath=f)
                yield db
        elif dbtype == 'mysql':
            if not isinstance(dbpath, str): raise Exception(f'dpath is not a string: {dbpath}')
            for db in (Database_mysql(name=dpath),):
                yield db
        else: raise Exception(f'unsupported db type: {dbtype}')

    def backup(self):
        dirBackup = self.dirBackup
        dirBackup.mkdir(parents=True, exist_ok=True)
        if not dirBackup.exists(): raise Exception('{dirBackup} does not exist and cannot be created'.format(dirBackup=dirBackup))

        dn = Date('now')
        dntxt = dn.toText()

        for db in self.getDatabases():
            l = db.name
            fdst = dirBackup / f"{l}_{dntxt}.sql"
            s = db.dump()
            fdst.write_text(s)

            p = Pipe(['xz', str(fdst)])
            if p.status:
                raise Exception(f'archiver failed (status = {p.status})')

            self.rmOlderBackups()
