# coding=utf-8


class Replacement:
    def __init__(self, start_col: int = None, end_col: int = None, old_val: str = None, new_val: str = None):
        self.start_col = start_col  # type: int
        self.end_col = end_col  # type: int
        self.old_val = old_val  # type: str
        self.new_val = new_val  # type: str

    def apply(self, line: str) -> str:
        # if the whole line is to be replaced, return the new value
        if self.end_col - self.start_col == len(line)-1:
            return self.new_val

        return '{prefix}{replacement}{suffix}'.format(
            prefix=line[:self.start_col],
            replacement=self.new_val,
            suffix=line[self.end_col:]
        )

    def __repr__(self):
        return '[({begin_col}:{end_col}) "{old_val}" -> "{new_val}"]'.format(
            begin_col=self.start_col,
            end_col=self.end_col,
            old_val=self.old_val,
            new_val=self.new_val
        )
