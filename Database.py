from EasyPipe import Pipe

class Database:
    def __init__(self, name=None):
        self.name = name

    def dump(self):
        raise Exception(f'unimplemented')

class Database_sqlite(Database):
    def __init__(self, *arg, dbpath=None, **kwarg):
        self.dbpath = dbpath
        Database.__init__(self, *arg, **kwarg)

    def dump(self):
        dbpath = self.dbpath
        p = Pipe(["sqlite3", str(dbpath)], stdin=".dump\n")
        if p.status: raise Exception(f"sqlite3 failed (status = {p.status})")
        return p.stdout

class Database_mysql(Database):
    def __init__(self, *arg, **kwarg):
        Database.__init__(self, *arg, **kwarg)
