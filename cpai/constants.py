"""Constants used throughout the codebase."""

# Default patterns to exclude
DEFAULT_EXCLUDE_PATTERNS = [
    # Build directories
    '**/build/**',
    '**/dist/**',
    '**/__pycache__/**',
    '**/.cache/**',
    '**/coverage/**',
    '**/.next/**',
    '**/out/**',
    '**/.nuxt/**',
    '**/.output/**',
    '**/*.egg-info/**',
    '**/node_modules/**',
    
    # Virtual environments
    '**/venv/**',
    '**/virtualenv/**',
    '**/env/**',
    '**/.env/**',
    '**/.venv/**',
    
    # IDE and system files
    '**/.idea/**',
    '**/.vscode/**',
    '**/.DS_Store',
    '**/.git/**',
    '**/.svn/**',
    '**/.hg/**',
    
    # Log files
    '**/*.log',
    '**/npm-debug.log*',
    '**/yarn-debug.log*',
    '**/yarn-error.log*',
    
    # Config files
    '**/.env',
    '**/.envrc',
    '**/.env.*',
    '**/.python-version',
    '**/.ruby-version',
    '**/.node-version',
    '**/package.json',
    '**/package-lock.json',
    '**/yarn.lock',
    '**/tsconfig.json',
    '**/jsconfig.json',
    '**/*.config.js',
    '**/pyproject.toml',
    '**/setup.py',
    '**/setup.cfg',
    '**/requirements.txt',
    '**/Pipfile',
    '**/Pipfile.lock',
    '**/bower.json',
    '**/composer.json',
    '**/composer.lock',
    
    # Minified files
    '**/*.min.js',
    '**/*.min.css',
    '**/*.map',
    
    # Build artifacts
    '**/dist/**',
    '**/build/**',
    '**/target/**',
    
    # Media files
    '**/*.jpg',
    '**/*.jpeg',
    '**/*.png',
    '**/*.gif',
    '**/*.ico',
    '**/*.pdf',
    '**/*.zip',
    '**/*.tar.gz',
    '**/*.tgz',
    '**/*.woff',
    '**/*.woff2',
    '**/*.ttf',
    '**/*.eot',
    '**/*.mp3',
    '**/*.mp4',
    '**/*.mov',
    '**/*.avi'
]

# Default file extensions to include
DEFAULT_FILE_EXTENSIONS = [
    '.py',
    '.js',
    '.jsx',
    '.ts',
    '.tsx',
    '.sol',
    '.rs',
    '.go',
    '.java',
    '.cpp',
    '.c',
    '.h',
    '.hpp',
    '.cs',
    '.php',
    '.rb',
    '.swift',
    '.kt',
    '.scala',
    '.m',
    '.mm',
    '.r',
    '.sh',
    '.bash',
    '.zsh',
    '.fish'
]

# Default chunk size for content
DEFAULT_CHUNK_SIZE = 50000

# Core source patterns to always include
CORE_SOURCE_PATTERNS = [
    '**/*.py',
    '**/*.js',
    '**/*.jsx',
    '**/*.ts',
    '**/*.tsx',
    '**/*.sol',
    '**/*.rs',
    '**/*.go',
    '**/*.java',
    '**/*.cpp',
    '**/*.c',
    '**/*.h',
    '**/*.hpp',
    '**/*.cs',
    '**/*.php',
    '**/*.rb',
    '**/*.swift',
    '**/*.kt',
    '**/*.scala',
    '**/*.m',
    '**/*.mm',
    '**/*.r',
    '**/*.sh',
    '**/*.bash',
    '**/*.zsh',
    '**/*.fish'
]
