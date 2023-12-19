# A set of classes to manage tkinter frames containing data
#
# (C) Copyright Richard Rodenbusch 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=bad-docstring-quotes,invalid-name
import tkinter as tk
from tkinter import messagebox

import pandastable as pt


def _getShape(shape=(1, 1), data=None):
    if data is None:
        return shape
    elif  hasattr(data, 'shape'):  # get the shape from the data list
        shape = data.shape()
    elif len(data) > 0:  # compute the shape of the list
        if isinstance(data[0], (list, tuple)):
            shape = (len(data), len(data[0]))
        else:
            shape = (len(data), 0)
    return(shape)


def _getValue(*args, **kw):
    """ Return a default value if the row,col entry does not exist in the data
    
    Args:
       data (list) : Data set to be searched
       row (int)   : Row of data to be searched
       col (int)   : Col of data to be searched (if 2D data set)
       default     : Default value to be returned if data requested not in data set
                   default = None
    
    Exceptions:
        Suppresses IndexError and returns default data value
        
    Returns:
        data[row][col] or default
    """
    if args and len(args) == 1:
        (row, col, data) = (kw.get('row'), kw.get('col', kw.get('column')), args[0])
    else:
        (row, col, data) = (kw.get('row'), kw.get('col', kw.get('column')), kw.get('data'))
            
    if isinstance(data, (list, tuple)) and (row is not None or col is not None):
        try:
            if row is None:
                return data[col]
            elif col is None:
                return data[row]
            else:
                return data[row][col]
        except IndexError:
            return kw.get('default')                        
    else:
        return kw.get('default')     

        
def _place_window(w, parent=None):
    """ Based on the tkinter.filedialog module
        useful to place a window at center of the parent window
        Useful because tkinter.simpledialog doesn't center on the parent window
    """
    w.wm_withdraw()  # Remain invisible while we figure out the geometry
    w.update_idletasks()  # Actualize geometry information

    minwidth = w.winfo_reqwidth()
    minheight = w.winfo_reqheight()
    maxwidth = w.winfo_vrootwidth()
    maxheight = w.winfo_vrootheight()
    if parent is not None and parent.winfo_ismapped():
        x = parent.winfo_rootx() + (parent.winfo_width() - minwidth) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - minheight) // 2
        vrootx = w.winfo_vrootx()
        vrooty = w.winfo_vrooty()
        x = min(x, vrootx + maxwidth - minwidth)
        x = max(x, vrootx)
        y = min(y, vrooty + maxheight - minheight)
        y = max(y, vrooty)
        if w._windowingsystem == 'aqua':
            # Avoid the native menu bar which sits on top of everything.
            y = max(y, 22)
    else:
        x = (w.winfo_screenwidth() - minwidth) // 2
        y = (w.winfo_screenheight() - minheight) // 2

    w.wm_maxsize(maxwidth, maxheight)
    w.wm_geometry('+%d+%d' % (x, y))
    w.wm_deiconify()  # Become visible at the desired location


class SideBySideDialog():
    """Create a side by list management dialog
    
    Move items between the left list and right list

    Args:
        parent (tkinter.Tk) : Optional parent window
        right (left) : Optional list of items to populate left hand side. Default=[]
        left (list) : Optional list of items to populate right hand side. Default=[]
        maxright (int) : Maximum number of items allowed in the right hand list.  Default=0 implies no limit
        cnf (dict) : A dictionary containing configuration for the modal window

    Examples:
        def sideByside():
            items = [x for x in range(21)] 
            popup.show(left=items, right=[], maxright=3)
            label.configure(text=f'Left: {len(popup.left)} items {popup.left}')
            label2.configure(text=f'\nRight: {len(popup.right)} items {popup.right}')
            label.grid(row=0, column=0, sticky='w', pady=3)
            label2.grid(row=1, column=0, sticky='w', pady=3)
        
        
        if __name__ == "__main__":
            root = tk.Tk()
            root.geometry("600x200") 
            label = tk.Label(root, text='Left:')
            label2 = tk.Label(root, text='Right:')
            label.grid(row=0, column=0, sticky='w', pady=3)
            label2.grid(row=1, column=0, sticky='w', pady=3)
            popup = SideBySideList(root)
            button = tk.Button(root, text='sideByside', command=sideByside)
            button.grid(row=2, column=0, pady=3, padx=10)
            root.mainloop()
    
    """

    def __init__(self, parent=None, right:list=[], left:list=[], maxright:int=0, cnf:dict={}):
        self.parent = parent
        self._right = right
        self._left = left
        self._cnf = cnf
        self._maxright = maxright
        self._popup = None
        self._rightlist = None
        self._leftlist = None
        return
                
    def _moveright(self, *args):  # Include *args to allow use as double click event handler
        selected_checkboxs = self._leftlist.curselection() 
        
        for selected_checkbox in selected_checkboxs[::-1]: 
            self._rightlist.insert(tk.END, self._leftlist.get(selected_checkbox))
            self._leftlist.delete(selected_checkbox)
        self._setup_buttons()

    def _moveleft(self, *args):  # Include *args to allow use as double click event handler
        selected_checkboxs = self._rightlist.curselection() 
        
        for selected_checkbox in selected_checkboxs[::-1]: 
            self._leftlist.insert(tk.END, self._rightlist.get(selected_checkbox))
            self._rightlist.delete(selected_checkbox)
        self._setup_buttons()

    def _setuplists(self):
        for item in self._right: 
            self._rightlist.insert(tk.END, item) 
        for item in self._left: 
            self._leftlist.insert(tk.END, item)
        self._setup_buttons()
        
    def _buildform(self):
        if self._popup is None:
            self._popup = tk.Toplevel(self.parent, cnf=self._cnf)
            self._moverightbutton = tk.Button(self._popup, text=">>>", command=self._moveright)
            self._moverightbutton.grid(row=0, column=1, sticky='s',)
            self._moveleftbutton = tk.Button(self._popup, text="<<<", command=self._moveleft)
            self._moveleftbutton.grid(row=1, column=1, sticky='n',) 
            self._savebutton = tk.Button(self._popup, text='Save', command=self._save)
            self._cancelbutton = tk.Button(self._popup, text='Cancel', command=self._cancel)
            self._savebutton.grid(row=2, column=0)
            self._cancelbutton.grid(row=2, column=2)
            self._rightlist = tk.Listbox(self._popup, selectmode=tk.SINGLE) 
            self._rightlist.grid(row=0, column=2, rowspan=2, sticky='nsew') 
            self._leftlist = tk.Listbox(self._popup, selectmode=tk.SINGLE)
            self._leftlist.grid(row=0, column=0, rowspan=2, sticky='nsew')
            self._setuplists()
 
            self._popup.columnconfigure(0, weight=1,)
            self._popup.columnconfigure(2, weight=1,)
            self._popup.rowconfigure(0, weight=1)
            self._popup.rowconfigure(1, weight=1)
            
            self._popup.protocol("WM_DELETE_WINDOW", self._cancel)
            self._popup.takefocus = True
            self._popup.grab_set()
            _place_window(self._popup, self.parent)
        return self._popup

    def _setup_buttons(self):
        if self._rightlist.size() > 0:
            self._moveleftbutton['state'] = tk.NORMAL
            self._rightlist.bind('<Double-1>', self._moveleft)
        else:
            self._moveleftbutton['state'] = tk.DISABLED
            self._rightlist.unbind('<Double-1>')
        if self._maxright > 0 and self._rightlist.size() >= self._maxright:
            self._moverightbutton['state'] = tk.DISABLED
            self._leftlist.unbind('<Double-1>')
        else:
            self._moverightbutton['state'] = tk.NORMAL
            self._leftlist.bind('<Double-1>', self._moveright)

    @property
    def right(self):
        """ List of items from the right side """
        return self._right
    
    @right.setter
    def right(self, rightlist:list):
        self._right = rightlight
    
    @property
    def left(self):
        """ List of item from the left side list """
        return self._left

    @left.setter
    def left(self, leftlist:list):
        self._left = leftlist
        
    @property
    def maxright(self):
        return self._maxright

    @maxright.setter
    def maxright(self, maxright:int):
        self._maxright = maxright
        
    def _save(self):
        if self._rightlist is not None:
            self._right = self._rightlist.get(0, tk.END)
        if self._leftlist is not None:
            self._left = self._leftlist.get(0, tk.END)
        self._popup.destroy()
        self._popup = None
        self._resp = True

    def _cancel(self):
        if messagebox.askokcancel('Cancel', 'Cancel?'):
            self._popup.destroy()
            self._popup = None
            self._resp = False

    def show(self, right=None, left=None, maxright=None):
        """Display the lists side by side for selection.

        Args:
            right: The instructions to add to the circuit.
            qubits: Any qubits to add to the circuit. This argument can be used,
                for example, to enforce a particular ordering of qubits.
            clbits: Any classical bits to add to the circuit. This argument can be used,
                for example, to enforce a particular ordering of classical bits.
            name: The name of the circuit.
            global_phase: The global phase of the circuit in radians.
            metadata: Arbitrary key value metadata to associate with the circuit.
            
            Args:
                right (list) : Optional list for right hand side
                left (list) : Optional list for left hand side
                maxright (int) : Optional max number of selections on right side
                                0 indicates no maximum on right side
                                
        Returns:
            Boolean : True if OK, False if Cancel
        """
        if right is not None: self._right = right
        if left is not None: self._left = left
        if maxright is not None: self._maxright = maxright
        if self._popup is None:
            self._popup = self._buildform()
        else:
            self._setuplists()
        if self._popup.state() in [ 'withdrawn', 'iconic' ]: self._popup.deiconify()
        self.parent.wait_window(self._popup)
        return self._resp


def askSideBySideLists(**kw):
    popup = SideBySideDialog()
    response = popup.show(kw)
    if response:
        return (popup.right, popup.left)
    return None
    

class LocalDialog():
    """ Simple, controllable dialog box for data entry
    
    Simple data entry dialog
    
    Args:
        parent (tkinter.Tk) : Optional parent window

    Examples:
        myDialog = LocalDialog(parent)
        myString = myDialog.askstring(parent,'title','query',cnf={width:20})
        
    """

    def __init__(self, parent=None, **kw):
        self.parent = parent
        self._font = kw.get('font')
        self._dtype = kw.get('dtype', 'str')
        
    def _drawframe(self, title='LocalDialog', **kw):
        self._popup = tk.Toplevel(self.parent)
        self._popup.title(title)
        self._dtype = kw.get('dtype', self._dtype)
        width = kw.get('width', 40)
        self._entry = tk.Entry(self._popup, width=width,)
        if 'default' in kw:
            self._entry.insert(0, kw['default'])
        curRow = 0
        if 'text' in kw:
            label = tk.Label(self._popup, text=kw['text'], anchor='n')
            label.grid(row=0, column=0, columnspan=2, sticky='ew')
            curRow += 1        
        self._entry.grid(row=curRow, column=0, columnspan=2, sticky='ew')
        self._okButton = tk.Button(self._popup, text='OK', command=self._okPress)
        self._okButton.grid(row=curRow + 1, column=0, sticky='e', padx=5, pady=5)
        self._cancelButton = tk.Button(self._popup, text='Cancel', command=self._cancelPress)
        self._cancelButton.grid(row=curRow + 1, column=1, sticky='w', padx=5, pady=5)
        self._popup.rowconfigure(curRow, weight=1)
        self._popup.rowconfigure(curRow + 1, weight=0)
        self._popup.columnconfigure(0, weight=1)
        self._popup.columnconfigure(1, weight=1)
        self._popup.protocol("WM_DELETE_WINDOW", self._cancelPress)
        self._popup.takefocus = True
        self._popup.grab_set()
        _place_window(self._popup, self.parent)
        return self._popup
        
    def _okPress(self):
        _validator = {'integer':int, 'flaot': float, 'complex':complex}
        valid = _validator.get(self._dtype, str)
        try:
            if self._dtype == 'integer':
                self._resp = _validator['integer'](self._entry.get())
            elif self._dtype == 'float':
                self._resp = float(self._entry.get())
            else:
                self._resp = self._entry.get()
            self._popup.destroy()
        except ValueError as e:
            messagebox.showerror('ValueError', f'{self._entry.get()} is not {self._dtype}. Try Again')

    def _cancelPress(self):
        self._resp = None
        self._popup.destroy()
            
    def askinteger(self, title:str='Ask Integer', text:str='Enter Integer', **kw):
        """ Retrieve a string variable via dialog
    
        Args:
            title (str) : Title for the dialog
            text (str) : Prompt for the dialog
            values (list) : the new values to display in the row 
        """
        kw['width'] = kw.get('width', 10)
        ask = self._drawframe(title, text=text, **kw)
        self.parent.wait_window(ask)
        return self._resp

    def askstring(self, title:str='Ask String', text:str='Enter String', **kw):
        """ Retrieve a string variable via dialog
    
        Args:
            title (str) : Title for the dialog
            text (str) : Prompt for the dialog
            values (list) : the new values to display in the row 
        """
        kw['dtype'] = 'str'
        askString = self._drawframe(title, text=text, **kw)
        self.parent.wait_window(askString)
        return self._resp


def askstring(*args, **kw):
    kw['dtype'] = 'str'
    popup = LocalDialog(kw.get('parent'))
    return popup.askstring(*args, **kw)


def askinteger(*args, **kw):
    kw['dtype'] = 'integer'
    popup = LocalDialog(kw.get('parent'))
    return popup.askinteger(*args, **kw)

    
class LocalEntryFrame(tk.Frame): 
    """A frome to manage a grid of data, some of which are editable
    
    Display all data in a grid, making some editable

    Args:
        parent (tkinter.Tk) : Optional parent window
        cnf (dict)     : Optional configuration parameters for the frame
        data (list}    : Optional list containing the text to display in each grid
                           shape of the list will override the shape parameter given
        shape (tuple)  : Optional if data is None then (nrows, ncols) define the shape of grid; default = (1,1)
        editlist (list): Optional list indicating which columns are to be editable
        editrows (list): Optional indicating all of row is editable
        editcols (list): Optional variable indicate all of the given column is editable
        default (str)  : Default value for grids not found in data list
                           if default == '{row}{col}' then the field will get the row and column number
        rowbg (list)   : Optional list containing the background color for each row (default is 'white')
        anchor (str)   : Optional anchor for the labels in the grid; default = 'w'

    Examples:
    
        desccnf = skillcnf = { 'bd':1, 'relief':'flat', 'bg':'#D3B683'}
        rowbg = ['#C9C9C9' for x in range(5)]
        skilldesc = (21, 4)
        skillshape = (21, 1)
        attrshape = (7, 1)
        attrdesc = (7, 3)
        
        editFrame = LocalEntryFrame(parent, shape=skillshape, cnf=skillcnf, rowbg=rowbg)
        editFrame.grid(row=0, column=0, sticky='nsew')
    
    """

    def __init__(self, parent=None, cnf:dict={}, shape=(1, 1),
                 data:list=None, rowbg:list=[], anchor:str='w', widths=None, default=None, **kw):
        if parent is None: parent = tk.Tk()
        # self.master = parent
        tk.Frame.__init__(self, parent)
        self._editable = ('editable' in kw) or ('editcols' in kw) or ('editrows' in kw)
        self._font = kw.get('font')
        if self._editable:
            editable = kw.get('editable', [])
            editrows = kw.get('editrows', [])
            editcols = kw.get('editcols', [])
        if data is None:  # create data with shape given using default value
            if default == '{row}{col}': 
                data = [ [f'({row},{col})' for col in range(shape[1])] for row in range(shape[0])]
            elif default:
                data = [ [default for col in range(shape[1])] for row in range(shape[0])]
            else:
                data = [ [] ]
        self._data = data               
        self._shape = (nrows, ncols) = _getShape(shape=shape, data=data)
        self._fields = [[None for i in range(ncols)] for j in range(nrows)]
        self._cnf = cnf

        self.configure(cnf)
        for row in range(nrows):
            for col in range(ncols):
                width = _getValue(widths,col=col,default=None)
                if (self._editable and
                     ((row in editrows) or (col in editcols) or _getValue(editable, row=row, col=col, default=False))):
                    curValue = _getValue(data, row=row, col=col, default='')
                    if isinstance(curValue, str):
                        justify = 'left'
                    else:
                        justify = 'center'
                    self._fields[row][col] = tk.Entry(self, justify=justify, font=self._font,
                                                          bg=_getValue(rowbg, row=row, default='white'))
                    if width:
                        self._fields[row][col]['width'] = width
                        
                    self._fields[row][col].insert(0, _getValue(data, row=row, col=col, default=''))
                else: 
                    self._fields[row][col] = tk.Label(self, anchor=anchor, pady=1, font=self._font,
                                                      bg=_getValue(rowbg, row=row, default='white'),
                                                      text=_getValue(data, row=row, col=col, default=''))
                self._fields[row][col].grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
                self.grid(row=row, column=col, sticky='nsew')
        for row in range(nrows):
            self.rowconfigure(row, weight=1)
        for col in range(ncols):
            self.columnconfigure(col, weight=1)
    
    def _setField(self, row, col, value):
        # Handle fields which can be either tk.Label or tk.Entry
        field = self._fields[row][col]
        if isinstance(field, tk.Entry):
            field.delete(0, tk.END)
            field.insert(0, value)
        elif isinstance(field, tk.Label):
            field.configure(text=value)
        
    def update(self, **kw):
        """ Update the displayed data
    
        Args:
            row (int)     : the row to be updated
                            if not provided it is a full column update
            col (int)     : the column for the data items
                            if not provided it is a full row update
            data (list) : the new values to display in the row
                            if row = col = None, then replace the entire dataset
            default : the default value to use if values[row][col] does not exist
        
        Exceptions:
            Suppress IndexError if row, col are outside span of values and returns default
        """
        (row, col, data) = (kw.get('row'), kw.get('col', kw.get('column')), kw.get('data')) 
        if col is None and row is None:  # data set replacement
            self.data = data
        elif col is None:  # row replacement
            for col in range(len(data)):
                self._setField(row, col, _getValue(data, col=col))
        elif row is None:  # column replacement
            for row in range(len(data)):
                self._setField(row, col, _getValue(data, row=row))
        else:
            self._setField(row, col, data)

    @property
    def data(self):
        """ A list of the current data in the grid """
        if self._editable:
            data = []
            for row in range(self._shape[0]):
                curRow = []
                for col in range(self._shape[1]):
                    if isinstance(self._fields[row][col], tk.Entry):
                        curRow.append(self._fields[row][col].get())
                    else:
                        curRow.append(self._data[row][col])
                data.append(curRow)
            self._data = data
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        (nrows, ncols) = (len(self._fields), len(self._fields[0]))
        for row in nrows:
            for col in ncols:
                self._setField(row, col, _getValue(value, row=row, col=col, default=self._fields[row][col]))

    
class LocalEntryDialog(): 
    """ Simple, controllable dialog box for managing a LocalEntryFrame
    
    Grid based data entry dialog
    
    Args:
        parent (tkinter.Tk) : Optional parent window
        cnf (dict) : Optional configuration parameters for the frame
        shape (tuple) : Optional if data is None then (nrows, ncols) giving shape of grid; default = (1,1)
                        the row and column number will be displayed in the grid unless data is set
        data (list} : Optional list containing the text to display in each grid
                      shape of the list will override the shape parameter given
        editlist (list) : Optional list indicating which columns are to be editable
        rowbg (list) : Optional list containing the background color for each row (default is 'white')
        anchor (str) : Optional anchor for the labels in the grid; default = 'w'


    Examples:
        myDialog = LocalDialog(parent)
        if myDialog.show(parent,'title','query',cnf={width:20}):
            newData = myDialog.data
    """

    def __init__(self, parent=None, title='LocalEntry', **kw):
        self._title = title
        self.parent = parent
        self._cnf = kw.get('cnf', {})
        self._font = kw.get('font')
        self._response = None
        
    def _drawDialog(self, **kw):
        self._popup = tk.Toplevel(self.parent, **self._cnf)
        if 'title' in kw:
            self._popup.title(kw['title'])
            del kw['title']            
        elif self._title:
            self._popup.title(self._title)
        if 'parent' in kw:
            del kw['parent']
        font = kw.get('font',self._font)
        self._entryFrame = LocalEntryFrame(parent=self._popup, **kw)
        self._entryFrame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self._okButton = tk.Button(self._popup, text='Save', command=self._okPress, font=font)
        self._okButton.grid(row=1, column=0, sticky='e')
        self._cancButton = tk.Button(self._popup, text='Cancel', command=self._cancelPress, font=font)
        self._cancButton.grid(row=1, column=1, sticky='w')
        self._popup.rowconfigure(0, weight=1)
        self._popup.columnconfigure(0, weight=1)
        self._popup.columnconfigure(1, weight=1)        
        self._popup.protocol("WM_DELETE_WINDOW", self._cancelPress)
        self._popup.takefocus = True
        self._popup.grab_set()
        _place_window(self._popup, self.parent)
        return self._popup
         
    def _okPress(self):
        self._response = True
        self._data = self._entryFrame.data
        self._popup.destroy()
        self._popup = None
            
    def _cancelPress(self):
        if messagebox.askokcancel('Cancel Edit', 'Cancel edits?'):
            self._response = False
            self._popup.destroy()
            self._popup = None

    def update(self, **kw):
        return self._entryFrame.update(kw)
        
    @property
    def data(self):
        """ A list of text to display in the grid """
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = data
        self._entryFrame.data = value
    
    @property
    def resp(self):
        return self._response
    
    def show(self, **kw):
        """ Display the form with editable data as a modal form """
        if 'parent' in kw:
            del kw['parent']  # Can't change after creation
        self.parent.wait_window(self._drawDialog(**kw))
        return self._response

    
class LocalDataFrame(LocalEntryFrame):
    """A frome to manage a grid of text labels
    
    Display buttons in a grid 

    Args:
        parent (tkinter.Tk) : Optional parent window
        cnf (dict) : Optional configuration parameters for the frame
        shape (tuple) : Optional if data is None then (nrows, ncols) giving shape of grid; default = (1,1)
                        the row and column number will be displayed in the grid unless data is set
        data (list} : Optional list containing the text to display in each grid
                      shape of the list will override the shape parameter given
        rowbg (list) : Optional list containing the background color for each row (default is 'white')
        anchor (str) : Optional anchor for the labels in the grid; default = 'w'

    Examples:
    
        desccnf = skillcnf = { 'bd':1, 'relief':'flat', 'bg':'#D3B683'}
        rowbg = ['#C9C9C9' for x in range(5)]
        skilldesc = (21, 4)
        skillshape = (21, 1)
        attrshape = (7, 1)
        attrdesc = (7, 3)
        
        self._skills = LocalDataFrame(parent, shape=skillshape, cnf=skillcnf, rowbg=rowbg)
        self._skills.grid(row=0, column=0, sticky='nsew')
        
    """

    def __init__(self, parent, **kw):
        for key in ['editable', 'editcols', 'editrows']:
            if key in kw:
                del kw[key]
        super().__init__(parent, **kw)


class LocalTableFrame(tk.Frame):
    """Basic frame for a pandastable displaying a pandas.dataframe table
    
    Display items from the pandas dataset 

    Args:
        parent (tkinter.Tk) : Optional parent window
        dataframe (pd.DataFrame) : Optional dataframe to display
        title (str) : Title for window

    """

    def __init__(self, parent=None, dataframe=None, title='obTable'):
        self._popup = tk.Toplevel(parent)
        self._popup.geometry('600x400')
        self._popup.title(title)
        self.parent = parent
        f = tk.Frame(self._popup)
        f.pack(fill=tk.BOTH, expand=1)
        if dataframe is None:
            dataframe = pt.TableModel.getSampleData()          
        self._table = pt.Table(f, dataframe=dataframe,
                               showtoolbar=True, showstatusbar=True)
        # set some options
        self._table.textcolor = 'red' 
        self._popup.takefocus = True
        self._popup.grab_set()
        _place_window(self._popup, self.parents)
        self._table.show()
        return


class LocalButtonFrame(tk.Frame):
    """A frome to manage the increment attribute buttons
    
    Display buttons in a grid 

    Args:
        parent (tkinter.Tk) : Optional parent window
        cnf (dict) : Optional configuration parameters for the frame
        shape (tuple) : (nrows, ncols) giving shape of grid; default = (1,1)
        commands (list} : list containing the commands for each button in the grid
        labels (list) : list containing the text for each button in the grid
        rowbg (list) : list containing the background color for each row (default is 'white')

    Examples:
    
        commands = [[lambda: self._inc(0)], [lambda: self._inc(1)], [lambda: self._inc(2)], [lambda: self._inc(3)], [lambda: self._inc(4)],
                    [lambda: self._inc(5)], [lambda: self._inc(6)], [lambda: self._inc(7)], [lambda: self._inc(8)], [lambda: self._inc(9)],
                    [lambda: self._inc(10)], [lambda: self._inc(11)], [lambda: self._inc(12)], [lambda: self._inc(13)], [lambda: self._inc(14)],
                    [lambda: self._inc(15)], [lambda: self._inc(16)], [lambda: self._inc(17)], [lambda: self._inc(18)], [lambda: self._inc(19)],
                    [lambda: self._inc(20)], [lambda: self._inc(21)], ]
        self._buttons = LocalButtonFrame(parent, shape=skillshape, rowbg=rowbg,
                                      labels=[ ['Inc'] for y in range(skillshape[0])] ,
                                      commands=commands,)
        self._buttons.grid(row=0, column=1, sticky='nsew')
        
    """

    def __init__(self, parent=None, cnf=None, shape=(1, 1), commands:list=[], data=[], rowbg=[], font=None):
        if parent is None: parent = tk.Tk()
        self.master = parent
        self._buttons = [[None for i in range(shape[1])] for j in range(shape[0])]
        self._shape = (nrows, ncols) = shape
        self._font = font
        
        self._commands = commands
        self._rowbg = rowbg
        self._data = data

        tk.Frame.__init__(self)
        if cnf is not None: self.configure(cnf)
        for row in range(nrows):
            for col in range(ncols):
                self._buttons[row][col] = tk.Button(self, underline=row,
                                                    text=_getValue(self._data, row=row, col=col, default=''),
                                                    bg=_getValue(self._rowbg, row=row, default='white'),
                                                    command=_getValue(self._commands, row=row, col=col),
                                                    font=font)
                self._buttons[row][col].grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
                self.grid(row=row, column=col, sticky='nsew')
        for row in range(nrows):
            self.rowconfigure(row, weight=1)
        for col in range(ncols):
            self.columnconfigure(col, weight=0)
        
        return
    
    def _nocommand(self):
        messagebox.showwarning('No Command Set', 'No Button Command Set')

