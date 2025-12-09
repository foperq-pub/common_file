#!/usr/bin/env python3
"""Add domains to an AGH-style file.

Usage:
  add_domains.py <domains_file> --to <target_file> --dns <DNS> [--position top|bottom] [--backup] [--dry-run]

The script reads domains (one per line) from <domains_file>, normalizes and deduplicates them,
then appends or prepends entries in the AGH bracket format `[/<domain>/]<DNS>` to <target_file>.
If a domain already exists in the target (including subdomain matches), it will not be added again.
"""
import argparse
import re
import shutil
from pathlib import Path


def read_domains_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def extract_domain_from_line(line):
    """Try to extract a single domain from a variety of input formats.
    Returns a normalized domain (lowercased) or None.
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # bracket format: [/domain/]dns
    m = re.match(r'^\s*\[/(.+?)/\].*$', line)
    if m:
        return m.group(1).lower()

    # full:domain or plain domain
    m = re.match(r'^(?:full:)?\s*([^\s/:]+)\s*$', line, flags=re.IGNORECASE)
    if m and not re.match(r'^(?:udp|tcp|tls|https|h3|quic|sdns)://', m.group(1)):
        return m.group(1).lower()

    return None


def existing_domains_from_target(lines):
    domains = set()
    for line in lines:
        d = extract_domain_from_line(line)
        if d:
            domains.add(d)
    return domains


def is_subdomain(domain, base):
    domain = domain.lower()
    base = base.lower()
    return domain == base or domain.endswith('.' + base)


def add_domains(domains, target_path, dns, position='bottom', backup=True, dry_run=False):
    p = Path(target_path)
    if not p.exists():
        # create file if missing
        existing_lines = []
    else:
        existing_lines = p.read_text().splitlines()

    existing = existing_domains_from_target(existing_lines)

    # filter and dedupe incoming domains
    unique = []
    seen = set()
    for d in domains:
        if not d:
            continue
        nd = d.strip().lower()
        if nd in seen:
            continue
        seen.add(nd)
        # skip if already present as domain or subdomain of existing
        skip = False
        for e in existing:
            if is_subdomain(nd, e) or is_subdomain(e, nd):
                skip = True
                break
        if not skip:
            unique.append(nd)

    if not unique:
        print('No new domains to add.')
        return 0

    new_lines = [f'[/{d}/]{dns}' for d in unique]

    out_lines = []
    if position == 'top':
        out_lines = new_lines + existing_lines
    else:
        out_lines = existing_lines + new_lines

    if dry_run:
        print('Dry run — the following lines would be added:')
        for l in new_lines:
            print(l)
        return 0

    if backup and p.exists():
        bak = p.with_suffix(p.suffix + '.bak') if p.suffix else Path(str(p) + '.bak')
        shutil.copy2(p, bak)
        print(f'Backup created at: {bak}')

    p.write_text('\n'.join(out_lines) + ('\n' if out_lines and not out_lines[-1].endswith('\n') else '\n'))
    print(f'Added {len(new_lines)} domains to {p} (position={position})')
    return len(new_lines)


def main():
    parser = argparse.ArgumentParser(description='Add domains to an AGH-style file')
    parser.add_argument('domains_file', help='File with domains (one per line)')
    parser.add_argument('--to', dest='target', required=True, help='Target file to modify')
    parser.add_argument('--dns', dest='dns', required=True, help='DNS string to use in entries (e.g. tls://223.5.5.5)')
    parser.add_argument('--position', choices=['top', 'bottom'], default='bottom', help='Where to add entries')
    parser.add_argument('--no-backup', dest='backup', action='store_false', help='Do not create a backup of the target')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')

    args = parser.parse_args()

    domains = read_domains_file(args.domains_file)
    # normalize possible lines containing messy format
    parsed = []
    for d in domains:
        ed = extract_domain_from_line(d)
        parsed.append(ed if ed else d.strip().lower())

    add_domains(parsed, args.target, args.dns, position=args.position, backup=args.backup, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
