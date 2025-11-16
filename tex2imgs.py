import os
import argparse
import re
from typing import List
import jinja2

def extract_preamble(latex_string: str) -> List[str]:
    """
    Extracts LaTeX preamble-related statements: usepackage, renewcommand, and newcommand.

    Args:
        latex_string: A string containing the LaTeX document content.

    Returns:
        A list of strings, where each string is a stripped command statement.
    """
    # Combined pattern to find all three command types:
    # 1. \usepackage: Handles optional arguments [...]
    # 2. \renewcommand: Handles required arguments {...}{...}
    # 3. \newcommand: Handles optional arguments [...] and required arguments {...}{...}
    preamble_pattern = re.compile(
        r'('
        r'\\usepackage(\[.*?\])?\{.*?\}'          # \usepackage[options]{package}
        r'|'
        r'\\renewcommand\{.*?\}\{.*?\}'           # \renewcommand{cmd}{def}
        r'|'
        r'\\newcommand(\[.*?\])?\{.*?\}\{.*?\}'   # \newcommand[args]{cmd}{def}
        r')',
        re.DOTALL
    )

    # findall returns a list of tuples since there are multiple capturing groups in the pattern.
    # The first element of each tuple (index 0) is the entire match (Group 1).
    matches = preamble_pattern.findall(latex_string)

    # Extract the full match from each tuple
    preamble_statements = [match[0].strip() for match in matches]

    return list(set(preamble_statements))

def _is_purely_numeric_content(content: str) -> bool:
    """
    Checks if the LaTeX content of an equation consists only of numbers (integers or decimals)
    and surrounding whitespace/newlines, excluding all other mathematical operators,
    variables, or commands.
    
    Args:
        content: The inner content of the LaTeX equation (without delimiters).

    Returns:
        True if the content is purely numeric (only digits, dots, and whitespace), False otherwise.
    """
    # 1. Clean the content by removing common LaTeX structural noise (whitespace, alignment markers, line breaks)
    # This helps focus only on the actual mathematical symbols.
    cleaned_content = re.sub(r'[\s&\]]', '', content)
    
    if not cleaned_content:
        # If the content is empty (e.g., $ $), it is not "purely numeric," so we keep it.
        return False
    
    # 2. Look for any character that signifies a *non-numeric* equation.
    # This includes letters (variables), math operators (+, -, =, etc.), or LaTeX command start (\).
    if re.search(r'[a-zA-Z+\-*/=<>\\]', cleaned_content):
        # If these exist, it's a real equation, not just a number.
        return False 

    # 3. If we reach here, the content only contains digits and dots (after removing operators/variables).
    # We use re.fullmatch to ensure the entire cleaned string is composed ONLY of digits and dots.
    if re.fullmatch(r'[\d.]+', cleaned_content) or re.fullmatch(r'\\mathbf\{[\d.]+\}', cleaned_content):
        return True # It is purely numeric (e.g., "123", "4.5", "12.34").
        
    return False


def _is_commented_out(content: str) -> bool:
    """
    Checks if the content is entirely commented out by LaTeX comment markers (%).
    
    Args:
        content: The inner content of the LaTeX equation (without delimiters/environment).

    Returns:
        True if all non-whitespace content is commented out, False otherwise.
    """
    lines = content.split('\n')
    
    # We look for any line that contains non-whitespace content AND doesn't start with a comment marker.
    for line in lines:
        stripped_line = line.strip()
        # If the line has content and does NOT start with a comment marker, it's not commented out.
        if stripped_line and not stripped_line.startswith('%'):
            return False 

    # If we iterate through all lines and find no significant, uncommented content, 
    # it is considered fully commented out.
    return True


def extract_latex_equations(latex_string: str, equation_types: List[str] = None) -> List[str]:
    r"""
    Extracts all LaTeX equations from a given string, including their surrounding delimiters
    or environment markers (e.g., \begin{align*}...\end{align*}, $$, or $).

    Equations that contain only numbers or are fully commented out are filtered out.

    Args:
        latex_string: A string containing the LaTeX document content.
        equation_types: List of equation types to extract. Options: 'block', 'display', 'inline', 'all'.
                       Default is None which extracts all types.

    Returns:
        A list of unique equation strings, including their original delimiters.
    """
    if equation_types is None:
        equation_types = ['all']
    
    # Normalize equation types
    extract_all = 'all' in equation_types
    extract_block = extract_all or 'block' in equation_types
    extract_display = extract_all or 'display' in equation_types
    extract_inline = extract_all or 'inline' in equation_types
    
    equations = []

    # --- 1. Match LaTeX Environments (block equations) ---
    if extract_block:
        # Group 1: full_match, Group 2: env_name, Group 3: inner_content
        env_pattern = re.compile(
            r'(\\begin\{(equation|align|gather|multline|flalign|alignat|split|cases)\*?\}(.*?)\\end\{\2\*?\})',
            re.DOTALL
        )

        env_matches = env_pattern.findall(latex_string)
        for full_match, _, inner_content in env_matches:
            if not _is_purely_numeric_content(inner_content) and not _is_commented_out(inner_content):
                equations.append(full_match.strip())

    # --- 2. Match Double Dollar Signs ($$ Display Math $$) ---
    if extract_display:
        # Group 1: full_match, Group 2: inner_content
        dd_pattern = re.compile(r'(\$\$([\s\S]*?)\$\$)', re.DOTALL)
        dd_matches = dd_pattern.findall(latex_string)
        for full_match, inner_content in dd_matches:
            if not _is_purely_numeric_content(inner_content) and not _is_commented_out(inner_content):
                equations.append(full_match.strip())

    # --- 3. Match Inline Dollar Signs ($ Inline Math $) ---
    if extract_inline:
        # Group 1: full_match, Group 2: inner_content
        # The inner content matching group is necessary for filtering
        id_pattern = re.compile(r'((?<!\$)\$([^\$]+?)\$(?!\$))', re.DOTALL)
        id_matches = id_pattern.findall(latex_string)
        for full_match, inner_content in id_matches:
            if not _is_purely_numeric_content(inner_content) and not _is_commented_out(inner_content):
                equations.append(full_match.strip())

    return list(set(equations))


def make_tex_file(equation: str, preamble: str, filename: str) -> None:
    """
    Writes a LaTeX equation to a .tex file with a minimal document structure.

    Args:
        equation: The LaTeX equation string to write.
        filename: The output .tex filename.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("."),
        autoescape=jinja2.select_autoescape()
    )
    template = env.get_template("template.tex")
    rendered_tex = template.render(preamble=preamble, equation=equation)
    with open(filename, 'w') as f:
        f.write(rendered_tex)

def post_process_equation(equation: str) -> str:
    """
    Post-processes a LaTeX equation string to ensure proper formatting.

    Args:
        equation: The LaTeX equation string to process.
    Returns:
        The processed LaTeX equation string.
    """
    # make numbered equations unnumbered
    equation = re.sub(r'\\begin\{(equation|align|gather|multline|flalign|alignat)\}', r'\\begin{\1*}', equation)
    equation = re.sub(r'\\end\{(equation|align|gather|multline|flalign|alignat)\}', r'\\end{\1*}', equation)
    return equation

def get_equation_label(equation: str) -> str | None:
    """
    Extracts the label from a LaTeX equation if it exists.

    Args:
        equation: The LaTeX equation string.
    Returns:
        The label string if found, otherwise an empty string.
    """
    label_pattern = re.compile(r'\\label\{(.*?)\}')
    match = label_pattern.search(equation)
    if match:
        return match.group(1).replace(":", "_")
    return None

def process_tex_file(path: str, output_dir: str, preamble: str, density: int = 300, equation_types: List[str] = None) -> str:
    """
    Processes a LaTeX file to extract equations and convert them to images.

    Args:
        path: The path to the LaTeX file.
        output_dir: The directory to save the output images.
        preamble: The accumulated preamble from previous files.
        density: The DPI density for image conversion (default: 300).
        equation_types: List of equation types to extract.
    """
    with open(path, 'r') as f:
        latex_document = f.read()

    extracted_equations = extract_latex_equations(latex_document, equation_types)
    preamble_statements = extract_preamble(latex_document)
    preamble = '\n'.join(preamble_statements)

    os.makedirs('./tmp/texs', exist_ok=True)
    os.makedirs('./tmp/pdfs', exist_ok=True)
    os.makedirs('./tmp/crops', exist_ok=True)

    for i, eq in enumerate(extracted_equations):
        eq = post_process_equation(eq)
        label = get_equation_label(eq)
        output_path = f'{output_dir}/equation_{label}.png' if label else f'{output_dir}/equation_{i+1}.png'

        make_tex_file(eq, preamble, f'./tmp/texs/equation_{i+1}.tex')
        os.system(f'pdflatex -interaction=nonstopmode -output-directory ./tmp/pdfs ./tmp/texs/equation_{i+1}.tex > /dev/null 2>&1')
        os.system(f"pdfcrop -margins 3 ./tmp/pdfs/equation_{i+1}.pdf ./tmp/crops/equation_{i+1}-crop.pdf")
        os.system(f"magick -density {density} ./tmp/crops/equation_{i+1}-crop.pdf -quality 90 {output_path}")
        os.system(f'rm ./tmp/pdfs/equation_{i+1}.log ./tmp/pdfs/equation_{i+1}.aux')
    return preamble



def process_directory(input_dir: str, output_dir: str = 'images', density: int = 300, equation_types: List[str] = None) -> None:
    """
    Processes all LaTeX files in a directory to extract equations and convert them to images.

    Args:
        input_dir: The directory containing LaTeX files.
        output_dir: The directory to save the output images (default: 'images').
        density: The DPI density for image conversion (default: 300).
        equation_types: List of equation types to extract.
    """
    os.makedirs(output_dir, exist_ok=True)
    agg_preamble = ''
    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.endswith('.tex'):
                file_output_dir = os.path.join(output_dir, dirpath.lstrip('./'), filename[:-4])
                os.makedirs(file_output_dir, exist_ok=True)
                preamble = process_tex_file(os.path.join(dirpath, filename), file_output_dir, agg_preamble, density, equation_types)
                agg_preamble += '\n' + preamble


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract equations as images from LaTeX projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Equation types:
  all      - Extract all equation types (default)
  block    - Extract block equations (\\begin{equation}, \\begin{align}, etc.)
  display  - Extract display math equations ($$...$$)
  inline   - Extract inline math equations ($...$)

Examples:
  %(prog)s ./my_latex_project
  %(prog)s ./my_latex_project -o ./output -d 600
  %(prog)s ./my_latex_project -t block display
  %(prog)s ./my_latex_project -o ./equations -t inline -d 450
        '''
    )
    
    parser.add_argument(
        'input_dir',
        help='Directory containing LaTeX files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='images',
        help='Output directory for equation images (default: images)'
    )
    
    parser.add_argument(
        '-t', '--equation-types',
        nargs='+',
        choices=['all', 'block', 'display', 'inline'],
        default=['all'],
        help='Types of equations to extract (default: all)'
    )
    
    parser.add_argument(
        '-d', '--density',
        type=int,
        default=300,
        help='DPI density for image conversion (default: 300)'
    )
    
    args = parser.parse_args()
    
    process_directory(args.input_dir, args.output_dir, args.density, args.equation_types)

