import json
import sys


def maybe_utf8(s):
    if isinstance(s, int):
        # s can be also an int for ex messages count
        return str(s)
    if isinstance(s, float):
        # s can be also a float for message rate
        return str(s)
    if sys.version_info[0] == 3:
        # It will have an encoding, which Python will respect
        return s
    else:
        # It won't have an encoding, and Python will pick ASCII by default
        return s.encode('utf-8')


class Lister:
    def verbose(self, string):
        if self.options.verbose:
            print(string)

    def display(self, json_list):
        depth = sys.maxsize
        if len(self.columns) == 0:
            depth = int(self.options.depth)
        (columns, table) = self.list_to_table(json.loads(json_list), depth)
        if len(table) > 0:
            self.display_list(columns, table)
        else:
            self.verbose("No items")

    def list_to_table(self, items, max_depth):
        columns = {}
        column_ix = {}
        row = None
        table = []

        def add(prefix, depth, item, fun):
            for key in item:
                column = prefix == '' and key or (prefix + '.' + key)
                subitem = item[key]
                if type(subitem) == dict:
                    fun(column, json.dumps(subitem))
                    # if 'json' in self.obj_info and key in self.obj_info['json']:
                    #     fun(column, json.dumps(subitem))
                    # else:
                    #     if depth < max_depth:
                    #         add(column, depth + 1, subitem, fun)
                elif type(subitem) == list:
                    # The first branch has mirrors in queues in
                    # mind (which come out looking decent); the second
                    # one has applications in nodes (which look less
                    # so, but what would look good?).
                    if [x for x in subitem if type(x) != str] == []:
                        serialised = " ".join(subitem)
                    else:
                        serialised = json.dumps(subitem)
                    fun(column, serialised)
                else:
                    fun(column, subitem)

        def add_to_columns(col, val):
            columns[col] = True

        def add_to_row(col, val):
            if col in column_ix:
                if val is not None:
                    row[column_ix[col]] = maybe_utf8(val)
                else:
                    row[column_ix[col]] = None

        if len(self.columns) == 0:
            for item in items:
                add('', 1, item, add_to_columns)
            columns = list(columns.keys())
            columns.sort(key=column_sort_key)
        else:
            columns = self.columns

        for i in range(0, len(columns)):
            column_ix[columns[i]] = i
        for item in items:
            row = len(columns) * ['']
            add('', 1, item, add_to_row)
            table.append(row)

        return (columns, table)


class TSVList(Lister):
    def __init__(self, columns, obj_info, options):
        self.columns = columns
        self.obj_info = obj_info
        self.options = options

    def display_list(self, columns, table):
        head = "\t".join(columns)
        self.verbose(head)

        for row in table:
            line = "\t".join(row)
            print(line)


class LongList(Lister):
    def __init__(self, columns, obj_info, options):
        self.columns = columns
        self.obj_info = obj_info
        self.options = options

    def display_list(self, columns, table):
        sep = "\n" + "-" * 80 + "\n"
        max_width = 0
        for col in columns:
            max_width = max(max_width, len(col))
        fmt = "{0:>" + str(max_width) + "}: {1}"
        print(sep)
        for i in range(0, len(table)):
            for j in range(0, len(columns)):
                print(fmt.format(columns[j], table[i][j]))
            print(sep)


class TableList(Lister):
    def __init__(self, columns):
        self.columns = columns

    def display_list(self, columns, table):
        total = [columns]
        total.extend(table)
        self.ascii_table(total)

    def ascii_table(self, rows):
        col_widths = [0] * len(rows[0])
        for i in range(0, len(rows[0])):
            for j in range(0, len(rows)):
                col_widths[i] = max(col_widths[i], len(rows[j][i]))
        self.ascii_bar(col_widths)
        self.ascii_row(col_widths, rows[0], "^")
        self.ascii_bar(col_widths)
        for row in rows[1:]:
            self.ascii_row(col_widths, row, "<")
        self.ascii_bar(col_widths)

    def ascii_row(self, col_widths, row, align):
        txt = "|"
        for i in range(0, len(col_widths)):
            fmt = " {0:" + align + str(col_widths[i]) + "} "
            txt += fmt.format(row[i]) + "|"
        print(txt)

    def ascii_bar(self, col_widths):
        txt = "+"
        for w in col_widths:
            txt += ("-" * (w + 2)) + "+"
        print(txt)


class KeyValueList(Lister):
    def __init__(self, columns, obj_info, options):
        self.columns = columns
        self.obj_info = obj_info
        self.options = options

    def display_list(self, columns, table):
        for i in range(0, len(table)):
            row = []
            for j in range(0, len(columns)):
                row.append("{0}=\"{1}\"".format(columns[j], table[i][j]))
            print(" ".join(row))


# TODO handle spaces etc in completable names
class BashList(Lister):
    def __init__(self, columns, obj_info, options):
        self.columns = columns
        self.obj_info = obj_info
        self.options = options

    def display_list(self, columns, table):
        ix = None
        for i in range(0, len(columns)):
            if columns[i] == 'name':
                ix = i
        if ix is not None:
            res = []
            for row in table:
                res.append(row[ix])
            print(" ".join(res))


FORMATS = {
    # Special cased
    'raw_json': None,
    # Ditto
    'pretty_json': None,
    'tsv': TSVList,
    'long': LongList,
    'table': TableList,
    'kvp': KeyValueList,
    'bash': BashList
}


def format_list(json_list, columns=[], format='pretty_json'):
    formatter = None
    if format == "raw_json":
        print(json_list)
        return
    elif format == "pretty_json":
        # enc = json.JSONEncoder(False, False, True, True, True, indent=2)
        enc = json.JSONEncoder(indent=2)
        print(enc.encode(json.loads(json_list)))
        return
    else:
        formatter = FORMATS[format]
    formatter_instance = formatter(columns)
    formatter_instance.display(json_list)
