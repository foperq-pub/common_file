"""Normalize a plain domain list into AGH bracket format entries.

This script reads an input file line-by-line and converts plain domain
lines (or lines prefixed with `full:`) into the AGH bracket format:

    [/domain/]<DNS>

Lines that already look like AGH entries, lines beginning with protocols
(`udp://`, `tls://`, etc.), IP address lines, or comments (`#`) are left
unchanged.

The script supports safe writing: backups, atomic replace, dry-run and
verbose output.
"""

import argparse
import re
import shutil
import stat
import tempfile
import os
from pathlib import Path


def process_file(input_path, dns, output_path=None, backup=True, dry_run=False, verbose=False):
    p_in = Path(input_path)
    if not p_in.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    text = p_in.read_text()
    lines = text.splitlines()

    new_lines = []
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$')
    proto_prefixes = ('udp://', 'tcp://', 'tls://', 'https://', 'h3://', 'quic://', 'sdns://')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # skip empty lines to produce a compact file (consistent with prior behavior)
            continue

        if stripped.startswith('regexp:'):
            # previous behavior: drop regexp entries
            if verbose:
                print(f"Skipping regexp line: {stripped}")
            continue

        if stripped.startswith('#'):
            new_lines.append(line)
            continue

        if stripped.startswith('[') or stripped.startswith(proto_prefixes) or ip_pattern.match(stripped):
            new_lines.append(line)
            continue

        # treat as domain or `full:domain`
        m = re.match(r'(?:full:)?(.+)', stripped)
        if m:
            domain = m.group(1).strip()
            if domain:
                new_lines.append(f'[/{domain}/]{dns}')
                continue

        # fallback: preserve original
        new_lines.append(line)

    # prepare output target
    out_path = Path(output_path) if output_path else p_in

    if dry_run:
        added = sum(1 for l in new_lines if l.startswith('[/' ))
        print(f"Dry run: would write {len(new_lines)} lines to {out_path} (added {added} bracketed entries)")
        return 0

    # If overwriting the input file and backup requested, create a .bak
    if backup and out_path.exists() and out_path.resolve() == p_in.resolve():
        bak = p_in.with_suffix(p_in.suffix + '.bak') if p_in.suffix else Path(str(p_in) + '.bak')
        shutil.copy2(p_in, bak)
        if verbose:
            print(f'Backup created at: {bak}')

    # Atomic write to same directory to preserve cross-filesystem safety
    tmp_dir = out_path.parent
    fd, tmp_name = tempfile.mkstemp(dir=tmp_dir)
    try:
        with os.fdopen(fd, 'w') as tf:
            tf.write('\n'.join(new_lines) + '\n')

        # preserve file mode if overwriting existing file
        if out_path.exists():
            st = out_path.stat()
            os.chmod(tmp_name, stat.S_IMODE(st.st_mode))

        os.replace(tmp_name, str(out_path))
    finally:
        # ensure no stray tmp file
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass

    if verbose:
        print(f'Wrote {len(new_lines)} lines to {out_path}')
    else:
        print(f'Processed {input_path} -> {out_path} (lines: {len(new_lines)})')

    return len(new_lines)


def validate_dns(dns):
    if not dns or dns.strip() == '':
        return False
    # very relaxed validation: allow scheme://..., or ip:port, or bare ip
    return True


def main():
    parser = argparse.ArgumentParser(description='Convert domain list to AGH bracket format')
    parser.add_argument('input_file', help='Input file to process')
    parser.add_argument('--dns', required=True, help='DNS string to append (e.g. tls://223.5.5.5 or 127.0.0.1:54)')
    parser.add_argument('--output', '-o', help='Write to this file instead of overwriting input')
    parser.add_argument('--no-backup', dest='backup', action='store_false', help='Do not create a .bak backup when overwriting')
    parser.add_argument('--dry-run', action='store_true', help='Show changes but do not write')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if not validate_dns(args.dns):
        print('Invalid --dns argument')
        raise SystemExit(2)

    try:
        process_file(args.input_file, args.dns, output_path=args.output, backup=args.backup, dry_run=args.dry_run, verbose=args.verbose)
    except Exception as e:
        print(f'Error: {e}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
