# tex2imgs
Extract equations as images from your tex project

## Usage

```bash
python tex2imgs.py <input_dir> [options]
```

### Positional Arguments
- `input_dir` - Directory containing LaTeX files to process

### Options
- `-o, --output-dir <dir>` - Output directory for equation images (default: `images`)
- `-t, --equation-types <type> [<type> ...]` - Types of equations to extract (default: `all`)
  - `all` - Extract all equation types
  - `block` - Extract block equations (`\begin{equation}`, `\begin{align}`, etc.)
  - `display` - Extract display math equations (`$$...$$`)
  - `inline` - Extract inline math equations (`$...$`)
- `-d, --density <dpi>` - DPI density for image conversion (default: `300`)

### Examples

Extract all equations from a LaTeX project:
```bash
python tex2imgs.py ./my_latex_project
```

Extract equations to a custom output directory with higher resolution:
```bash
python tex2imgs.py ./my_latex_project -o ./output -d 600
```

Extract only block and display equations:
```bash
python tex2imgs.py ./my_latex_project -t block display
```

Extract only inline equations with custom output and density:
```bash
python tex2imgs.py ./my_latex_project -o ./equations -t inline -d 450
```

Get help:
```bash
python tex2imgs.py --help
```

