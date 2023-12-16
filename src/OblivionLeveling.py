#!/usr/bin/env python3
# A simple utility to help manage Elder Scrolls Oblivion Leveling
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
import os
import sqlite3

import pyautogui
import argparse
import logging
import pandas as pd
import tkinter as tk

from tkinter import messagebox, filedialog as fd
import datadialogs
from datadialogs import (LocalDataFrame,
                         LocalButtonFrame,
                         LocalTableFrame,
                         SideBySideDialog,
                         LocalEntryFrame,)


def get_args():
    """ Parse and return command line arguments
    
    Args:
        None
        
    Returns:
        A dictionary containing the parsed command line arguments
    """
    clArgs = [['-d', '--database', {'help':'sqlite3 database name [oblevels.db]'}],
              ['-n', '--new', {'help':'create a new database', 'action':'store_true'}],
              ['-l', '--list', {'help':'list existing tables', 'action':'store_true'}],
              ['-v', '--verbose', {'help': 'INFO level logging', 'action':'store_true'}],
              ]

    parser = argparse.ArgumentParser(
                    prog='oblevel',
                    description='Manage Oblivion Leveling',
                    epilog='For Efficient Leveling')
    for cur_arg in clArgs:
        parser.add_argument(cur_arg[0], cur_arg[1], **cur_arg[2])
    args = parser.parse_args()
    logger.debug(args)
    return args


class rootWindow(tk.Frame):
    """ Application Window to manage Leveling
    
    Manage the complicate oblivion leveling rules
    
    Args:
        parent (tkinter.Tk) : Optional parent window
        title (str) : Optional title string for the window; default='obTable'

    Returns:
        tk.Frame cover the parent Window
    """

    def __init__(self, parent=None, title='obTable', dbname=None, cnf={}):
        self._skillmapdf = None
        self._skillsmap = None
        self._curLevel = None
        self._dbName = None
        self._selectList = None
        self._dirty = [ 0 ]
        self._filetypes = (('DB files', '*.db'), ('All files', '*.*'))
        self._incCommands = [[lambda: self._inc(0)], [lambda: self._inc(1)], [lambda: self._inc(2)], [lambda: self._inc(3)], [lambda: self._inc(4)],
            [lambda: self._inc(5)], [lambda: self._inc(6)], [lambda: self._inc(7)], [lambda: self._inc(8)], [lambda: self._inc(9)],
            [lambda: self._inc(10)], [lambda: self._inc(11)], [lambda: self._inc(12)], [lambda: self._inc(13)], [lambda: self._inc(14)],
            [lambda: self._inc(15)], [lambda: self._inc(16)], [lambda: self._inc(17)], [lambda: self._inc(18)], [lambda: self._inc(19)],
            [lambda: self._inc(20)], ]

        if parent is None: parent = tk.Tk()
        self.parent = parent
        tk.Frame.__init__(self)
        self.main = self.master
        
        # Place the window at the current mouse position, supports multiple monitors best
        self.main.geometry('1080x820')
        mousepos = pyautogui.position()
        self.main.wm_geometry(f'+{mousepos[0]}+{mousepos[1]}')
        self.main.title(title)
        self.main['bg'] = '#D3B683'
        self.font = tk.font.nametofont("TkDefaultFont").actual()
        self.main.protocol("WM_DELETE_WINDOW", self._quit)
        self._setDB(dbname)
        self._setupMenu()
        self._drawFrame()
        
    def _drawFrame(self):
        if self._dbName is not None and os.path.isfile(self._dbName):
            # Some colors and default configurations
            desccnf = skillcnf = { 'bd':1, 'relief':'flat', 'bg':'#D3B683', }

            skilldesc = (21, 4)
            skillshape = (21, 1)
            attrshape = (7, 1)
            attrdesc = (7, 3)
            
            if len(self._majorList) > 0:
                rowbg = ['#C9C9C9' for x in range(len(self._majorList))]
            else:
                rowbg = []
            
            self._header1 = tk.Frame(self.parent, bg=skillcnf['bg'])
            self._header1.grid(row=0, column=0, sticky='nsew')
            label1 = tk.Label(self._header1, text='Value', padx=1, pady=1, bg=skillcnf['bg'])
            label1.grid(row=0, column=0, sticky='nsew')            
            label2 = tk.Label(self._header1, text='Increase', padx=1, pady=1, bg=skillcnf['bg'])
            label2.grid(row=0, column=1, sticky='nsew')
            self._header2 = tk.Label(self.parent, font=self.font,
                                     text=f'       {self._levelUp*10}% to Next Level    -----   Current Level {self._curLevel} ', bg=skillcnf['bg'], anchor='w')
            self._header2.grid(row=0, column=1, columnspan=2, sticky='nsew')
            
            self._skills = LocalDataFrame(self.parent, data=self._stats, shape=skillshape, cnf=skillcnf, rowbg=rowbg, anchor='n')
            self._skills.grid(row=1, column=0, sticky='nsew')
             
            self._buttons = LocalButtonFrame(self.parent, shape=skillshape, rowbg=rowbg,
                                          data=[ ['Inc'] for y in range(skillshape[0])] ,
                                          commands=self._incCommands,)
            self._buttons.grid(row=1, column=1, sticky='nsew')
            
            self._desc = LocalEntryFrame(self.parent, data=self._skilldesclist, cnf=desccnf, rowbg=rowbg,)
            self._desc.grid(row=1, column=2, sticky='nsew')
            
            self._attrs = LocalDataFrame(self.parent, shape=attrshape, cnf=skillcnf, data=self._attrSums, anchor='n',)
            self._attrs.grid(row=2, column=0, sticky='nsew', pady=10, ipady=2)
            
            self._attrdesc = LocalDataFrame(self.parent, shape=attrdesc, cnf=desccnf, data=self._attrdesclist)
            self._attrdesc.grid(row=2, column=2, sticky='nsew', pady=10,)
            
            self.parent.rowconfigure(1, weight=10)
            self.parent.rowconfigure(2, weight=1)

            self.parent.columnconfigure(0, weight=0)
            self.parent.columnconfigure(1, weight=0)
            self.parent.columnconfigure(2, weight=1)
        else:
            self._header = None
            self._skills = None
            self._buttons = None
            self._skilldesclist = None
            self._desc = None
            self._attrs = None
            self._attrdesclist = None
            self._attrdesc = None
        # self._checkMenu()
        return
    
    def _refreshData(self):
        if messagebox.askokcancel('Refresh Data', 'OK to refresh all data from database?'):
            self._drawFrame()
            
    def _initDataSets(self):
        self._sqls = {'skilldesc': 'select Skill, Attr, Skilldesc from skillMap order by MajorSkill Desc, Skill Asc',
              'skillkey': 'select ROWID, MajorSkill, underline from skillMap order by MajorSkill Desc, Skill Asc',
              'stats': 'select CurValue, Increase from statsMap where level = ? order by MajorSkill Desc, Skill Asc',
              'attrdesc': 'select name, desc  from obAttributes order by name Asc',
              'underlines': 'select name, underline from skillMap order by MajorSkill Desc, Skill Asc',
              'attrkey': 'select ROWID from obAttributes order by name Asc',
              'statskey': 'select ROWID from statsMap where level = ? order by MajorSkill Desc, Skill Asc',
              'attrsum': f'select sum(CurValue) as CurValue, sum(Increase) as Increase from statsMap where level = ? '
                         f'group by Attr order by Attr asc'
              }
        if self._dbName is None: return
    
        keymap = self._getDataList('select skill, attr from skillMap',)
        self._skill2attr = {}
        for row in keymap:
            self._skill2attr[row[0]] = row[1]

        keymap = self._getDataList('select ROWID, name from obAttributes')
        self._attr2key = {}
        self._key2attr = {}
        for row in keymap:
            self._key2attr[row[0]] = row[1]
            self._attr2key[row[1]] = row[0]
        
        keymap = self._getDataList('select ROWID, name from obSkills')
        self._dirty = [ 0 for x in range(len(keymap))]
        self._skill2key = {}
        self._key2skill = {}
        for row in keymap:
            self._key2skill[row[0]] = row[1]
            self._skill2key[row[1]] = row[0]
            
        self._skilldesclist = self._getDataList(self._sqls['skilldesc'])
        self._attrdesclist = self._getDataList(self._sqls['attrdesc'])

        keymap = self._getDataList(self._sqls['skillkey'])
        self._skillKey2Row = [ [] for x in range(len(keymap)) ]
        self._row2SkillKey = [ [] for x in range(len(keymap)) ]
        self._minorList = []
        self._majorList = []
        self._row2Underline = []
        for i in range(len(keymap)):
            self._row2Underline.append(keymap[i][2])
            key = keymap[i][0]
            self._skillKey2Row[key] = i
            self._row2SkillKey[i] = key
            if keymap[i][1]:
                self._majorList.append(self._key2skill[key])
            else:
                self._minorList.append(self._key2skill[key])
        self._majorSkillCnt = len(self._majorList)
                        
        keymap = self._getDataList(self._sqls['attrkey'])
        self._attr2row = [  [] for x in range(len(keymap)) ]
        self._row2attr = [ [] for x in range(len(keymap)) ]
        rowcnt = 0
        for row in keymap:
            self._attr2row[row[0]] = rowcnt
            self._row2attr[rowcnt] = row[0]
            rowcnt += 1

        if self._curLevel is None:
            levels = self._getDataList('select max(level) from obStats')
            self._curLevel = levels[0][0]
        
        self._stats = self._getDataList(self._sqls['stats'], (self._curLevel,))
        self._levelUp = sum([x[1] for x in self._stats[:self._majorSkillCnt]])
        keymap = self._getDataList(self._sqls['statskey'], (self._curLevel,))
        self._stats2row = {}
        self._row2StatsKey = [[] for x in range(len(keymap))]
        rowcnt = 0
        for row in keymap:
            self._stats2row[row[0]] = rowcnt
            self._row2StatsKey[rowcnt] = row[0]
            rowcnt += 1

        self._attrSums = self._getDataList(self._sqls['attrsum'], (self._curLevel,))
        if self._curLevel is None: self._curLevel = 0
            
    def _inc(self, x):
        """ Increment the value of skill in row x """
        key = self._row2SkillKey[x]
        skill = self._key2skill[key]
        attrkey = self._attr2key[ self._skill2attr[skill] ]
        (curvalue, increase) = self._stats[x]
        if messagebox.askyesno('Increase Skill', f'Increment {skill}?'):
            self._stats[x] = (self._stats[x][0] + 1, self._stats[x][1] + 1)
            self._skills.update(row=x, data=(self._stats[x]))
            self._attrSums[attrkey] = (self._attrSums[attrkey][0] + 1, self._attrSums[attrkey][1] + 1)
            self._attrs.update(row=attrkey, data=self._attrSums[attrkey])
            self._dirty[x] = 1
            if x < self._majorSkillCnt:
                self._levelUp += 1
            
        self._checkMenu()
        
    def _getDataList(self, sql, params=None):
        if self._dbName is not None and os.path.isfile(self._dbName): 
            try:
                with sqlite3.connect(self._dbName) as conn:
                    if params is not None:
                        cursor = conn.execute(sql, params)
                    else:
                        cursor = conn.execute(sql)
                    datalist = cursor.fetchall()
                return datalist
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Error in {sql}\n{str(e)}')

    def _getDataFrame(self, sql):
        try:
            with sqlite3.connect(self._dbName) as conn:
                df = pd.read_sql(sql, conn)
            return df
        except sqlite3.Error as e:
            messagebox.showerror('SQL error', f'Error in {sql}\n{str(e)}')

    def _doNothing(self):
       messagebox.showwarning('rootWindow', 'Do Nothing Button Pressed')
    
    def _setDB(self, filename):
        self._validDB = (self._dbName != filename) and (filename is not None and os.path.isfile(filename))
        if self._validDB:
            (fpath, fname) = os.path.split(filename)
            self._dbName = filename
            self.parent.title(f'Oblivion Levels {fname}')
            self._initDataSets()
            self._drawFrame()
            self._fillIncMenu()
        
    def _openDB(self, *args):
        filename = fd.askopenfilename(parent=self.parent, title='Open Database', filetypes=self._filetypes)
        if filename and len(filename):
            if os.path.isfile(filename):
                (fpath, fname) = os.path.split(filename)
                self._setDB(filename)
            else:
                messagebox.showerror(title='Open File', message=f'{filename} does not exist')
        self._checkMenu()

    def _saveMajorList(self):
        if messagebox.askyesno('Save', 'Commit Major Skill Changes?'):
            if sum(self._dirty) > 0:
                self._saveDB()
            try:
                with sqlite3.connect(self._dbName) as conn:
                    for skill in self._minorList:
                        conn.execute("update obSkills set major = 0 where ROWID = ?", (self._skill2key[skill],))
                    for skill in self._majorList:
                        conn.execute("update obSkills set major = 1 where ROWID = ?", (self._skill2key[skill],))
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Update on skill {skill} @ rowid {self._skill2key[skill]}\n'
                                     f' failed with message\n{str(e)}')
            self._drawFrame()
        
    def _insertLevel(self, level):
        levels = []
        try:
            with sqlite3.connect(self._dbName) as conn:
                for rowid, skill in self._key2skill.items():
                    conn.execute('insert into obStats (SKILLID, level, curvalue, prevalue) VALUES (?,?,0,0)', (rowid, level,))
                    levels.append([skill, 0, ])
            return levels
        except sqlite3.Error as e:
            messagebox.showerror('SQL error', f'Insert {skill} @ level {level}\n'
                                 f' failed with message\n{str(e)}')
                
    def _getLevel(self, level, create=True):
        try:
            with sqlite3.connect(self._dbName) as conn:
                cursor = conn.execute('select skill, curValue from statsMap where level = ?', (level,))
                levels = cursor.fetchall()
                if create and len(levels) < 21:
                    levels = self._insertLevel(level)
            return levels
        
        except sqlite3.Error as e:
            messagebox.showerror('SQL error', f'Get Level {level}\n'
                                 f' failed with message\n{str(e)}')
            
    def _setLevel(self):
        level = datadialogs.askinteger('Select Level', 'Enter level number.', parent=self.parent,
                                       default=self._curLevel)
        if level is not None:
            try:
                with sqlite3.connect(self._dbName) as conn:
                    cursor = conn.execute('select skill, curValue from statsMap where level = ?', (level,))
                    levels = cursor.fetchall()
                    if len(levels) == 21:
                        self._curLevel = level
                        self._drawFrame()
                    else:
                        messagebox.showerror('Level Not Found', f'Level {level} not found.')
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Set Level {level}\n'
                                     f' failed with message\n{str(e)}')
        
    def _editLevel(self):
        level = datadialogs.askinteger('Level to Edit', 'Enter the Level to Edit', parent=self.parent,
                                       default=self._curLevel)
        if level is not None:
            if self._dirty:
                if messagebox.askyesno('Save Changes', 'Save Changes? Unsaved changes will be lost.'):
                    self._saveDB(force=True)
            levels = self._getLevel(level)          
            myEntry = datadialogs.LocalEntryDialog(self.parent, cnf={'bg':'#D3B683'})
            if myEntry.show(data=levels, editcols=[1, 2, ], cnf={ 'bd':1, 'relief':'flat', 'bg':'#D3B683', }):
                try:
                    newStats = myEntry.data
                    with sqlite3.connect(self._dbName) as conn:
                        for row in newStats:
                            conn.execute('update obStats set curvalue=? where SKILLID = ? and level = ?',
                                         (row[1], self._skill2key[row[0]], level))
                    self._curLevel = level
                    self._initDataSets()
                    self._drawFrame()
                except sqlite3.Error as e:
                    messagebox.showerror('SQL error', f'Update Level {level} skill {skill}\n'
                                         f' failed with message\n{str(e)}')
            
    def _nextLevel(self):
        # Save current level and setup next level in database
        if messagebox.askyesno('Level Up', f'Save Level {self._curLevel} and Level Up?'):
            self._saveDB(force=True)
            try:
                with sqlite3.connect(self._dbName) as conn:
                    for curStats in [ (i, self._row2StatsKey[i]) for i in range(len(self._row2StatsKeys))]: 
                        (row, statRowId) = curStats
                        params = (statRowId, self._curLevel + 1, self._stats[row][0], self._stats[row][0])
                        conn.execute('INSERT INTO obStats (SKILLID,level,curvalue, prevalue) VALUES (?,?,?,?)', params)
                self._curLevel += 1
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Update on obStats(SKILLID,level,curvalue,prevalue)={params}\n'
                                     f' failed with message\n{str(e)}')
            self._drawFrame()

    def _saveDB(self, *args, force=False):
        if force or messagebox.askyesno('Save', 'Commit all skill level changes?'):
            try:
                with sqlite3.connect(self._dbName) as conn:
                    for row in range(len(self._dirty)):
                        if self._dirty[row]:
                            key = self._row2StatsKey[row]
                            skill = self._skilldesclist[row][0]
                            conn.execute('update obStats set curvalue = ? where ROWID = ? ', (self._stats[row][0], key))
                            self._dirty[row] = 0
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Update on {skill} @ row {row} failed with message\n{str(e)}')
        self._checkMenu()
                
    def _newDB(self, *args):
        filename = fd.asksaveasfilename(parent=self.parent, title='Create Database',
                                        filetypes=self._filetypes, defaultextension='.db',
                                        confirmoverwrite=False)
        if filename and len(filename):
            if not os.path.isfile(filename) and messagebox.askyesno('Create DB', f'Create New DB at\n\t{filename}'):
                logger.debug(f'Create database {filename}')
                with open('create_obdb.sql', 'r') as f:
                    filelist = f.readlines()
                createscript = ' '.join(filelist)
                with open('insert_obdb.sql', 'r') as f:
                    filelist = f.readlines()
                insertscript = ' '.join(filelist)
                try:
                    with sqlite3.connect(filename) as conn:
                        res = conn.executescript(createscript)
                        logger.debug(f'create script return {res}')
                        res = conn.executescript(insertscript)
                        logger.debug(f'insert script return {res}')
                    self._setDB(filename)
                    self._drawFrame()
                    
                except (sqlite3.Warning, sqlite3.Error) as e:
                    messagebox.showerror(title='SQL Exception', message=str(e))
            else:
                messagebox.showerror(parent=self.parent,
                                     title='New DB', message=f"{fname} already exists!")          
        self._checkMenu()
        
    def _setupMenu(self):
        self._menu = tk.Menu(self.parent)
        self._setupFileMenu()
        self._filemenu.entryconfigure(2, state='disabled')  # Save menu on if valid
        self._setupDataMenu()
        self._menu.entryconfigure(3, state='disabled')
        self._setupIncMenu()
        self._menu.entryconfigure(3, state='disabled')
        self.parent.config(menu=self._menu)

    def _showSQL(self):
        sql = datadialogs.askstring('SQL', 'Enter SQL for query', parent=self.parent)
        if sql:
            try:
                df = self._getDataFrame(sql)
                datatable = LocalTableDialog(parent=se.f.parent, dataframe=df, title=f'Query: {sql}')
            except (sqlite3.Warning, sqlite3.Error, pd.errors.DatabaseError) as e:
                messagebox.showerror('SQL error', f'Error in {sql}\n{str(e)}')
             
    def _selectMajorSkills(self):
        if self._selectList is None:
            self._selectList = SideBySideDialog(self.parent)
        if self._selectList.show(left=self._minorList, right=self._majorList, maxright=7):
            self._minorList = self._selectList.left
            self._majorList = self._selectList.right
            self._saveMajorList()

    def _setupIncMenu(self):
        self._incMenu = tk.Menu(self._menu, tearoff=0)
        self._menu.add_cascade(label='Increment', menu=self._incMenu, underline=0)
        
    def _fillIncMenu(self):
        lastItem = self._incMenu.index(tk.END)
        if lastItem is not None:
            for i in range(lastItem + 1):
                self._incMenu.delete("end")
        for row in range(len(self._row2Underline)):
            skill = self._skilldesclist[row][0]
            underline = self._row2Underline[row]
            self._incMenu.add_command(label=skill, command=self._incCommands[row][0], underline=underline)

    def _setupDataMenu(self):
        self._dataMenu = tk.Menu(self._menu, tearoff=0)
        self._dataMenu.add_command(label="Level-Up", command=self._nextLevel, underline=6)        
        self._dataMenu.add_command(label="Refresh Data", command=self._refreshData, underline=0)        
        self._dataMenu.add_separator()
        self._dataMenu.add_command(label="Set Level", command=self._setLevel, underline=4)
        self._dataMenu.add_command(label="Edit Level", command=self._editLevel, underline=0)
        self._dataMenu.add_command(label="Major Skills", command=self._selectMajorSkills, underline=0)
        self._dataMenu.add_separator()
        self._dataMenu.add_command(label='SQL', command=self._showSQL, underline=0)
        self._menu.add_cascade(label='Data', menu=self._dataMenu, underline=0)
           
    def _setupFileMenu(self):
        self._filemenu = tk.Menu(self._menu, tearoff=0)
        self._filemenu.add_command(label="New", command=self._newDB, accelerator='Ctrl-N', underline=0)
        self._filemenu.add_command(label="Open", command=self._openDB, accelerator='Ctrl-O', underline=0)
        self._filemenu.add_command(label="Save", command=self._saveDB, accelerator='Ctrl-S', underline=0)
        self._filemenu.add_separator()

        self._filemenu.add_command(label='Quit', command=self._quit, accelerator='Ctrl-Q', underline=0)
        self._menu.add_cascade(label='File', menu=self._filemenu, underline=0)
        self.parent.bind('<Control-KeyPress-N>', self._newDB)
        self.parent.bind('<Control-KeyPress-O>', self._openDB)
        self.parent.bind('<Control-KeyPress-Q>', self._quit)
        self.parent.bind('<Control-KeyPress-n>', self._newDB)
        self.parent.bind('<Control-KeyPress-o>', self._openDB)
        self.parent.bind('<Control-KeyPress-q>', self._quit)

    def _checkMenu(self):
        STATES = ['disabled', 'normal', ]
        
        dbValid = self._dbName is not None and os.path.isfile(self._dbName)
        dbDirty = dbValid and (sum(self._dirty) > 0)
        levelUp = (dbValid and self._levelUp > 9)
        if dbDirty:
            self.parent.bind('<Control-KeyPress-s>', self._saveDB)   
            self.parent.bind('<Control-KeyPress-S>', self._saveDB)
        else:
            self.parent.unbind('<Control-KeyPress-S>')
            self.parent.unbind('<Control-KeyPress-s>')
        self._filemenu.entryconfigure(2, state=STATES[int(dbDirty)])  # Save menu on if valid
        self._menu.entryconfigure(2, state=STATES[dbValid])  # Level menu only if valid
        self._menu.entryconfigure(3, state=STATES[dbValid])

        if dbValid:
            self._dataMenu.entryconfigure(0, state=STATES[int(levelUp)])
        
    def _quit(self, *args):
        if sum(self._dirty) > 0:
            if messagebox.askyesno('Save Changes', 'Save Changes to Database before exit?'):
                self._saveDB(force=True)
        if messagebox.askokcancel('Quit', 'Exit: Are you sure?'):
            self.main.destroy()


def main():
    global logger
    logger = logging.getLogger('obLeveling')
    logger.debug('Begin main()')
    args = get_args()
    if args.verbose:
        logger.setLevel(logging.INFO)
    # config = get_config()
    mainWindow = rootWindow(title=f'Level Manager: {args.database}', dbname=args.database,
                            cnf={})
    if args.new:
        mainWindow._newDB()
    mainWindow.mainloop()    


if __name__ == "__main__":
    main()
else:
    logger = logging.getLogger(__name__)
