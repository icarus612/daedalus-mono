import subprocess
import sys

def word_to_pdf(input_file, output_file):
    subprocess.call(['unoconv', '-f', 'pdf', '-o', output_file, input_file])

if __name__ == '__main__':
		word_to_pdf(sys.argv[1], sys.argv[2])
