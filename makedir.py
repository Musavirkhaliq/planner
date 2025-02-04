import os

# Define the directory structure
structure = {
    'app': {
        '__init__.py': '',
        'auth.py': '',
        'config.py': '',
        'crud.py': '',
        'database.py': '',
        'dependencies.py': '',
        'main.py': '',
        'models.py': '',
        'schemas.py': '',
        'utils.py': ''
    },
    'frontend': {
        'static': {
            'script.js': '',
            'style.css': ''
        },
        'templates': {
            'dashboard.html': '',
            'index.html': '',
            'login.html': '',
            'register.html': ''
        }
    }
}

# Create the directory structure
for root, dirs in structure.items():
    os.mkdir(root)
    for file, content in dirs.items():
        if isinstance(content, dict):
            for subfile, subcontent in content.items():
                filepath = os.path.join(root, file, subfile)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                open(filepath, 'w').close()
        else:
            filepath = os.path.join(root, file)
            open(filepath, 'w').close()
