import argparse
import re
import shutil
from pathlib import Path


def read_list_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def extract_domain_from_line(line):
    """Extract a domain from AGH bracket format or simple lines.
    Returns the domain (lowercased) or None if not a domain-bearing line.
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # bracket format: [/domain/]dns
    m = re.match(r'^\s*\[/(.+?)/\].*$', line)
    if m:
        return m.group(1).lower()

    # full:domain or plain domain with no scheme
    m = re.match(r'^(?:full:)?\s*([^\s/:]+)\s*$', line, flags=re.IGNORECASE)
    if m and not re.match(r'^(?:udp|tcp|tls|https|h3|quic|sdns)://', m.group(1)):
        return m.group(1).lower()

    return None


def is_subdomain(domain, base):
    domain = domain.lower()
    base = base.lower()
    return domain == base or domain.endswith('.' + base)


def should_remove(domain, bases):
    if not domain:
        return False
    for b in bases:
        if is_subdomain(domain, b):
            return True
    return False


def process(input_file, removed_file, output_file=None, backup=True, dry_run=False, verbose=False):
    input_p = Path(input_file)
    removed = [d.lower() for d in read_list_file(removed_file)]

    lines = input_p.read_text().splitlines() if input_p.exists() else []

    kept = []
    removed_count = 0
    for line in lines:
        d = extract_domain_from_line(line)
        if d and should_remove(d, removed):
            removed_count += 1
            if verbose:
                print(f'Removing: {line}')
            continue
        kept.append(line)

    if dry_run:
        print(f'Dry run: would remove {removed_count} lines from {input_file}')
        return removed_count

    out_path = Path(output_file) if output_file else input_p
    if backup and input_p.exists() and out_path.resolve() == input_p.resolve():
        bak = input_p.with_suffix(input_p.suffix + '.bak') if input_p.suffix else Path(str(input_p) + '.bak')
        shutil.copy2(input_p, bak)
        if verbose:
            print(f'Backup created at {bak}')

    out_path.write_text('\n'.join(kept) + ('\n' if kept and not kept[-1].endswith('\n') else '\n'))

    if verbose:
        print(f'Wrote {len(kept)} lines to {out_path} (removed {removed_count})')
    else:
        print(f'Removed {removed_count} entries')

    return removed_count


def main():
    parser = argparse.ArgumentParser(description='Remove domains (and their subdomains) listed in file B from file A')
    parser.add_argument('file_a', help='Input file (will be overwritten unless --output given)')
    parser.add_argument('file_b', help='File with domains to remove (one per line)')
    parser.add_argument('--output', '-o', help='Write results to this file instead of overwriting A')
    parser.add_argument('--no-backup', dest='backup', action='store_false', help='Do not create a backup of the original input')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without writing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()
    process(args.file_a, args.file_b, output_file=args.output, backup=args.backup, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == '__main__':
    main()