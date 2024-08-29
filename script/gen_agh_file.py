import sys
import re

def process_file(input_file, dns):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    new_lines = []
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$')

    for line in lines:
        stripped_line = line.strip()

        if (stripped_line.startswith('regexp:')):
            continue

        if (stripped_line.startswith(('udp://', 'tcp://', 'tls://', 'https://', 'h3://', 'quic://', 'sdns://', '[', '#')) or
            ip_pattern.match(stripped_line)):
            new_lines.append(line)
            continue

        match = re.match(r'(?:full:)?(.+)', stripped_line)
        if match:
            domain = match.group(1)
            new_line = f'[/{domain}/]{dns}\n'
            new_lines.append(new_line)

    with open(input_file, 'w') as file:
        file.writelines(new_lines)

def main():
    if len(sys.argv) != 4 or sys.argv[2] != '--dns':
        print("Usage: script.py <file> --dns <DNS>")
        sys.exit(1)

    input_file = sys.argv[1]
    dns = sys.argv[3]

    process_file(input_file, dns)

if __name__ == "__main__":
    main()
