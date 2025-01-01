"""Constants used throughout the application."""

# Default chunk size for splitting large outputs
DEFAULT_CHUNK_SIZE = 90000

# Model character and token limits
CHATGPT_CHAR_LIMIT = 500000
CLAUDE_CHAR_LIMIT = 350000
O1_API_TOKEN_LIMIT = 180000
SONNET_API_TOKEN_LIMIT = 180000
FOURTHBRAIN_API_TOKEN_LIMIT = 108000

# Token buffer for responses
TOKEN_BUFFER = 20000

# Model compatibility symbols
COMPAT_CHECK = "✔"
COMPAT_X = "✘"

# Output icons
CLIPBOARD_ICON = "📋"
FILE_ICON = "📄"
STDOUT_ICON = "＞"

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
    '.fish',
    '.md'
]

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
