#!/usr/bin/env python


# Functions
# ------------------------------------------------
def table_string(body, header=None, index_name=None,
                 header_prefix=None, alignment=">"):
    """
    Returns a string that contains a well formated table.
        
    body        | list | list that contains the rows
    header      | list | list that contains the column names
    index_name  | str  | The name of the first column,
                |      | contains the row number.
    head_prefix | str  | Inserted before the header column
    alignment   | str  | "<"|"^"|">"
    """    
    # Some constants
    row_count = len(body)
    
    if body:
        col_count = len(body[0])
    elif header is not None:
        col_count = len(header)
    else:
        col_count = 0    
    
    body = [[str(col) for col in row] for row in body]
    if not header is None:
        header = [str(col) for col in header]
    
    # Get the widths of the columns
    widths = [0 for i in range(col_count)]
    
    # Body
    for row_index, row in enumerate(body):
        for col_index, col in enumerate(row):
            widths[col_index] = max(widths[col_index], len(col))
            
    # header
    if not header is None:
        for col_index, col in enumerate(header):
            widths[col_index] = max(widths[col_index], len(col))

    # First column
    if not index_name is None:
        width_index_col = max(len(index_name), len(str(row_count)))
        widths.insert(0, width_index_col)
        
    if widths and header_prefix is not None:
        widths[0] += len(header_prefix)

    # Extend the width of each column
    widths = [width + 2 for width in widths]

    # --
    # Create the formatters and spacers
    format_body = ["{{:{0}{1}}}".format(alignment, width) for width in widths]
    format_body = "|".join(format_body) 

    # Undo the widths change because of
    # the head_prefix
    if header_prefix is not None:
        widths[0] -= len(header_prefix)
        
    if header is not None:
        format_head = ["{{:{0}{1}}}".format(alignment, width) for width in widths]
        format_head = "|".join(format_head)
        
    spacer = ["-" * width for width in widths]
    if header_prefix is not None:
        spacer = header_prefix + "+".join(spacer)
    else:
        spacer = "+".join(spacer)
        
    # --
    # Print the table
    table = list()
    
    # header
    if header is not None:
        temp = header_prefix if not header_prefix is None else ""        
        if index_name is not None:
            temp += format_head.format(index_name, *header)
        else:
            temp += format_head.format(*header)            
        table.append(temp)
        table.append(spacer)

    # Body
    if index_name is not None:
        for row_index, row in enumerate(body):
            temp = format_body.format(row_index, *row)
            table.append(temp)
        
    else:
        for row_index, row in enumerate(body):
            temp = format_body.format(*row)
            table.append(temp)
            
    table = "\n".join(table)
    return table

def print_table(*args, **kargs):
    """
    Uses the same arguments as table_string.
    """
    temp = table_string(*args,**kargs)
    print(temp)
    return None
