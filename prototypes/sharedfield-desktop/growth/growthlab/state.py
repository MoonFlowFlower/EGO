"""Local versioned state with explicit provenance and deletion closure.

No raw personal-content audit log or external cache exists in this prototype.
All derived records (including summaries/index/cache/profile) must list parents.
"""
import json
import sqlite3
import uuid

KINDS={'experience','skill','general_rule','map','fact','self','preference','project','summary','index','cache','profile'}
GLOBAL_KINDS={'skill','general_rule','self','preference'}


class Store:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA secure_delete=ON')
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS records(
          id TEXT PRIMARY KEY, kind TEXT NOT NULL, scope TEXT NOT NULL,
          world TEXT, status TEXT NOT NULL, personal INTEGER NOT NULL,
          body TEXT NOT NULL, source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS deps(
          child TEXT REFERENCES records(id) ON DELETE CASCADE,
          parent TEXT REFERENCES records(id) ON DELETE CASCADE,
          relation TEXT NOT NULL CHECK(relation IN ('derived','correction')),
          PRIMARY KEY(child,parent));
        CREATE TABLE IF NOT EXISTS models(id TEXT PRIMARY KEY);
        ''')

        columns={r[1] for r in self.db.execute('PRAGMA table_info(deps)')}
        if 'relation' not in columns:
            # Old probe DBs do not distinguish edges; do not guess a migration.
            self.db.close();raise ValueError('legacy_relationship_schema_requires_explicit_migration')

    def put(self,kind,body,source,*,world=None,personal=False,parents=(),relation='derived'):
        if kind not in KINDS or not source: raise ValueError('metadata_required')
        if relation not in ('derived','correction'):raise ValueError('relation_required')
        if kind in ('map','fact') and world is None: raise ValueError('world_required')
        if kind=='project' and body.get('type')=='world' and world is None: raise ValueError('world_required')
        with self.db:
            for parent in parents:
                row=self.db.execute('SELECT personal,world FROM records WHERE id=?',(parent,)).fetchone()
                if not row: raise ValueError('missing_parent')
                personal=personal or bool(row[0])
                can_generalize=world is None and (kind in GLOBAL_KINDS or (kind=='project' and body.get('type')=='skill'))
                if row[1] is not None and world!=row[1] and not can_generalize: raise ValueError('scope_leak')
            identity=uuid.uuid4().hex
            self.db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?)',
                (identity,kind,'world' if world else 'global',world,'active',int(personal),json.dumps(body,ensure_ascii=False),source))
            self.db.executemany('INSERT INTO deps VALUES (?,?,?)',[(identity,p,relation) for p in parents])
        return identity

    def correct(self,old,body,source):
        row=self.db.execute('SELECT kind,world,personal FROM records WHERE id=?',(old,)).fetchone()
        if row is None: raise ValueError('missing_record')
        new=self.put(row[0],body,source,world=row[1],personal=bool(row[2]),parents=[old],relation='correction')
        with self.db: self.db.execute("UPDATE records SET status='superseded' WHERE id=?",(old,))
        return new

    def load(self,world,*,include_personal=False):
        query="SELECT id,kind,world,status,body,source FROM records WHERE status='active' AND (world IS NULL OR world=?)"
        if not include_personal: query+=' AND personal=0'
        return [dict(zip(('id','kind','world','status','body','source'),(r[0],r[1],r[2],r[3],json.loads(r[4]),r[5]))) for r in self.db.execute(query,(world,))]

    def delete_private(self,identity):
        row=self.db.execute('SELECT personal FROM records WHERE id=?',(identity,)).fetchone()
        if not row or not row[0]: raise ValueError('not_private')
        heads={identity}
        while True:
            found={r[1] for r in self.db.execute("SELECT child,parent FROM deps WHERE relation='correction'") if r[0] in heads}
            if found<=heads:break
            heads|=found
        ids=set(heads)
        while True:
            found={r[0] for r in self.db.execute('SELECT child,parent FROM deps') if r[1] in ids}
            if found<=ids: break
            ids|=found
        with self.db:
            self.db.executemany('DELETE FROM records WHERE id=?',[(x,) for x in ids])
        self.db.execute('VACUUM')
        return len(ids)

    def switch_model(self,model):
        with self.db:
            self.db.execute('DELETE FROM models')
            self.db.execute('INSERT INTO models VALUES (?)',(model,))

    def close(self): self.db.close()
