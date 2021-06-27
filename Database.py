from pathlib import Path
import sys, os
import shutil

from EasyPipe import Pipe

class Database:
    def __init__(self, name=None, dbpath=None):
        self.name = name
        self.dbpath = dbpath

    def dump(self):
        raise Exception(f'unimplemented')

    def recreateFromSQL(self):
        raise Exception(f'unimplemented')

    def restore(self, fileSql, interactive=True):
        fileSql = Path(fileSql).resolve()

        if not fileSql.exists():
            raise Exception("{fileSql} does not exist".format(fileSql=fileSql))

        name = self.name
        dbpath = self.dbpath
        dbstr = f"{dbpath}" if dbpath else f"{name}"

        if interactive:
            resp = print(f"""
Are you sure you want to restore database {name} from file {fileSql}?"
"""[1:-1])

            resp = input("[yes/no] ")

            if resp not in ('y', 'yes'):
                raise Exception('Aborted')

        cat = {
            '.xz': 'xzcat',
            '.bz2': 'bzcat',
            '.zip': 'zcat',
            '.gz': 'zcat',
        }.get(fileSql.suffix)

        inp = ""
        if cat:
            p = Pipe([cat, str(fileSql)])
            inp = p.stdout
        else:
            inp = fileSql.read_text()

        self.recreateFromSQL(inp)


class Database_sqlite(Database):
    def __init__(self, *arg, **kwarg):
        Database.__init__(self, *arg, **kwarg)

    def dump(self):
        dbpath = self.dbpath
        p = Pipe(["sqlite3", str(dbpath)], stdin=".dump\n")
        if p.status: raise Exception(f"sqlite3 failed (status = {p.status})")
        return p.stdout

    def recreateFromSQL(self, inp, keepBakFile=True):
        dbpath = self.dbpath
        if dbpath.exists():
            if keepBakFile:
                f0bak = str(dbpath) + '.bak'
                shutil.copy(str(dbpath), f0bak)
            dbpath.unlink()

        p = Pipe(['sqlite3', str(dbpath)], stdin=inp)
        if p.stderr:
            sys.stderr.write("sqlite3:\n")
            sys.stderr.write(p.stderr)
        if p.status: raise Exception(f'sqlite error: status={p.status}')


class Database_mysql(Database):
    def __init__(self, *arg, defaultsFile=None, **kwarg):
        if not defaultsFile: raise Exception(f'defaultsFile must be given')
        self.defaultsFile = defaultsFile.resolve()
        Database.__init__(self, *arg, **kwarg)

    def dump(self):
        name, defaultsFile = self.name, self.defaultsFile
        cmd = ["mysqldump", f'--defaults-file={defaultsFile}', name]

        p = Pipe(cmd)
        if p.status: raise Exception(f"mysqldump failed (status = {p.status}). Error message:\n{p.stderr}")
        return p.stdout

    def recreateFromSQL(self, inp):
        name, defaultsFile = self.name, self.defaultsFile
        print(inp)
