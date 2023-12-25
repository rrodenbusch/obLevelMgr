# A simple utility to help manage Elder Scrolls Oblivion Leveling
#
# (C) Copyright Richard Rodenbusch 2023.
#
# This code is licensed under the GNU Affero General Public License v3.0
# You may obtain a copy of this license in the LICENSE file in the root directory
# of this source tree or at https://www.gnu.org/licenses/agpl-3.0.en.html .
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=bad-docstring-quotes,invalid-name
import os
import csv
import sqlite3
import configparser

import pyautogui
import argparse
import logging
import pandas as pd
import tkinter as tk

from tkinter import messagebox, filedialog as fd
from obleveltracker.datadialogs import (LocalDataFrame,
                                        LocalButtonFrame,
                                        SideBySideDialog,
                                        LocalTableDialog,
                                        LocalEntryDialog,
                                        LocalEntryFrame,
                                        askinteger,
                                        askstring,)


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
        
    Notes:
        font attributes: {'family': 'Lucida Grande', 
                          'weight': 'normal', 
                          'slant': 'roman', 
                          'overstrike': False, 
                          'underline': False, 
                           'size': 13}

    Returns:
        tk.Frame cover the parent Window
    """

    def __init__(self, parent=None, title='obTable', dbname=None, ):
        self._skillmapdf = None
        self._skillsmap = None
        self._curLevel = None
        self._dbName = None
        self._selectList = None
        self._notesDialog = None
        self._dirty = [ 0 ]
        self._levelsInc = 0
        self._filetypes = (('DB files', '*.db'), ('All files', '*.*'))
        
        self._incCommands = [[lambda: self._inc(0)], [lambda: self._inc(1)], [lambda: self._inc(2)], [lambda: self._inc(3)], [lambda: self._inc(4)],
            [lambda: self._inc(5)], [lambda: self._inc(6)], [lambda: self._inc(7)], [lambda: self._inc(8)], [lambda: self._inc(9)],
            [lambda: self._inc(10)], [lambda: self._inc(11)], [lambda: self._inc(12)], [lambda: self._inc(13)], [lambda: self._inc(14)],
            [lambda: self._inc(15)], [lambda: self._inc(16)], [lambda: self._inc(17)], [lambda: self._inc(18)], [lambda: self._inc(19)],
            [lambda: self._inc(20)], ]
        self._recentCommands = [lambda: self._openRecent(0), lambda: self._openRecent(1), lambda: self._openRecent(2),
                                lambda: self._openRecent(3), lambda: self._openRecent(4), lambda: self._openRecent(5),
                                lambda: self._openRecent(6), lambda: self._openRecent(7), lambda: self._openRecent(8),
                                lambda: self._openRecent(9), ]
        self._incButtonHotkeys = []
        if parent is None: parent = tk.Tk()
        self._config = self._getConfig()

        self.parent = parent
        tk.Frame.__init__(self)
        self.main = self.master
        
        # Place the window at the current mouse position, supports multiple monitors best
        self.main.geometry(f'{self._width}x{self._height}')
        mousepos = pyautogui.position()
        self.main.wm_geometry(f'+{mousepos[0]}+{mousepos[1]}')
        self.main.title(title)
        self.main['bg'] = '#D3B683'
        self.font = tk.font.nametofont("TkDefaultFont").actual()
        self.main.protocol("WM_DELETE_WINDOW", self._quit)
        parent.bind("<Configure>", self._on_window_resize)
        self._setDB(dbname)
        self._setupMenu()
        self._drawFrame()
        
    def _saveConfig(self):
        if not self._config.has_section('RecentFiles'):
            self._config.add_section('RecentFiles')
        self._config.set('RecentFiles', 'files', "\n".join(self._recentList))
        with open(self._cfgFile, 'w') as f:
            self._config.write(f)
        
    def _getConfig(self):
        self._config = configparser.ConfigParser()
        self._config.optionxform = str
        self._environ = dict(os.environ)
        self._homeDir = self._environ.get('HOME', self._environ.get('HOMEPATH', ''))
        self._cfgFile = f"{self._homeDir}/.oblevel.ini"
        self._tkDefaultFont = tk.font.nametofont("TkDefaultFont")
        self._defaultFont = tk.font.Font()
        try:
            if os.path.isfile(self._cfgFile):
                self._config.read(self._cfgFile)
            else:
                if os.path.isfile(f"{os.getcwd()}/oblevel.ini"):
                    self._config.read(f"{os.getcwd()}/oblevel.ini")
            if self._config.has_option('default', 'fontSize'):
                self._defaultFont.configure(size=self._config.get('default', 'fontSize'))
            if self._config.has_option('default', 'fontWeight'):
                self._defaultFont.configure(weight=self._config.get('default', 'fontWeight'))
            if self._config.has_option('default', 'fontName'):
                self._defaultFont.configure(family=self._config.get('default', 'fontName'))
        except configparser.Error as e:
            messagebox.showerror('Config Error', f'Configuration File Error\n{e}')
        self._width = self._config.get('main', 'width', fallback='1860')   
        self._height = self._config.get('main', 'height', fallback='1175')   
        self._recentFiles = self._config.get('RecentFiles', 'files', fallback='')
        self._recentList = self._recentFiles.split('\n')
        while '' in self._recentList:
            self._recentList.remove('')
         
        return self._config

    def _drawFrame(self):
        if self._dbName is not None and os.path.isfile(self._dbName):
            # Some colors and default configurations
            desccnf = skillcnf = { 'bd':1, 'relief':'flat', 'bg':'#D3B683', }

            skillshape = (21, 1)
            attrshape = (7, 1)
            attrdesc = (7, 3)
            
            if len(self._majorList) > 0:
                rowbg = ['#C9C9C9' for _ in range(len(self._majorList))]
            else:
                rowbg = []
            
            self._header1 = tk.Frame(self.parent, bg=skillcnf['bg'])
            self._header1.grid(row=0, column=0, sticky='nsew')
            label1 = tk.Label(self._header1, text='Value', padx=1, pady=1, bg=skillcnf['bg'],
                              font=self._defaultFont)
            label1.grid(row=0, column=0, sticky='nsew')            
            label2 = tk.Label(self._header1, text='Increase', padx=1, pady=1, bg=skillcnf['bg'],
                              font=self._defaultFont)
            label2.grid(row=0, column=1, sticky='nsew')
            self._header2 = tk.Label(self.parent, font=self._defaultFont,
                                     text=f'       {self._levelsInc*10}% to Next Level    -----   Current Level {self._curLevel} ', bg=skillcnf['bg'], anchor='w')
            self._header2.grid(row=0, column=1, columnspan=2, sticky='nsew')
            
            self._skills = LocalDataFrame(self.parent, data=self._stats, shape=skillshape, cnf=skillcnf, rowbg=rowbg,
                                          font=self._defaultFont, anchor='n')
            self._skills.grid(row=1, column=0, sticky='nsew')
            
            buttonLabels = self._fillIncMenu()
            self._buttons = LocalButtonFrame(self.parent, shape=skillshape, rowbg=rowbg,
                                          data=buttonLabels,
                                          commands=self._incCommands, font=self._defaultFont,)
            self._buttons.grid(row=1, column=1, sticky='nsew')
            
            self._desc = LocalEntryFrame(self.parent, data=self._skilldesclist, cnf=desccnf, rowbg=rowbg, font=self._defaultFont,)
            self._desc.grid(row=1, column=2, sticky='nsew')
            
            self._attrs = LocalDataFrame(self.parent, shape=attrshape, cnf=skillcnf, data=self._attrSums, anchor='n',
                                         font=self._defaultFont,)
            self._attrs.grid(row=2, column=0, sticky='nsew', pady=10, ipady=2)
            
            self._attrdesc = LocalDataFrame(self.parent, shape=attrdesc, cnf=desccnf, data=self._attrdesclist,
                                            font=self._defaultFont)
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
        self._sqls = {'skilldesc': 'select Skill, Attr, Skilldesc from skillMap order by MajorSkill Desc, sortorder Asc',
              'skillkey': 'select ROWID, MajorSkill, underline from skillMap order by MajorSkill Desc, sortorder Asc',
              'stats': 'select CurValue, Increase from statsMap where level = ? order by MajorSkill Desc, sortorder Asc',
              'attrdesc': 'select name, desc  from obAttributes order by name Asc',
              'attrvals': 'select curvalue, name from attrsMap where level = ? order by name',
              'underlines': 'select name, underline from skillMap order by MajorSkill Desc, Skill Asc',
              'attrkey': 'select ROWID from obAttributes order by name Asc',
              'statskey': 'select ROWID from statsMap where level = ? order by MajorSkill Desc, sortorder Asc',
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
        self._dirty = [ 0 for _ in range(len(keymap))]
        self._skill2key = {}
        self._key2skill = {}
        for row in keymap:
            self._key2skill[row[0]] = row[1]
            self._skill2key[row[1]] = row[0]
            
        self._skilldesclist = self._getDataList(self._sqls['skilldesc'])
        self._attrdesclist = self._getDataList(self._sqls['attrdesc'])

        keymap = self._getDataList(self._sqls['skillkey'])
        self._skillKey2Row = [ [] for _ in range(len(keymap)) ]
        self._row2SkillKey = [ [] for _ in range(len(keymap)) ]
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
        self._attr2row = [  [] for _ in range(len(keymap)) ]
        self._row2attr = [ [] for _ in range(len(keymap)) ]
        rowcnt = 0
        for row in keymap:
            self._attr2row[row[0]] = rowcnt
            self._row2attr[rowcnt] = row[0]
            rowcnt += 1

        if self._curLevel is None:
            levels = self._getDataList('select max(level) from obStats')
            self._curLevel = levels[0][0]
        
        self._attrVals = self._getDataList(self._sqls['attrvals'], (self._curLevel,))
        self._stats = self._getDataList(self._sqls['stats'], (self._curLevel,))
        self._levelsInc = sum([x[1] for x in self._stats[:self._majorSkillCnt]])
        keymap = self._getDataList(self._sqls['statskey'], (self._curLevel,))
        self._stats2row = {}
        self._row2StatsKey = [[] for x in range(len(keymap))]
        rowcnt = 0
        for row in keymap:
            self._stats2row[row[0]] = rowcnt
            self._row2StatsKey[rowcnt] = row[0]
            rowcnt += 1

        self._attrSums = self._getDataList(self._sqls['attrsum'], (self._curLevel,))
        for row in range(len(self._attrSums)):
            self._attrSums[row] = [self._attrVals[row][0], self._attrSums[row][1]]
        if self._curLevel is None: self._curLevel = 0
            
    def _inc(self, x):
        """ Increment the value of skill in row x """
        key = self._row2SkillKey[x]
        skill = self._key2skill[key]
        attrkey = self._attr2key[ self._skill2attr[skill] ]
        if messagebox.askyesno('Increase Skill', f'Increment {skill}?'):
            self._stats[x] = (self._stats[x][0] + 1, self._stats[x][1] + 1)
            self._skills.update(row=x, data=(self._stats[x]))
            self._attrSums[attrkey] = (self._attrSums[attrkey][0] + 1, self._attrSums[attrkey][1] + 1)
            self._attrs.update(row=attrkey, data=self._attrSums[attrkey])
            self._dirty[x] = 1
            if x < self._majorSkillCnt:
                self._levelsInc += 1
            self._checkMenu()
            self._drawFrame()
        
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
            (_, fname) = os.path.split(filename)
            self._dbName = filename
            self.parent.title(f'Oblivion Levels {fname}')
            self._checkMenu()
            self._initDataSets()
            self._fillIncMenu()
            self._drawFrame()
        
    def _openRecent(self, idx):
        filename = self._recentList[idx]
        if filename and len(filename):
            if os.path.isfile(filename):
                self._setDB(filename)
                self._setupRecentMenu(filename=filename)
                self._checkMenu()
        
    def _openDB(self, *args): # pylint: disable=unused-argument
        filename = fd.askopenfilename(parent=self.parent, title='Open Database', filetypes=self._filetypes)
        if filename and len(filename):
            if os.path.isfile(filename):
                self._setDB(filename)
                self._setupRecentMenu(filename=filename)
                self._checkMenu()
            else:
                messagebox.showerror(title='Open File', message=f'{filename} does not exist')

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
        selectSQL = 'select skill, curValue from statsMap where level = ? order by Majorskill DESC, Sortorder ASC'
        try:
            with sqlite3.connect(self._dbName) as conn:
                cursor = conn.execute(selectSQL, (level,))
                levels = cursor.fetchall()
                if create and len(levels) < 21:
                    levels = self._insertLevel(level)
                    cursor = conn.execute(selectSQL, (level,))
                    levels = cursor.fetchall()
                    
            return levels
        
        except sqlite3.Error as e:
            messagebox.showerror('SQL error', f'Get Level {level}\n'
                                 f' failed with message\n{str(e)}')
            
    def _setLevel(self):
        level = askinteger('Select Level', 'Enter level number.', parent=self.parent,
                            default=self._curLevel)
        if level is not None:
            try:
                with sqlite3.connect(self._dbName) as conn:
                    cursor = conn.execute('select skill, curValue from statsMap where level = ?', (level,))
                    levels = cursor.fetchall()
                    if len(levels) == 21:
                        self._curLevel = level
                        self._initDataSets()
                        self._checkMenu()
                        self._drawFrame()
                    else:
                        messagebox.showerror('Level Not Found', f'Level {level} not found.')
            except sqlite3.Error as e:
                messagebox.showerror('SQL error', f'Set Level {level}\n'
                                     f' failed with message\n{str(e)}')
        
    def _editLevel(self):
        level = askinteger('Level to Edit', 'Enter the Level to Edit', parent=self.parent,
                            default=self._curLevel, font=self._defaultFont)
        if level is not None:
            if sum(self._dirty):
                if messagebox.askyesno('Save Changes', 'Save Changes? Unsaved changes will be lost.'):
                    self._saveDB(force=True)
            levels = self._getLevel(level)
            myEntry = LocalEntryDialog(self.parent, cnf={'bg':'#D3B683'}, font=self._defaultFont)
            if myEntry.show(data=levels, editcols=[1, 2, ], cnf={ 'bd':1, 'relief':'flat', 'bg':'#D3B683', }):
                try:
                    newStats = myEntry.data
                    with sqlite3.connect(self._dbName) as conn:
                        for row in newStats:
                            _name = row[0]
                            conn.execute('update obStats set curvalue=? where SKILLID = ? and level = ?',
                                         (row[1], self._skill2key[row[0]], level))
                        if myEntry.show(data=self._attrVals, editcols=[0, ], widths=[10, 20, ]):
                            newAttrs = myEntry.data
                            for row in newAttrs:
                                _name = self._attrVals[1]  # for Exception below
                                conn.execute('update obAttrs set curvalue=? where ATTRID = ? and level = ?',
                                             (row[0], self._attr2key[row[1]], level,))
                    self._curLevel = level
                    self._initDataSets()
                    self._checkMenu()
                    self._drawFrame()
                except sqlite3.Error as e:
                    messagebox.showerror('SQL error', f'Update Level {level} skill {_name}\n'
                                         f' failed with message\n{str(e)}')

    def _saveNotes(self, *args, force=False):
        self._notes = self._notesFrame.data
        #  If not forced, confirm the save
        messagebox.showinfo('save notes', f'save notes\n{self._notes}')
        
    def _cancelNotes(self):
        # if self._notesFrame.isdirty() - Ask for save first
        if messagebox.askokcancel('Close Notes', 'Close Notes?\nUnsaved data will be lost'):
            self._notesDialog.destroy()
            self._notesDialog = None
        
    def _editNotes(self, *args):
        if self._notesDialog:
            self._notesDialog.lift()
        else:
            self._notes = []
            try:
                with open('notes.csv', newline='') as f:
                    reader = csv.reader(f)
                    self._notes = list(reader)
            except FileNotFoundError:
                pass
            self._notesDialog = tk.Toplevel(self.parent, bg='#C9C9C9')
            self._notesDialog.protocol('WM_DELETE_WINDOW', self._cancelNotes)
            self._notesFrame = LocalDataFrame(self._notesDialog, data=self._notes, font=self._defaultFont,)
            self._notesFrame.grid(row=0, column=0, columnspan=2, sticky='nsew')
            self._notesDialog.rowconfigure(0, weight=1)
            saveButton = tk.Button(self._notesDialog, text='Save', command=self._saveNotes, font=self._defaultFont)
            saveButton.grid(row=1, column=0, sticky='e')
            cancButton = tk.Button(self._notesDialog, text='Cancel', command=self._cancelNotes, font=self._defaultFont)
            cancButton.grid(row=1, column=1, sticky='w')
            self._notesDialog.columnconfigure(0, weight=1)
            self._notesDialog.columnconfigure(1, weight=1)    
            self._notesFrame._drawFrame(data=self._notes)
         
        messagebox.showinfo('In Note', f'Edit Notes: {len(self._notes)} lines\n{self._notes}')
    
    def _levelUp(self):
        # Save current level and setup next level in database
        if messagebox.askyesno('Level Up', f'Save Level {self._curLevel} and Level Up?'):
            self._saveDB(force=True)
            try:
                with sqlite3.connect(self._dbName) as conn:
                    for curStats in [ (i, self._row2SkillKey[i]) for i in range(len(self._row2SkillKey))]: 
                        (row, statRowId) = curStats
                        params = (statRowId, self._curLevel + 1, self._stats[row][0], self._stats[row][0])
                        conn.execute('INSERT INTO obStats (SKILLID,level,curvalue, prevalue) VALUES (?,?,?,?)', params)
                    for curAttr in [ (self._attrVals[i][0], self._attr2key[self._attrVals[i][1]])
                                    for i in range(len(self._attrVals)) ]:
                        params = (curAttr[0], curAttr[1], self._curLevel + 1)
                        conn.execute('INSERT INTO obAttrs (curvalue,ATTRID,level) VALUES (?,?,?)', params)
                self._curLevel += 1
                self._initDataSets()
                myEntry = LocalEntryDialog(self.parent, cnf={'bg':'#D3B683'})
                if myEntry.show(data=self._attrVals, editcols=[0, ], widths=[10, 20, ]):
                    with sqlite3.connect(self._dbName) as conn:
                        newAttrs = myEntry.data
                        for row in newAttrs:
                            _name = row[1]  # for Exception below
                            params = (row[0], self._attr2key[row[1]], self._curLevel,)
                            conn.execute('update obAttrs set curvalue=? where ATTRID = ? and level = ?',
                                         (row[0], self._attr2key[row[1]], self._curLevel,))
                    self._initDataSets()
                self._drawFrame()
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
                (fpath, _) = os.path.split(__file__)
                with open(f'{fpath}/create_obdb.sql', 'r') as f:
                    filelist = f.readlines()
                createscript = ' '.join(filelist)
                with open(f'{fpath}/insert_obdb.sql', 'r') as f:
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
                (_,fname) = os.path.split(filename)
                messagebox.showerror(parent=self.parent,
                                     title='New DB', message=f"{fname} already exists!")          
        self._checkMenu()
        
    def _setupMenu(self):
        self._menu = tk.Menu(self.parent)
        self._setupFileMenu()
        self._fileMenu.entryconfigure(2, state='disabled')  # Save menu on if valid
        self._setupEditMenu()
        self._menu.entryconfigure(3, state='disabled')
        self._setupIncMenu()
        self._menu.entryconfigure(3, state='disabled')
        self.parent.config(menu=self._menu)

    def _showSQL(self):
        sql = askstring('SQL', 'Enter SQL for query', parent=self.parent)
        if sql:
            try:
                df = self._getDataFrame(sql)
                _ = LocalTableDialog(parent=self.parent, dataframe=df, title=f'Query: {sql}')
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
        self._menu.add_cascade(label='Skill-Up', menu=self._incMenu, underline=5)
        
    def _incHotKey(self, event):
        self._inc(self._incKeyIndex[event.char.upper()])

    def _clearMenu(self, menu):
        lastItem = menu.index(tk.END)
        if lastItem is not None:
            for _ in range(lastItem + 1):
                menu.delete("end")
        
    def _fillIncMenu(self):
        # Delete any exisiting items
        self._clearMenu(self._incMenu)
        self._incKeyIndex = {}
        buttonLabels = []
        # Insert the increment menu items
        for row in range(len(self._row2Underline)):
            skill = self._skilldesclist[row][0]
            underline = self._row2Underline[row]
            self._incMenu.add_command(label=skill, command=self._incCommands[row][0], underline=underline)
            buttonLabels.append(['Inc', ])
            if underline is not None:
                char = skill[underline]
                buttonLabels[row][0] = char
                self._incKeyIndex[char.upper()] = row
                self.parent.bind(f'<Alt-KeyPress-{char.upper()}>', self._incHotKey)             
                self.parent.bind(f'<Alt-KeyPress-{char.lower()}>', self._incHotKey)
        return buttonLabels

    def _setupEditMenu(self):
        self._editMenu = tk.Menu(self._menu, tearoff=0)
        self._editMenu.add_command(label="Level-Up", command=self._levelUp, underline=6)
        self._editMenu.add_command(label='Edit Notes', command=self._editNotes, underline=5)        
        self._editMenu.add_command(label="Refresh Data", command=self._refreshData, underline=0)        
        self._editMenu.add_separator()
        self._editMenu.add_command(label="Set Level", command=self._setLevel, underline=4)
        self._editMenu.add_command(label="Edit Level", command=self._editLevel, underline=0)
        self._editMenu.add_command(label="Major Skills", command=self._selectMajorSkills, underline=0)
        self._editMenu.add_separator()
        self._editMenu.add_command(label='SQL', command=self._showSQL, underline=0)
        self._menu.add_cascade(label='Edit', menu=self._editMenu, underline=0)
        
    def _setupRecentMenu(self, filename=None):
        if filename in self._recentList:
            self._recentList.remove(filename)
        if filename:
            self._recentList.insert(0, filename)
            self._recentList = self._recentList[0:11]
        self._clearMenu(self._recentMenu)
        if len(self._recentList):
            for idx, filename in zip(range(len(self._recentList)), self._recentList):
                (_, fname) = os.path.split(filename)
                self._recentMenu.add_command(label=f'{idx}: {fname}', underline=0, command=self._recentCommands[idx])
        self._saveConfig()
           
    def _setupFileMenu(self):
        self._fileMenu = tk.Menu(self._menu, tearoff=0)
        self._fileMenu.add_command(label="New", command=self._newDB, accelerator='Ctrl-N', underline=0)
        self._fileMenu.add_command(label="Open", command=self._openDB, accelerator='Ctrl-O', underline=0)
        self._fileMenu.add_command(label="Save", command=self._saveDB, accelerator='Ctrl-S', underline=0)
        self._recentMenu = tk.Menu(self._fileMenu, tearoff=0)
        self._fileMenu.add_cascade(label="Recent..", menu=self._recentMenu, underline=0)
        if len(self._recentList):
            self._setupRecentMenu()
            self._fileMenu.entryconfigure(3, state='normal')
        else:
            self._fileMenu.entryconfigure(3, state='disabled')
        self._fileMenu.add_separator()

        self._fileMenu.add_command(label='Quit', command=self._quit, accelerator='Ctrl-Q', underline=0)
        self._menu.add_cascade(label='File', menu=self._fileMenu, underline=0)
        self._bindHotkeys(self.parent, ['N', 'n', 'O', 'o', 'Q', 'q', ])
        
    def _bindHotkeys(self, parent, keys):
        for char in keys:
            parent.bind(f'<Control-KeyPress-{char}>', self._hotkeyHandler)
    
    def _unbindHotkeys(self, parent, keys):
        for char in [keys]: 
            parent.unbind(f'<Control-KeyPress-{char}>')

    def _hotkeyHandler(self, event):
        match event.keysym.upper():
            case 'N':
                self._newDB()
            case 'O':
                self._openDB()
            case 'Q':
                self._quit()
            case _:
                messagebox.showwarning('Unknown Hot Key', f'Unknown hotkey {event.keysym}')

    def _checkMenu(self):
        STATES = ['disabled', 'normal', ]       
        dbValid = self._dbName is not None and os.path.isfile(self._dbName)
        dbDirty = dbValid and (sum(self._dirty) > 0)
        levelUp = (dbValid and self._levelsInc > 9)
        hasRecent = len(self._recentList) > 0
        
        self._fileMenu.entryconfigure(2, state=STATES[int(dbDirty)])  # Save menu on if valid
        self._fileMenu.entryconfigure(3, state=STATES[int(hasRecent)])  # Recent menu on if valid
        self._menu.entryconfigure(2, state=STATES[dbValid])  # Level menu only if valid
        self._menu.entryconfigure(3, state=STATES[dbValid])  # Inc menu online if dbValid
        self._editMenu.entryconfigure(0, state=STATES[int(levelUp)])
        
        if dbDirty:
            self._bindHotkeys(self.parent, ['S', 's'])
        else:
            self._unbindHotkeys(self.parent, ['S', 's'])
                          
    def _quit(self, *args):
        if sum(self._dirty) > 0:
            if messagebox.askyesno('Save Changes', 'Save Changes to Database before exit?'):
                self._saveDB(force=True)
        if messagebox.askokcancel('Quit', 'Exit: Are you sure?'):
            self.main.destroy()

    def _on_window_resize(self, event):
        self._width = event.width
        self._height = event.height
        # print(f"Window resized to {width}x{height}")


def main():
    global logger
    logger = logging.getLogger('obLeveling')
    logger.debug('Begin main()')
    args = get_args()
    
    if args.verbose:
        logger.setLevel(logging.INFO)
    mainWindow = rootWindow(title=f'Level Manager: {args.database}', dbname=args.database,)
    if args.new:
        mainWindow._newDB()
    mainWindow.mainloop()    


if __name__ == "__main__":
    main()
else:
    logger = logging.getLogger(__name__)
