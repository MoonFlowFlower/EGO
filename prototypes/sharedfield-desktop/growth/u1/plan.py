"""Frozen protocol and source integrity. No fitting to returned results."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from growthlab.models import MODEL, ROUTE
from growthlab.records import ROOT, write_json
from .fixtures import build
from .protocol import A_SLEEP_SYSTEM, B_SLEEP_SYSTEM, DECISION_SYSTEM, MEMORY_LIMIT

BASE = ROOT / 'runs/u1'
OUT = ROOT / 'evidence/u1'
MANIFEST = OUT / 'frozen_v1.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def source_hashes():
    files = list((ROOT / 'u1').rglob('*.py')) + [ROOT / ('growthlab/' + n + '.py') for n in
            ('state', 'forks', 'models', 'memory', 'consolidation', 'decision', 'records')]
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}


def verify(manifest):
    for name, value in manifest['source_sha256'].items():
        if sha(ROOT / name) != value:
            raise ValueError('frozen_source_changed:' + name)
    for name, value in manifest['artifact_sha256'].items():
        if sha(ROOT / name) != value:
            raise ValueError('frozen_artifact_changed:' + name)


def freeze():
    if MANIFEST.exists():
        raise ValueError('manifest_already_exists_no_overwrite')
    OUT.mkdir(parents=True, exist_ok=True)
    fixtures = build()
    write_json(OUT / 'scripts_v1.json', fixtures)
    write_json(OUT / 'prompts_v1.json', {'decision': DECISION_SYSTEM, 'B_sleep': B_SLEEP_SYSTEM, 'A_sleep': A_SLEEP_SYSTEM})
    endpoints_path = BASE / 'preflight/official_zdr_endpoints.json'
    endpoints = read(endpoints_path)
    required = {'response_format', 'max_tokens', 'temperature', 'reasoning'}
    eligible = [x for x in endpoints
                if x['model_id'] in ('deepseek/deepseek-v4-pro-0813', 'deepseek/deepseek-v4-pro')
                and required <= set(x['supported_parameters'])
                and float(x['pricing']['prompt']) <= .000001
                and float(x['pricing']['completion']) <= .000002]
    eligible.sort(key=lambda x: (float(x['pricing']['prompt']) + float(x['pricing']['completion']), x['model_id'], x['tag']))
    stronger = eligible[0] if eligible else None
    configs = {
        'main': {'model': MODEL, 'route': ROUTE, 'reasoning': False},
        'same_reasoning': {'model': MODEL, 'route': ROUTE, 'reasoning': True},
        'stronger': ({'model': stronger['model_id'], 'route': stronger['tag'], 'reasoning': True} if stronger else None),
    }
    budget = ROOT / 'runs/phase1/budget.sqlite'
    db = sqlite3.connect(budget.resolve().as_uri() + '?mode=ro', uri=True)
    used = db.execute('SELECT COALESCE(SUM(usd),0) FROM charges').fetchone()[0]
    db.close()
    manifest = {
        'freeze_version': 'u1-v1', 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'design_version': 'v0.8', 'source_commit': '55a3390762cef89e0741ec8c11fddbc1845eeb1a',
        'claim_ceiling': 'Synthetic convention pipeline only; not understanding a person, subjective experience, or product benefit.',
        'configs': configs, 'descriptive_stronger_skip': None if stronger else 'no_compatible_zdr_route_under_inherited_price_caps',
        'shared_budget': {'path': 'runs/phase1/budget.sqlite', 'limit_usd': 5, 'used_at_freeze': used,
                          'never_reset': True, 'unknown_reservations_retained': True},
        'request_policy': {'temperature': 0, 'concurrency': 1, 'provider_fallbacks': False, 'zdr': True,
                           'data_collection': 'deny', 'max_price_usd_per_million': {'prompt': 1, 'completion': 2},
                           'decision_max_tokens': 1024, 'sleep_max_tokens': 2048, 'reasoning_max_tokens': 8192,
                           'memory_serialized_utf8_bytes': MEMORY_LIMIT, 'lane_wall_seconds': 3600,
                           'transport': 'One identical retry after 30s for HTTP 429/502/503/504, TimeoutError or URLError; second failure stops only that independent lane. No content retries. Resource/privacy/budget stops are hard stops.',
                           'protocol': 'Every invalid returned decision is scored false. Two consecutive invalid envelopes/property order/choice outputs stop that lane. No repair, re-prompt or regrade.'},
        'ua': {'main_decisions': 180, 'descriptive_decisions_each': 90, 'description_arms': 'B only; each independently scheduled even when the main lane stops.',
               'conditions': ['none', 'true', 'false'], 'situations_per_family': 10,
               'criterion': 'B code true >= 8/10 AND B code false >= 8/10. Both interpretation and action must match. A and other families descriptive.',
               'complete_required': True,
               'emotional_prior': 'Report no-memory target count per arm/config. A no-memory choice already matching the convention is separately flagged; it is not counted as evidence against prior knowledge.'},
        'ub': {'calls': 10, 'explicit': 5, 'two_correction_contexts': 5,
               'criterion': 'At least 8/10 contain one active card passing frozen trigger/meaning keywords and exact trigger configuration, with accepted quoted user provenance.'},
        'uc': {'calls': 10, 'criterion': 'Every card correct at Ub completion retains its exact active ID, trigger, meaning and source_ids after each of 10 consolidations without a contrary user correction.',
               'failure_does_not_block_chain': True},
        'chain': {'forks': ['B_R', 'B_I', 'B_N', 'A_R'], 'initial_decisions': 240, 'correction_decisions': 60, 'deletion_decisions': 60,
                  'total_decisions': 360, 'situations_per_family_per_split': 10,
                  'retention': 'B_R T1 code >= 8/10 and promise >= 8/10 after a fresh process reload.',
                  'causal': 'B_R T1 code >= 8/10; B_I and B_N T1 code each <= 2/10.',
                  'correction': 'B_R corrected T1 follows the new interpretation AND action >= 8/10 separately in code and promise; their old cards are superseded with correction-source links. Emotion scores and provenance are descriptive.',
                  'deletion': 'Every B_R saved-state file lacks all original/corrected teaching texts, quoted meanings, and derived reflection/card payloads; deleted T1 follow rates for old and new conventions each <= corresponding B_N T1 rate + 0.10 separately in code and promise. Emotion follow rates are descriptive; complete erasure remains a privacy invariant.',
                  'baseline': 'A_R follows the identical teaching/session/consolidation/restart/testing/correction/deletion schedule. Same memory bound; no B annotation.',
                  'descriptive': ['T2 per family, also split by literal-trigger versus paraphrase', 'emotion retention', 'all A_R metrics']},
        'model_switch': {'eligibility': 'Main Ua failed its completed quality gate, OR stopped with an explicitly recorded protocol/transport failure, and at least one complete descriptive arm passes the unchanged Ua B-code criterion. Incomplete is not called an accuracy failure.',
                         'priority': ['same_reasoning', 'stronger'], 'maximum_switches': 1,
                         'action': 'Write immutable frozen_v2 manifest before any new paid call; rerun full 180-call Ua from new stores on chosen config; unchanged scripts/prompts/criteria. Only then Ub/Uc/chain use that config. If rerun fails, stop without repair.'},
        'stopping': 'Ua or Ub failure stops downstream main work. Description lanes remain separate. Uc failure is reported on every chain result. No Crafter execution.',
        'ambiguity_resolutions': [
            'The estimate about 300 chain decisions is a cost estimate, not a sample cap. Full 10-case T1/T2 and equal A schedule require 360; no sample shrinkage.',
            'Each decision counts only if interpretation AND action both follow the frozen target; reply never affects score.',
            'Ua known memory intervention uses hand-inserted quoted cards for B and the same source plus hand-written plain reflection for A; no extra teaching-model calls.',
            'Real learning in Ub/chain is only model-proposed, program-validated. Meaning is quoted verbatim for mechanical provenance; this is a bounded exact-quotation protocol, not a semantic truth checker.',
            'Canonical correction grammar requires the quoted old and new meaning in an explicit not-old/now-new sentence. No inferred semantic contradiction.',
            'Uc reuses all Ub conversations plus one unrelated dialogue per round; omission in a proposal never deletes a card.',
            'T2 code/emotion cases 0-4 retain the literal trigger in changed contexts; cases 5-9 paraphrase it. Both are reported separately; no semantic matcher is smuggled in.',
            'Deletion tests the live state and SQLite sidecars, not the immutable synthetic experiment scripts and audit logs. No copied payload state is written outside SQLite; offline output records contain process IDs/counts/hash only.',
            'B_N empty consolidation is a documented no-op with zero model calls because no evidence exists; B_I receives equal-character-length unrelated dialogues.',
            'Author predictions are frozen historical intuitions in design section 16, not extra pass criteria.',
            'P7 may reserve concurrently in the same ledger. Failed-call before/after ledger differences are shared_ledger_delta_unattributed, never attributed as U1-only expense. Successful charge_id is exact; total ledger occupancy remains authoritative.',
            'Supported situation grammar is 周<weekday><HH:MM>以后上线. Parsed weekday/time/login must equal the structured trigger, or the library rejects the card.',
            'Section 16 says T2 and emotional-signal classes are descriptive. Emotion correction/deletion/provenance are fully reported but not promoted to quality thresholds; code and promise retain the original gates.',
        ],
        'official_metadata': {'source': 'https://openrouter.ai/api/v1/endpoints/zdr', 'sha256': sha(endpoints_path),
                              'chosen_stronger': stronger, 'fee_for_preflight': 0},
        'source_sha256': source_hashes(),
        'artifact_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in (OUT / 'scripts_v1.json', OUT / 'prompts_v1.json')},
    }
    write_json(MANIFEST, manifest)
    return manifest


def switch_manifest(original, choice, ua_evidence):
    path = OUT / 'frozen_v2.json'
    if path.exists():
        raise ValueError('switched_manifest_already_exists')
    value = json.loads(json.dumps(original))
    value.update(freeze_version='u1-v2-model-switch', parent_manifest_sha256=sha(MANIFEST),
                 selected_config=choice, model_switch_evidence=ua_evidence,
                 frozen_at_utc=datetime.now(timezone.utc).isoformat())
    verify(value)
    write_json(path, value)
    return path
