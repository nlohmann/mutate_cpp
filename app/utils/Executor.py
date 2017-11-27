# coding=utf-8

import shlex
import subprocess
from threading import Timer, Thread
import psutil
from app.models import Patch, Run, File
import tempfile
import os
import datetime
from app import db


class Executor:
    def __init__(self, app):
        self.__processes = []
        self.running = False
        self.app = app
        self.__current_patch = None

    def start(self):
        if self.__current_patch is None:
            self.running = True
            Thread(target=self.main).start()

    def stop(self):
        self.running = False

    @property
    def count(self):
        return Patch.query.filter(Patch.state == 'incomplete').count()

    @property
    def current_patch(self):
        return self.__current_patch

    def main(self):
        with self.app.app_context():
            while self.running:
                for patch in Patch.query.filter(Patch.state == 'incomplete').all():
                    if self.running:
                        self.workflow(patch)
                self.stop()

    def __execute_command_timeout(self, command, timeout=None, cwd=None, stdin=None):
        proc = subprocess.Popen(shlex.split(command), stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=cwd)
        self.__processes.append(proc.pid)

        def killer(process):
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):  # or parent.children() for recursive=False
                child.kill()
            parent.kill()

        timer = Timer(timeout, killer, (proc,))
        try:
            timer.start()
            stdout, stderr = proc.communicate()
            errcode = proc.returncode
            cancelled = not timer.is_alive()
        finally:
            timer.cancel()

        self.__processes.remove(proc.pid)

        if cancelled:
            raise subprocess.TimeoutExpired(command, timeout, stdout)

        if errcode != 0:
            raise subprocess.CalledProcessError(errcode, command, stdout)

        return stdout

    def workflow(self, patch: Patch):
        assert self.__current_patch is None, 'no auto-concurrency!'
        
        file = File.query.get(patch.file_id)
        
        if file is not None:
            self.__current_patch = patch

            # step 1: write patch to temp file
            patchfile = tempfile.NamedTemporaryFile(delete=False, mode='w')
            patchfile.write(patch.patch)
            patchfile.close()

            # step 2: apply patch
            self.__execute_command_timeout('patch -p1 --input={patchfile} {inputfile}'.format(patchfile=patchfile.name, inputfile=file.filename), cwd='/')

            # step 3: command pipeline
            success = self.__apply_command(patch, 'build_command') and \
                      self.__apply_command(patch, 'quickcheck_command') and \
                      self.__apply_command(patch, 'test_command')

            if success:
                 patch.state = 'survived'
                 db.session.commit()

            # step 4: revert patch
            self.__execute_command_timeout('patch -p1 --reverse --input={patchfile} {inputfile}'.format(patchfile=patchfile.name, inputfile=file.filename),
                                       cwd='/')

            # step 6: delete patch file
            os.remove(patchfile.name)

            self.__current_patch = None

    def __apply_command(self, patch: Patch, step: str):
        print(patch, step)

        if step == 'quickcheck_command':
            timeout = patch.project.quickcheck_timeout
            command = patch.project.quickcheck_command
        elif step == 'test_command':
            timeout = patch.project.test_timeout
            command = patch.project.test_command
        elif step == 'build_command':
            timeout = None
            command = patch.project.build_command
        elif step == 'clean_command':
            timeout = None
            command = patch.project.clean_command
        else:
            raise NotImplementedError

        # if no command is provided, return without creating a run; True means: next command must be executed
        if not command:
            return True

        run = Run()
        run.command = step
        run.patch_id = patch.id
        run.project_id = patch.project_id
        run.timestamp_start = datetime.datetime.now()

        # execute command
        try:
            output = self.__execute_command_timeout(command, cwd=patch.project.workdir, timeout=timeout)
            timeout = False
            success = True
            nochange = False
        except subprocess.CalledProcessError as e:
            output = e.output
            timeout = False
            success = False
            nochange = e.returncode == 77
        except subprocess.TimeoutExpired as e:
            output = e.output
            timeout = True
            success = False
            nochange = False

        run.output = str(output, encoding='utf-8', errors='ignore')

        run.timestamp_end = datetime.datetime.now()
        run.duration = (run.timestamp_end - run.timestamp_start).total_seconds()

        # determine log message
        if success:
            log = 'success'
        elif timeout:
            log = 'timeout'
        elif nochange:
            log = 'nochange'
        else:
            log = 'failure'

        run.log = log
        run.success = success

        db.session.add(run)

        if not success:
            patch.state = 'killed'

        db.session.commit()

        return success
