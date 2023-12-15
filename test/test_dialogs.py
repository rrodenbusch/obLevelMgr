import pyautogui
import tkinter as tk
from datadialogs import *

   
def doAskString():
    """ Example usase for myDialog class """
    resp = myDialog.askstring(title='Hi', text='Hi')
    if resp:
        text.insert(tk.END, f"Got dialog response '{resp}'\n")
    else:
        text.insert(tk.END, "Cancelled\n")

        
def doEntryDialog():
    """ Example usase for myDialog class """
    data = [ [1, 2, 3, 4, 'str'], [5,6,7,'str8',9], ]
    if myEntry.show(data=data, editcols=[2,], cnf={ 'bd':1, 'relief':'flat', 'bg':'#D3B683', }):
        newData = myEntry.data
        text.insert(tk.END, f"After edit: '{newData}'\n")
    else:
        text.insert(tk.END, f"Entry Dialog cancelled\n")


def main():
    """ Example usage for myDialog class """
    global myDialog
    global myEntry
    global text
    top = tk.Tk()
    top.geometry("400x400")
    mousepos = pyautogui.position()
    top.wm_geometry(f'+{mousepos[0]}+{mousepos[1]}')
    top.title('test LocalDialog')
    myDialog = LocalDialog(top)
    myEntry  = LocalEntryDialog(top,cnf={'bg':'#D3B683'})
    button1 = tk.Button(top, text='Ask String', command=doAskString)
    button1.grid(row=0, column=0, sticky='e')
    button2 = tk.Button(top, text='Entry Dialog', command=doEntryDialog)
    button2.grid(row=0, column=1, sticky='w')
    text = tk.Text(top)
    text.grid(row=1, column=0, columnspan = 2, sticky='nsew')
    top.rowconfigure(1, weight=1)
    top.columnconfigure(0, weight=1)
    top.columnconfigure(1, weight=1)
    top.mainloop()


if __name__ == "__main__":
    main()
