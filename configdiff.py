#!/usr/bin/env python3
"""configdiff - Smart config file comparison."""
import json, argparse, sys, os, configparser

def load_json(path):
    with open(path) as f: return json.load(f)

def load_ini(path):
    cp = configparser.ConfigParser()
    cp.read(path)
    return {s: dict(cp[s]) for s in cp.sections()}

def load_env(path):
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                result[k.strip()] = v.strip().strip('"').strip("'")
    return result

def flatten(d, prefix=''):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

def diff_dicts(a, b, name_a='file1', name_b='file2'):
    flat_a, flat_b = flatten(a), flatten(b)
    all_keys = sorted(set(flat_a) | set(flat_b))
    added = removed = changed = same = 0
    
    for key in all_keys:
        in_a, in_b = key in flat_a, key in flat_b
        if in_a and not in_b:
            print(f"  - {key} = {flat_a[key]}")
            removed += 1
        elif in_b and not in_a:
            print(f"  + {key} = {flat_b[key]}")
            added += 1
        elif str(flat_a[key]) != str(flat_b[key]):
            print(f"  ~ {key}: {flat_a[key]} → {flat_b[key]}")
            changed += 1
        else:
            same += 1
    
    print(f"\n  +{added} -{removed} ~{changed} ={same}")

def load_auto(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.json': return load_json(path)
    elif ext in ('.ini', '.cfg', '.conf'): return load_ini(path)
    elif ext in ('.env',): return load_env(path)
    else:
        # Try JSON first
        try: return load_json(path)
        except: pass
        try: return load_ini(path)
        except: pass
        return load_env(path)

def main():
    p = argparse.ArgumentParser(description='Config file comparison')
    p.add_argument('file1')
    p.add_argument('file2')
    p.add_argument('-j', '--json', action='store_true', help='Output as JSON')
    args = p.parse_args()
    
    a = load_auto(args.file1)
    b = load_auto(args.file2)
    
    if args.json:
        flat_a, flat_b = flatten(a), flatten(b)
        diff = {'added': {}, 'removed': {}, 'changed': {}}
        for k in set(flat_b) - set(flat_a): diff['added'][k] = flat_b[k]
        for k in set(flat_a) - set(flat_b): diff['removed'][k] = flat_a[k]
        for k in set(flat_a) & set(flat_b):
            if str(flat_a[k]) != str(flat_b[k]):
                diff['changed'][k] = {'from': flat_a[k], 'to': flat_b[k]}
        print(json.dumps(diff, indent=2, default=str))
    else:
        print(f"Comparing {args.file1} ↔ {args.file2}\n")
        diff_dicts(a, b, args.file1, args.file2)

if __name__ == '__main__':
    main()
