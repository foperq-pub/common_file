import sys

def read_domains(file_path):
    """Reads a file and returns a set of domains."""
    with open(file_path, 'r') as f:
        return set(line.strip().lower() for line in f if line.strip())

def is_subdomain(domain, base_domains):
    """Checks if the domain or its subdomains are in the base domains."""
    for base in base_domains:
        if domain == base or domain.endswith(f".{base}"):
            return True
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <file_A> <file_B> [output_file_C]")
        sys.exit(1)
    
    file_a = sys.argv[1]
    file_b = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Read domains from input files
    domains_a = read_domains(file_a)
    domains_b = read_domains(file_b)
    
    # Filter domains in A by removing domains and subdomains listed in B
    filtered_domains = {domain for domain in domains_a if not is_subdomain(domain, domains_b)}
    
    # Write to output file or print to stdout
    output = output_file if output_file else file_a

    with open(output, 'w') as f:
        for domain in sorted(filtered_domains):
            f.write(domain + '\n')
    print(f"Filtered domains written to {output_file}")

if __name__ == "__main__":
    main()