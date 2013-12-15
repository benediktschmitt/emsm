#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


import sys
import io


__all__ = ["TablePrinter", "PrettyTablePrinter"]


class TablePrinter(object):
    """
    Prints a table pretty.
    """

    def __init__(self,
                 colname_row_index=None,
                 alignment = ">"):
        self.colname_row_index = colname_row_index        
        self.alignment = alignment
        
        # Attributes of the currently printed table.
        # Listed in the order of their initialisation.
        # self._update_col_count() sets self._col_count,
        # self._update_col_widths() sets self._col_widths and so on.
        self._head = None
        self._body = None
        
        self._col_count = None
        self._col_widths = None

        self._row_format = None
        self._row_delimiter = None
        self._section_delimieter = None

    def _update_col_count(self):
        """
        Returns the columns in the table.
        """
        head_count = len(self._head) if self._head else 0
        body_count = len(self._body[0]) if self._body else 0

        if head_count == 0:
            self._col_count = body_count
        elif body_count == 0 or head_count == body_count:
            self._col_count = head_count
        else:
            raise ValueError("The number of columns in head is not equal "\
                             "to the number of columns in the body!")        
    def _update_col_widths(self):
        """
        Fetches the widths of the strings in the columnds.
        """
        widths = [0]*self._col_count

        if self._body is not None:
            for row in self._body:
                for col_index, col in enumerate(row):
                    if widths[col_index] < len(str(col)):
                        widths[col_index] = len(str(col))

        if self._head is not None:
            for col_index, col in enumerate(self._head):
                if widths[col_index] < len(str(col)):
                    widths[col_index] = len(str(col))

        if self.colname_row_index is not None:
            widths.insert(0, len(self.colname_row_index))

        self._col_widths = widths

    def _update_row_format(self):
        """
        Returns a string that can be formatted with *str.format()*.
        """
        temp = ["{{:{0}{1}}}".format(self.alignment, width) \
                for width in self._col_widths]
        temp = "  ".join(temp) + "\n"
        self._row_format = temp

    def _update_row_delimiter(self):
        """
        Returns a string that is printed between each row.
        """
        self._row_delimiter = ""
        
    def _update_section_delimiter(self):
        """
        Returns a string that is printed between head and body, and
        at the beginning and the end of the table.
        """
        self._section_delimiter = ""

    def print(self, body, head=None, file=sys.stdout):
        """
        >>> tableprinter.pprint(body=[[10,11,12], [20,21,22]], head=["a", "b", "c"])
         a   b   c
        10  11  12
        20  21  22    
        """
        self._body = body
        self._head = head

        # Update the meta values:
        self._update_col_count()
        self._update_col_widths()
        
        self._update_row_format()
        self._update_row_delimiter()
        self._update_section_delimiter()

        # Print the table:        
        file.write(self._section_delimiter)
        
        if self._head is not None:
            if self.colname_row_index:
                formatted_row = self._row_format.format(
                    self.colname_row_index, *self._head)
            else:   
                formatted_row = self._row_format.format(*self._head)
            file.write(formatted_row)

        if self._head is not None and self._body is not None:
            file.write(self._section_delimiter)

        if self._body is not None:
            last_row_index = len(self._body) - 1

            for row_index, row in enumerate(self._body):
                # XXX Slow for big tables. Perhaps, I'll put this case outside
                # of the loop.
                if self.colname_row_index:
                    formatted_row = self._row_format.format(row_index, *row)
                else:
                    formatted_row = self._row_format.format(*row)
                file.write(formatted_row)                    
                if row_index != last_row_index:
                    file.write(self._row_delimiter)

        file.write(self._section_delimiter)
        return None

    def to_string(self, body, head=None):
        string_io = io.StringIO()
        self.print(body, head, string_io)
        return string_io.getvalue()


class PrettyTablePrinter(TablePrinter):
    """
    >>> tableprinter.pprint(body=[[10,11,12], [20,21,22]], head=["a", "b", "c"])
    +====+====+====+
    |  a |  b |  c |
    +====+====+====+
    | 10 | 11 | 12 |
    +----+----+----+
    | 20 | 21 | 22 |
    +====+====+====+  
    """

    def _update_row_format(self):
        """
        Returns a string that can be formatted with *str.format()*.
        """
        temp = [" {{:{0}{1}}} ".format(self.alignment, width) \
                for width in self._col_widths]
        temp = "|" + "|".join(temp) + "|\n"
        self._row_format = temp

    def _update_row_delimiter(self):
        """
        Returns a string that is printed between each row.
        """
        temp = ["-"*(width + 2) for width in self._col_widths]
        temp = "+" + "+".join(temp) + "+\n"
        self._row_delimiter = temp
        
    def _update_section_delimiter(self):
        """
        Returns a string that is printed between head and body, and
        at the beginning and the end of the table.
        """
        temp = ["="*(width + 2) for width in self._col_widths]
        temp = "+" + "+".join(temp) + "+\n"
        self._section_delimiter = temp
        

if __name__=="__main__":
    c = 5
    r = 10
    myhead = ["x^{}".format(i) for i in range(c)]
    mybody = [[k**i for i in range(c)] for k in range(r)]

    myhead = ["section", "address", "value", "description"]
    mybody = [["program", "0", "INC 0", "Increments the value in the data register 0."],
              ["program", "1", "INC 0", "Increments the value in the data register 0."],
              ["program", "2", "INC 0", "Increments the value in the data register 0."],
              ["program", "3", "INC 0", "Increments the value in the data register 0."],
              ["program", "4", "DEC 0", "Decrements the value in the data register 0."],
              ["program", "5", "DEC 0", "Decrements the value in the data register 0."],
              ["delimiter", "6", "0", "Register with the value 0. Marks the end of the program."],
              ["data", "7", "anumber", "The data address 1."]
              ]

    printer = PrettyTablePrinter("Nr.")
    printer.print(mybody)
