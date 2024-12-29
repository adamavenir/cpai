# Flag Behaviors

## Selection Modifiers
These flags modify what gets selected for processing:

### --dirs
- Changes selection to target directories instead of files
- Only selects immediate directories in the target path(s)
- When combined with --file and {dir} template:
  - Creates separate output file for each selected directory
  - Names each file using the directory's name
- Still respects default excludes (e.g., .git, node_modules)
- Example: `cpai --dirs --file '{dir}.tree.md'` in a directory with src/ and lib/ creates src.tree.md and lib.tree.md

### --all (-a)
- Overrides default excludes
- Includes test files, config files, etc.
- Does not override explicit excludes from command line or config

## Output Modifiers
These flags modify how the selected targets are processed/displayed:

### --tree
- Shows ASCII tree structure instead of file contents
- With normal files: shows directory structure + function outlines
- With --dirs: shows only directory structure

### --nodocs
- Excludes documentation files (.txt, .md)
- Adds to exclude patterns rather than overriding them

## Output Destination
These flags control where output goes:

### --file [FILENAME]
- Writes to file instead of clipboard
- Supports {dir} template when used with --dirs
- Without filename: uses output-cpai.md

### --noclipboard
- Prevents clipboard output
- Requires explicit output destination (--file or --stdout)

### --stdout
- Outputs to terminal instead of clipboard
- Takes precedence over --file