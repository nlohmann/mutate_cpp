# coding=utf-8

from app import db
import os
from datetime import datetime
from app.utils.Mutation import get_mutators
from app.utils.Replacement import Replacement
from app.models import File, Patch


class SourceFile:
    def __init__(self, file: File, first_line, last_line):
        self.file = file
        self.filename = file.filename
        self.full_content = [x.rstrip() for x in file.content.split('\n')]

        print(first_line, last_line)

        # the line numbers stored here are human-readable; to use them as indices to
        # self.full_content, we need to subtract -1
        self.first_line = first_line
        self.last_line = last_line

        if self.last_line == -1:
            self.last_line = len(self.full_content)

        # read the relevant content
        self.content = '\n'.join(self.full_content[self.first_line - 1:self.last_line])  # type: str

    def generate_patches(self):
        mutators = get_mutators()

        for line_number, line_raw in self.__get_lines():
            for mutator_name, mutator in mutators.items():
                for mutation in mutator.find_mutations(line_raw):
                    patch_text = self.__create_patch(line_number, mutation)

                    patch = Patch(kind=mutator_name,
                                  line=line_number,
                                  column_start=mutation.start_col,
                                  column_end=mutation.end_col,
                                  code_original=mutation.old_val,
                                  code_replacement=mutation.new_val,
                                  patch=patch_text,
                                  state='incomplete',
                                  confirmation='unknown',
                                  file_id=self.file.id,
                                  project_id=self.file.project_id)

                    db.session.add(patch)

        db.session.commit()

    def __get_lines(self):
        in_comment = False

        for line_number in range(self.first_line, self.last_line):
            line_raw = self.full_content[line_number - 1]
            line_stripped = line_raw.strip()

            # skip line comments and preprocessor directives
            if line_stripped.startswith('//') or line_stripped.startswith('#'):
                continue

            # skip empty lines or "bracket onlys"
            if line_stripped in ['', '{', '}', '};', '});', ')']:
                continue

            # recognize the beginning of a line comment
            if line_stripped.startswith('/*'):
                in_comment = True
                continue

            # skip assertions
            if line_stripped.startswith('assert(') or line_stripped.startswith('static_assert('):
                continue

            # skip "private" or "protected" declaration
            if line_stripped.startswith('private:') or line_stripped.startswith('protected:'):
                continue

            # recognize the end of a line comment
            if line_stripped.endswith('*/'):
                in_comment = False
                continue

            # return line to mutate
            if not in_comment:
                yield line_number, line_raw

    def __create_patch(self, line_number: int, replacement: Replacement) -> str:
        # get file date in the format we need to write it to the patch
        original_file_date = datetime.fromtimestamp(os.path.getmtime(self.filename)).strftime('%Y-%m-%d %H:%M:%S.%f')

        # passed line_number is human-readable
        index_line_number = line_number - 1
        old_line = self.full_content[index_line_number]
        new_line = replacement.apply(old_line)

        # number of lines before and after the changed line
        context_lines = 3
        context_before = self.full_content[max(0, index_line_number - context_lines):index_line_number]
        context_after = self.full_content[
                        index_line_number + 1:min(len(self.full_content), index_line_number + context_lines + 1)]

        patch_lines = []

        # first line: we want to change the source file
        patch_lines.append('--- {filename} {date}'.format(filename=self.filename, date=original_file_date) + os.linesep)
        # second line: the new file has the same name, but is changed now
        patch_lines.append('+++ {filename} {date}'.format(filename=self.filename, date=datetime.now()) + os.linesep)
        # third line: summarize the changes regarding to displayed lines
        patch_lines.append('@@ -{lineno},{context_length} +{lineno},{context_length_shortened} @@'.format(
            lineno=line_number - len(context_before),
            context_length=len(context_before) + len(context_after) + 1,
            context_length_shortened=len(context_before) + len(context_after) + (1 if new_line else 0)
        ) + os.linesep)

        # lines: context before
        patch_lines += [' ' + x + os.linesep for x in context_before]
        # line: the old value
        patch_lines.append('-' + old_line + os.linesep)
        # line: the new value
        if replacement.new_val is not None:
            patch_lines.append('+' + new_line + os.linesep)
        # lines: context after
        patch_lines += [' ' + x + os.linesep for x in context_after]

        patch_text = ''.join(patch_lines)
        return patch_text
