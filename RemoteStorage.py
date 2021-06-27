import sys, os
from pathlib import Path
import shutil
import re

from EasyPipe import Pipe
import shutil
import re

class RemoteStorage:
    def __init__(self,
        server = None,
        remote_user = None,
        key_file = None,
        remote_dir = None,
        local_dir = None,
    ):
        if not server: raise Exception(f'server must be given')
        if not remote_user: raise Exception(f'remote_user must be given')
        if not key_file: raise Exception(f'key_file must be given')
        if not remote_dir: raise Exception(f'remote_dir must be given')
        if not local_dir: raise Exception(f'local_dir must be given')

        self.server = server
        self.remote_user = remote_user
        self.key_file = key_file
        self.remote_dir = remote_dir
        self.local_dir = local_dir

        self.ssh_cmd_base = ssh_cmd_base = ['ssh', '-i', key_file]
        self.ssh_cmd = ssh_cmd = ssh_cmd_base + [remote_user + '@' + server]
        self.rsync_cmd = rsync_cmd = ['rsync', '-e', ' '.join(ssh_cmd_base)]

    def getLatestRemoteFiles(self, srcDir, prefixes=None):
        cmd = self.ssh_cmd + [
            "ls", "--almost-all", str(srcDir),
        ]

        p = Pipe(cmd)
        if p.status: raise Exception(f'remote ls failed (status={p.status})')

        matchesPrefixes = lambda f: not prefixes or any(
            re.search(r'^' + fnPrefix, f.stem) for fnPrefix in prefixes
        )

        fs = list(filter(
            lambda f:
                re.search(r'\.[a-z0-9]+\.xz', "".join(f.suffixes)) and
                matchesPrefixes(f),
            map(
                lambda l: Path(l.strip()),
                p.stdout.split("\n"),
            ),
        ))

        fsByPrefix = {}
        for f in fs:
            prefix = re.sub(r'^(.*)_[0-9]+\.[a-z0-9]+\.xz', r'\1', f.name)

            pfs = fsByPrefix.setdefault(prefix, [])
            pfs += [f]

        for pfs in fsByPrefix.values(): pfs.sort()

        fs = list(
            pfs[-1] for prefix, pfs in sorted(
                fsByPrefix.items(), key = lambda x: x[0]
            )
        )

        return fs

    def downloadFile(self, srcDir, dstDir, f):
        src = f"{self.remote_user}@{self.server}:/{srcDir}/{f}"
        dst = f"{dstDir}/"

        cmd = self.rsync_cmd + [src, dst]

        print(f'downloading {src} -> {dst}')
        print('    rsync command:', cmd)
        p = Pipe(cmd)

    def downloadBackups(self, prefixes=None, cbAfterEachDL=None):
        srcDir = self.remote_dir
        dstDir = self.local_dir
        fs = self.getLatestRemoteFiles(srcDir, prefixes=prefixes)
        if not fs: raise Exception('no backups found')

        dstDir.mkdir(parents=True, exist_ok=True)

        for f in fs:
            self.downloadFile(srcDir, dstDir, f)
            if cbAfterEachDL: cbAfterEachDL(f)
