"""Versioned skill registration shared by A and B; no preloaded programs."""
import ast
import re
from .sandbox import parse, validate_graph, Denied


class SkillLibrary:
    def __init__(self, store, world, actions):
        self.store, self.world, self.actions = store, world, actions

    def current(self):
        return {r['body']['name']: dict(r['body'], id=r['id']) for r in self.store.load(self.world) if r['kind'] == 'skill'}

    def register(self, name, description, source, completion, *, parents=(), origin='model_proposal'):
        if not isinstance(name, str) or not re.fullmatch(r'[\w-]{1,64}', name): raise Denied('skill_name')
        if type(description) is not str or len(description) > 400: raise Denied('description_limit')
        tree = parse(source); parse(completion, condition=True)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and node.func.id == 'act' and node.args[0].value not in self.actions: raise Denied('action_denied')
        library = self.current(); old = library.get(name)
        skill = dict(name=name, description=description, source=source, completion=completion,
                     version=old['version']+1 if old else 1, origin=origin)
        library[name] = skill; validate_graph(library)
        for parent in parents:
            row = self.store.db.execute("SELECT kind FROM records WHERE id=? AND personal=0", (parent,)).fetchone()
            if not row or row[0] != 'experience': raise Denied('experience_required')
        identity = self.store.put('skill', skill, origin, parents=parents)
        if old:
            with self.store.db:
                self.store.db.execute("INSERT INTO deps VALUES (?,?,'correction')", (identity, old['id']))
                self.store.db.execute("UPDATE records SET status='superseded' WHERE id=?", (old['id'],))
        return dict(skill, id=identity)
