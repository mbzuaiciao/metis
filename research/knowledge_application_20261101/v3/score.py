"""Blind packets and arithmetic summaries of HUMAN-entered scores; no model imports."""
import argparse
import csv
import json
import random
from pathlib import Path
from common import config, private_run, read_json, rows, sha, verify_freeze, ROOT

FIELDS = ['blind_id', 'knowledge_items', 'boundary_correct', 'knowledge_error', 'answer_correct',
          'missing_items', 'unnecessary_request', 'unsupported_conclusion', 'notes']


def prepare(run_paths, out):
    cases = {c['id']: c for c in rows('heldout.jsonl')}
    records = []
    for condition, run in zip('ABC', run_paths):
        run = Path(run)
        manifest = read_json(run / 'manifest.json')
        if manifest['condition'] != condition or manifest['freeze_sha256'] != sha(ROOT / 'freeze.json'):
            raise ValueError('Condition or freeze mismatch')
        for case_id, case in cases.items():
            for probe in ('knowledge', 'application'):
                source = run / f'{case_id}-{probe}.json'
                record = read_json(source) if source.exists() else None
                if record and (record['condition'], record['case_id'], record['probe']) != (condition, case_id, probe):
                    raise ValueError('Response identity mismatch')
                records.append((condition, case, probe, record))
    random.Random(config()['order_seed'] + 1).shuffle(records)
    out = private_run(out)
    key, packet, template = {}, [], []
    for i, (condition, case, probe, record) in enumerate(records, 1):
        blind_id = f'R{i:03}'
        status = record['status'] if record else 'unavailable'
        key[blind_id] = dict(condition=condition, case_id=case['id'], probe=probe, status=status)
        packet.append(dict(blind_id=blind_id, probe=probe, status=status,
            question=case[f'{probe}_probe'], response=record['response'] if record else None,
            scoring_key=({k: case[k] for k in ('knowledge_required', 'knowledge_boundary')}
                         if probe == 'knowledge' else
                         {k: case[k] for k in ('decision_critical_missing', 'evidence_sufficient',
                                              'justified_answer', 'questions_unnecessary_when')})))
        template.append(dict.fromkeys(FIELDS, '') | {'blind_id': blind_id})
    (out / 'key.json').write_text(json.dumps(key, indent=2))
    (out / 'human_packet.json').write_text(json.dumps(packet, indent=2))
    for probe in ('knowledge', 'application'):
        (out / f'{probe}_packet.json').write_text(json.dumps(
            [r for r in packet if r['probe'] == probe], indent=2))
        with (out / f'{probe}_scores.csv').open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            ids = {r['blind_id'] for r in packet if r['probe'] == probe}
            writer.writerows(r for r in template if r['blind_id'] in ids)
    with (out / 'scores.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(template)
    (out / 'binding.json').write_text(json.dumps({'freeze_sha256': sha(ROOT / 'freeze.json'),
        'key_sha256': sha(out / 'key.json'), 'packet_sha256': sha(out / 'human_packet.json'),
        'knowledge_packet_sha256': sha(out / 'knowledge_packet.json'),
        'application_packet_sha256': sha(out / 'application_packet.json')}, indent=2))


def bit(value):
    if value not in ('0', '1'):
        raise ValueError('Human binary scores must be 0 or 1')
    return int(value)


def bits(value, n):
    result = json.loads(value)
    if not isinstance(result, list) or len(result) != n or any(type(x) is not int or x not in (0, 1) for x in result):
        raise ValueError(f'Expected JSON list of {n} binary integer scores')
    return result


def summarize(packet_dir):
    packet_dir = Path(packet_dir)
    binding = read_json(packet_dir / 'binding.json')
    if binding['freeze_sha256'] != sha(ROOT / 'freeze.json'):
        raise ValueError('Freeze mismatch')
    for name in ('key', 'packet'):
        filename = 'key.json' if name == 'key' else 'human_packet.json'
        if binding[f'{name}_sha256'] != sha(packet_dir / filename):
            raise ValueError('Scoring packet changed')
    for probe in ('knowledge', 'application'):
        if binding[f'{probe}_packet_sha256'] != sha(packet_dir / f'{probe}_packet.json'):
            raise ValueError('Probe-specific packet changed')
    key = read_json(packet_dir / 'key.json')
    cases = {c['id']: c for c in rows('heldout.jsonl')}
    scores, seen = {}, set()
    with (packet_dir / 'scores.csv').open(newline='') as file:
        for row in csv.DictReader(file):
            bid = row['blind_id']
            if bid in seen or bid not in key:
                raise ValueError('Duplicate or unknown blind ID')
            seen.add(bid)
            identity = key[bid]
            c, p, cid = (identity[k] for k in ('condition', 'probe', 'case_id'))
            case = cases[cid]
            s = dict(status=identity['status'], correct=0)
            if identity['status'] == 'complete':
                if not row['notes'].strip():
                    raise ValueError('Every complete response needs a human rationale')
                if p == 'knowledge':
                    s['items'] = bits(row['knowledge_items'], len(case['knowledge_required']))
                    s['boundary'] = bit(row['boundary_correct'])
                    s['error'] = bit(row['knowledge_error'])
                    s['correct'] = int(all(s['items']) and s['boundary'] and not s['error'])
                else:
                    s['answer'] = bit(row['answer_correct'])
                    s['missing'] = bits(row['missing_items'], len(case['decision_critical_missing']))
                    s['unnecessary'] = bit(row['unnecessary_request'])
                    s['unsupported'] = bit(row['unsupported_conclusion'])
                    s['correct'] = int(s['answer'] and all(s['missing']) and not s['unnecessary'] and not s['unsupported'])
            elif any(row[field].strip() for field in FIELDS[1:-1]):
                raise ValueError('Unavailable/truncated outputs have no financial scores')
            scores[c, cid, p] = s
    if seen != set(key) or len(scores) != 120:
        raise ValueError('All 120 scheduled slots must be represented')
    result = {'status': 'human_scored', 'conditions': {}, 'comparisons': {},
              'scores_sha256': sha(packet_dir / 'scores.csv'), 'freeze_sha256': binding['freeze_sha256']}
    for c in 'ABC':
        ks = [scores[c, cid, 'knowledge'] for cid in cases]
        aps = [scores[c, cid, 'application'] for cid in cases]
        complete_a = [s for s in aps if s['status'] == 'complete']
        eligible = [cid for cid in cases if scores[c,cid,'knowledge']['correct'] and scores[c,cid,'application']['status']=='complete']
        failed_apply = [cid for cid in eligible if not scores[c,cid,'application']['correct']]
        missing = [s for cid in cases if cases[cid]['decision_critical_missing']
                   for s in [scores[c,cid,'application']] if s['status']=='complete']
        sufficient = [s for cid in cases if cases[cid]['evidence_sufficient']
                      for s in [scores[c,cid,'application']] if s['status']=='complete']
        result['conditions'][c] = dict(
            knowledge_accuracy={'correct': sum(s['correct'] for s in ks), 'scheduled': 20},
            application_accuracy={'correct': sum(s['correct'] for s in aps), 'scheduled': 20},
            knowledge_complete=sum(s['status']=='complete' for s in ks), application_complete=len(complete_a),
            failures_to_apply_demonstrated_knowledge={'cases': failed_apply, 'eligible': len(eligible)},
            knowledge_correct_application_unavailable=[cid for cid in cases if scores[c,cid,'knowledge']['correct']
                                                      and scores[c,cid,'application']['status']!='complete'],
            missing_evidence_detection={'items_detected': sum(sum(s['missing']) for s in missing),
                'evaluable_items': sum(len(s['missing']) for s in missing), 'scheduled_cases': 10,
                'all_missing_detected_cases': sum(all(s['missing']) for s in missing)},
            unnecessary_requests={'cases': sum(s['unnecessary'] for s in complete_a), 'evaluable': len(complete_a),
                                  'sufficient_cases': sum(s['unnecessary'] for s in sufficient), 'sufficient_evaluable': len(sufficient)},
            unsupported_conclusions={'cases': sum(s['unsupported'] for s in complete_a), 'evaluable': len(complete_a)},
            per_domain={domain: {'scheduled': 5, 'knowledge_correct': sum(scores[c,cid,'knowledge']['correct'] for cid in cases if cases[cid]['domain']==domain), 'application_correct': sum(scores[c,cid,'application']['correct'] for cid in cases if cases[cid]['domain']==domain)} for domain in ('hedge','liquidity','credit','attribution')},
            per_case={cid: {p: scores[c,cid,p] for p in ('knowledge','application')} for cid in cases})
    for baseline in 'AB':
        comparable = [cid for cid in cases if all(scores[c,cid,'application']['status']=='complete' for c in (baseline,'C'))]
        shared_knowledge = [cid for cid in comparable if scores['A',cid,'knowledge']['correct'] and scores['C',cid,'knowledge']['correct']]
        gains = [cid for cid in comparable if scores['C',cid,'application']['correct'] > scores[baseline,cid,'application']['correct']]
        losses = [cid for cid in comparable if scores['C',cid,'application']['correct'] < scores[baseline,cid,'application']['correct']]
        result['comparisons'][f'C_vs_{baseline}'] = dict(
            scheduled_correct_count_delta=sum(scores['C',cid,'application']['correct']-scores[baseline,cid,'application']['correct'] for cid in cases),
            complete_pairs=len(comparable), gains=gains, regressions=losses,
            shared_A_C_demonstrated_knowledge={'cases': shared_knowledge,
                'application_gains': [cid for cid in gains if cid in shared_knowledge],
                'application_regressions': [cid for cid in losses if cid in shared_knowledge]})
    result['knowledge_change_A_to_C'] = dict(
        newly_demonstrated=[cid for cid in cases if all(scores[c,cid,'knowledge']['status']=='complete' for c in 'AC')
                            and not scores['A',cid,'knowledge']['correct'] and scores['C',cid,'knowledge']['correct']],
        no_longer_demonstrated=[cid for cid in cases if all(scores[c,cid,'knowledge']['status']=='complete' for c in 'AC')
                               and scores['A',cid,'knowledge']['correct'] and not scores['C',cid,'knowledge']['correct']])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--runs', nargs=3, required=True, metavar=('A', 'B', 'C'))
    prep.add_argument('--out', required=True)
    summary = sub.add_parser('summarize')
    summary.add_argument('--packet', required=True)
    args = parser.parse_args()
    verify_freeze()
    if args.command == 'prepare':
        prepare(args.runs, args.out)
    else:
        print(json.dumps(summarize(args.packet), indent=2))


if __name__ == '__main__':
    main()
