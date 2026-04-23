import os

def add_favicon_globally(base_dir):
    favicon_link = '    <link rel="icon" type="image/png" href="{% static \'images/logo.png\' %}">\n'
    static_tag = '{% load static %}'
    
    updated_files = []
    
    # Walk through all directories in the project
    for root, dirs, files in os.walk(base_dir):
        # Skip common non-template directories
        if any(skip in root for skip in ['venv', '.git', '__pycache__', 'media', 'staticfiles']):
            continue
            
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue # Skip binary or non-utf8 files
                
                # Check if it's a template with a head but no favicon
                if '<head>' in content and 'rel="icon"' not in content:
                    print(f"Updating {path}")
                    
                    # Add favicon link after <head>
                    new_content = content.replace('<head>', '<head>\n' + favicon_link)
                    
                    # Ensure {% load static %} is present at the very top if not already there
                    if '{% static' in new_content and '{% load static' not in new_content and '{% load i18n static' not in new_content:
                        # Find the first non-empty line to insert before, or just at the top
                        new_content = static_tag + '\n' + new_content
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated_files.append(path)

    print(f"\nDone! Updated {len(updated_files)} files.")

if __name__ == "__main__":
    # Start from the project root
    add_favicon_globally('e:\\down\\AQUA')
