import sys
import re


def process_file(input_file, dns):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        if line.startswith('regexp:'):
            continue

        match = re.match(r'(?:full:)?(.+)', line.strip())
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
