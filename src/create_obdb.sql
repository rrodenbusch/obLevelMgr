    CREATE TABLE IF NOT EXISTS obLevels (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            level INT );
    CREATE TABLE IF NOT EXISTS obAttributes(
          ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
          name  VARCHAR(20),
          desc  VARCHAR(128) );
    CREATE TABLE IF NOT EXISTS obSkills(
          ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
          ATTRID INTEGER,
          name VARCHAR(20),
          desc VARCHAR(128),
          class VARCHAR(7),
          major INT DEFAULT 0,
          FOREIGN KEY(ATTRID) REFERENCES obAttributes(ROWID)
          );
    CREATE TABLE IF NOT EXISTS obStats (
        ROWID    INTEGER PRIMARY KEY AUTOINCREMENT,
        SKILLID  INTEGER,
        level    INTEGER DEFAULT  2,
        prevalue INTEGER DEFAULT  0,
        curvalue INTEGER DEFAULT  0,
        UNIQUE(SKILLID, level),
        FOREIGN KEY(SKILLID) REFERENCES obSkills(ROWID)
        );
    CREATE VIEW skillMap AS SELECT
        a.ROWID,
        a.class as SkillGroup,
        a.name as Skill,
        a.desc as SkillDesc,
        a.major as MajorSkill,
        b.name as Attr,
        b.desc as AttrDesc
        FROM obSkills a
        LEFT JOIN obAttributes b ON a.ATTRID = b.ROWID;
    CREATE VIEW statsMap AS SELECT
        a.ROWID,
        a.level AS Level,
        a.curvalue as CurValue,
        a.curvalue - a.prevalue as Increase,
        b.name as Skill,
        b.major as MajorSkill,
        b.desc as SkillDesc,
        b.class as SkillGroup,
        c.name as Attr,
        c.desc as AttrDesc
        FROM obStats a
        LEFT JOIN obSkills b ON a.SKILLID = b.ROWID
        LEFT JOIN obAttributes c on b.ATTRID = c.ROWID;