"""Generate many small Python modules to increase repository LOC for company-level demo.

This script creates `platform/generated` package with many modules.
Adjust `num_files` and `lines_per_file` as needed.
"""
from pathlib import Path
import textwrap

OUT_DIR = Path('platform/generated')
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_FILES = 100
LINES_PER_FILE = 600  # approx lines per file -> 100*600 = 60,000 LOC

for i in range(1, NUM_FILES + 1):
    mod_path = OUT_DIR / f'module_{i:03d}.py'
    with mod_path.open('w', encoding='utf-8') as f:
        f.write('# Auto-generated module for LOC expansion\n')
        f.write('"""Module %d: generated helpers"""\n\n' % i)

        # create many simple functions
        for j in range(1, LINES_PER_FILE // 3):
            fname = f'func_{i:03d}_{j:04d}'
            body = textwrap.dedent("""
            def {fname}(x=None):
                '''Return a tuple identifying this generated function.'''
                return ("{fname}", x)


            """).format(fname=fname)
            f.write(body)

        # safety main
        f.write('\nif __name__ == "__main__":\n')
        f.write('    print("Module %d loaded. Sample:", func_%03d_0001())\n' % (i, i))

# write __init__.py
init_file = OUT_DIR / '__init__.py'
init_file.write_text('# Generated package for demo\n')

print(f'Generated {NUM_FILES} modules in {OUT_DIR} (approx {NUM_FILES * LINES_PER_FILE} lines)')
