import requests
import json
import os
import glob
import difflib
import re
import subprocess
import shutil
from datetime import datetime
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table

console = Console()

class CLIAgent:
    def __init__(self):
        self.api_key = "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"
        self.model = "kwaipilot/kat-coder-pro:free"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.conversation = []
        
    def get_workspace_context(self):
        """Obtine contextul complet si inteligent al workspace-ului"""
        # Context de baza
        files = []
        for root, dirs, filenames in os.walk("."):
            for filename in filenames:
                if not filename.startswith('.') and not '__pycache__' in root:
                    rel_path = os.path.relpath(os.path.join(root, filename))
                    files.append(rel_path)
        
        # Detecteaza tipul de proiect
        project_info = self.detect_project_type()
        
        # Incarca configuratii
        configs = self.load_config_files()
        
        # Analizeaza dependentele
        dependencies = self.analyze_dependencies()
        
        # Construieste contextul
        context = f"""Current directory: {os.getcwd()}
Project type: {project_info['type']}
Language: {project_info['language']}
Framework: {project_info.get('framework', 'None')}

Available files: {', '.join(files[:15])}
"""
        
        # Adauga dependentele
        if dependencies["main"]:
            context += f"\nMain dependencies: {', '.join(dependencies['main'][:8])}"
        if dependencies["python"]:
            context += f"\nPython packages: {', '.join(dependencies['python'][:8])}"
        
        # Adauga preview-uri de configuratie
        for config_name, config_content in configs.items():
            if len(config_content) < 500:
                context += f"\n\n{config_name}:\n{config_content[:300]}\n---"
        
        # Adauga continutul fisierelor importante
        important_files = [f for f in files[:5] if f.endswith(('.py', '.js', '.md')) and os.path.getsize(f) < 1000]
        for file in important_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()[:400]
                context += f"\n\n{file} preview:\n{content}\n---"
            except:
                pass
        
        return context
    
    def read_file(self, filepath):
        """Citeste un fisier"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Afiseaza fisierul cu syntax highlighting
            ext = os.path.splitext(filepath)[1].lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.html': 'html',
                '.css': 'css', '.json': 'json', '.md': 'markdown'
            }
            
            syntax = Syntax(content, lang_map.get(ext, 'text'), theme="monokai")
            console.print(Panel(
                syntax,
                title=f"📄 {filepath}",
                border_style="green"
            ))
            
            return content
        except Exception as e:
            console.print(f"[red]Error reading {filepath}: {e}[/red]")
            return f"Error reading {filepath}: {e}"
    
    def write_file(self, filepath, content):
        """Scrie un fisier si arata diff-ul"""
        old_content = ""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                old_content = f.read()
        
        try:
            # Creeaza directorul daca nu exista
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Arata diff-ul
            self.show_diff(filepath, old_content, content)
            return True
        except Exception as e:
            console.print(f"[red]Error writing {filepath}: {e}[/red]")
            return False
    
    def show_diff(self, filepath, old_content, new_content):
        """Arata diferentele intre versiuni"""
        if not old_content:
            console.print(f"[green]✅ Created {filepath}[/green]")
            # Afiseaza continutul nou creat
            ext = os.path.splitext(filepath)[1].lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.html': 'html',
                '.css': 'css', '.json': 'json', '.md': 'markdown'
            }
            syntax = Syntax(new_content, lang_map.get(ext, 'text'), theme="monokai")
            console.print(Panel(syntax, title=f"📄 {filepath}", border_style="green"))
            return
            
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"{filepath} (before)",
            tofile=f"{filepath} (after)",
            lineterm=""
        ))
        
        if diff:
            console.print(f"\n[yellow]🔄 Modified {filepath}:[/yellow]")
            diff_text = "".join(diff)
            console.print(Panel(
                Syntax(diff_text, "diff", theme="monokai"),
                title="Changes",
                border_style="yellow"
            ))
    
    def list_files(self, pattern="*"):
        """Listeaza fisierele din workspace"""
        tree = Tree(f"📁 {os.path.basename(os.getcwd())}")
        
        for root, dirs, files in os.walk("."):
            if '__pycache__' in root or '.git' in root:
                continue
                
            level = tree
            if root != ".":
                level = tree.add(f"📁 {os.path.relpath(root)}")
            
            for file in sorted(files):
                if not file.startswith('.'):
                    if pattern == "*" or pattern.lower() in file.lower():
                        level.add(f"📄 {file}")
        
        console.print(tree)
    
    def execute_file_operations(self, response_text):
        """Executa operatiunile cu fisiere din raspunsul AI"""
        modified_response = response_text
        
        # Detecteaza si executa blocuri de cod cu nume de fisier
        code_blocks = re.findall(r'```(\w+):([^\n]+)\n(.*?)```', response_text, re.DOTALL)
        
        for lang, filename, code in code_blocks:
            filename = filename.strip()
            code = code.strip()
            
            if self.write_file(filename, code):
                # Inlocuieste blocul de cod cu confirmarea
                old_block = f'```{lang}:{filename}\n{code}\n```'
                new_block = f'✅ **Created/Modified {filename}**'
                modified_response = modified_response.replace(old_block, new_block)
        
        # Detecteaza comenzi de citire fisiere
        read_patterns = [
            r'read\s+(?:file\s+)?([\w\./]+\.[a-zA-Z]+)',
            r'show\s+(?:me\s+)?(?:file\s+)?([\w\./]+\.[a-zA-Z]+)',
            r'display\s+([\w\./]+\.[a-zA-Z]+)'
        ]
        
        for pattern in read_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                filename = match.group(1)
                if os.path.exists(filename):
                    self.read_file(filename)
        
        # Detecteaza comenzi de listare
        if re.search(r'list\s+files|show\s+files|files\s+in', response_text, re.IGNORECASE):
            self.list_files()
        
        return modified_response
    
    def send_message_stream(self, user_message):
        """Trimite mesaj la AI cu streaming"""
        context = self.get_workspace_context()
        
        system_prompt = {
            "role": "system",
            "content": f"""You are CodeMate CLI, an advanced AI coding assistant with full file system access.

Current workspace context:
{context}

Capabilities:
- Create/modify files using: ```language:filename.ext\ncode here\n```
- Read files by mentioning: "read filename.ext" or "show filename.ext"
- List files by saying: "list files" or "show files"
- Analyze code, suggest improvements, debug issues
- Understand project structure and dependencies

Always:
1. Understand the full context before acting
2. Explain what you're doing
3. Use appropriate file formats and naming
4. Follow best practices for the language/framework
5. Be concise but thorough"""
        }
        
        if not self.conversation or self.conversation[0]["role"] != "system":
            self.conversation.insert(0, system_prompt)
        
        self.conversation.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(self.base_url, json={
                "model": self.model,
                "messages": self.conversation,
                "temperature": 0.2,
                "max_tokens": 3000,
                "stream": True
            }, headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }, stream=True)
            
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and json_data['choices']:
                                delta = json_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    chunk = delta['content']
                                    full_response += chunk
                                    yield chunk
                        except json.JSONDecodeError:
                            continue
            
            # Executa operatiunile cu fisiere dupa streaming
            self.execute_file_operations(full_response)
            self.conversation.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            yield f"❌ Error: {e}"
    
    def search_in_files(self, search_term):
        """Cauta text in toate fisierele"""
        results = []
        for root, dirs, files in os.walk("."):
            if '__pycache__' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.md', '.txt', '.json')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                if search_term.lower() in line.lower():
                                    results.append((filepath, i, line.strip()))
                    except:
                        continue
        
        if results:
            table = Table(title=f"Search Results for '{search_term}'")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="magenta")
            table.add_column("Content", style="white")
            
            for filepath, line_num, content in results[:20]:  # Primele 20
                table.add_row(filepath, str(line_num), content[:80] + "..." if len(content) > 80 else content)
            
            console.print(table)
        else:
            console.print(f"[yellow]No results found for '{search_term}'[/yellow]")
    
    def git_status(self):
        """Afiseaza status Git"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                if result.stdout.strip():
                    console.print("[yellow]Git Status:[/yellow]")
                    for line in result.stdout.strip().split('\n'):
                        status = line[:2]
                        filename = line[3:]
                        color = "green" if status.strip() == "A" else "red" if status.strip() == "D" else "yellow"
                        console.print(f"[{color}]{status} {filename}[/{color}]")
                else:
                    console.print("[green]Working directory clean[/green]")
            else:
                console.print("[red]Not a git repository[/red]")
        except FileNotFoundError:
            console.print("[red]Git not installed[/red]")
    
    def run_file(self, filepath):
        """Executa un fisier si arata output-ul"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext == '.py':
                result = subprocess.run(['python', filepath], 
                                      capture_output=True, text=True, cwd='.')
            elif ext == '.js':
                result = subprocess.run(['node', filepath], 
                                      capture_output=True, text=True, cwd='.')
            else:
                console.print(f"[red]Cannot run {ext} files[/red]")
                return
            
            console.print(f"[green]Output from {filepath}:[/green]")
            if result.stdout:
                console.print(Panel(result.stdout, title="STDOUT", border_style="green"))
            if result.stderr:
                console.print(Panel(result.stderr, title="STDERR", border_style="red"))
            console.print(f"[dim]Exit code: {result.returncode}[/dim]")
            
        except FileNotFoundError as e:
            console.print(f"[red]Runtime not found: {e}[/red]")
    
    def backup_project(self):
        """Creeaza backup al proiectului"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        
        try:
            # Creeaza directorul de backup
            os.makedirs("backups", exist_ok=True)
            backup_path = os.path.join("backups", backup_name)
            
            # Copiaza toate fisierele (exclude backups si __pycache__)
            def ignore_patterns(dir, files):
                return [f for f in files if f in ['__pycache__', '.git', 'backups', 'node_modules']]
            
            shutil.copytree(".", backup_path, ignore=ignore_patterns)
            console.print(f"[green]✅ Backup created: {backup_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Backup failed: {e}[/red]")
    def detect_project_type(self):
        """Detecteaza tipul de proiect"""
        project_info = {"type": "Unknown", "framework": None, "language": "Mixed"}
        
        # Detecteaza prin fisiere de configurare
        if os.path.exists("package.json"):
            try:
                with open("package.json", 'r') as f:
                    pkg = json.loads(f.read())
                    project_info["type"] = "Node.js"
                    project_info["language"] = "JavaScript"
                    
                    # Detecteaza framework-uri
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps:
                        project_info["framework"] = "React"
                    elif "vue" in deps:
                        project_info["framework"] = "Vue.js"
                    elif "express" in deps:
                        project_info["framework"] = "Express"
            except:
                pass
        
        elif os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
            project_info["type"] = "Python"
            project_info["language"] = "Python"
            
            # Detecteaza framework-uri Python
            try:
                if os.path.exists("requirements.txt"):
                    with open("requirements.txt", 'r') as f:
                        reqs = f.read().lower()
                        if "flask" in reqs:
                            project_info["framework"] = "Flask"
                        elif "django" in reqs:
                            project_info["framework"] = "Django"
                        elif "fastapi" in reqs:
                            project_info["framework"] = "FastAPI"
            except:
                pass
        
        elif os.path.exists("pom.xml"):
            project_info["type"] = "Java"
            project_info["language"] = "Java"
            project_info["framework"] = "Maven"
        
        elif os.path.exists("Cargo.toml"):
            project_info["type"] = "Rust"
            project_info["language"] = "Rust"
        
        # Detecteaza prin extensii de fisiere
        py_files = len(glob.glob("*.py"))
        js_files = len(glob.glob("*.js")) + len(glob.glob("*.ts"))
        
        if py_files > js_files and project_info["type"] == "Unknown":
            project_info["type"] = "Python"
            project_info["language"] = "Python"
        elif js_files > py_files and project_info["type"] == "Unknown":
            project_info["type"] = "JavaScript"
            project_info["language"] = "JavaScript"
        
        return project_info
    
    def load_config_files(self):
        """Incarca fisiere de configurare importante"""
        configs = {}
        
        config_files = [
            ".env", "config.json", "package.json", "requirements.txt",
            "pyproject.toml", "tsconfig.json", "webpack.config.js"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) < 2000:  # Doar fisiere mici
                            configs[config_file] = content[:1000]
                except:
                    pass
        
        return configs
    
    def analyze_dependencies(self):
        """Analizeaza dependentele proiectului"""
        deps = {"main": [], "dev": [], "python": []}
        
        # Node.js dependencies
        if os.path.exists("package.json"):
            try:
                with open("package.json", 'r') as f:
                    pkg = json.loads(f.read())
                    deps["main"] = list(pkg.get("dependencies", {}).keys())[:10]
                    deps["dev"] = list(pkg.get("devDependencies", {}).keys())[:10]
            except:
                pass
        
        # Python dependencies
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", 'r') as f:
                    lines = f.readlines()
                    for line in lines[:15]:
                        if line.strip() and not line.startswith("#"):
                            dep = line.strip().split("==")[0].split(">=")[0]
                            deps["python"].append(dep)
            except:
                pass
        
        return deps
    
    def batch_modify_files(self, pattern, old_text, new_text):
        """Modifica text in multiple fisiere simultan"""
        modified_files = []
        
        for root, dirs, files in os.walk("."):
            if '__pycache__' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.md', '.txt')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if old_text in content:
                            new_content = content.replace(old_text, new_text)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            modified_files.append(filepath)
                            
                    except Exception as e:
                        console.print(f"[red]Error modifying {filepath}: {e}[/red]")
        
        if modified_files:
            console.print(f"[green]✅ Modified {len(modified_files)} files:[/green]")
            for file in modified_files:
                console.print(f"  📄 {file}")
        else:
            console.print(f"[yellow]No files found containing '{old_text}'[/yellow]")
    
    def refactor_rename(self, old_name, new_name, file_types=None):
        """Redenumeste functii/clase in toate fisierele"""
        if file_types is None:
            file_types = ['.py', '.js']
        
        modified_files = []
        patterns = [
            rf'\bdef\s+{old_name}\b',  # Python functions
            rf'\bclass\s+{old_name}\b',  # Python/JS classes
            rf'\bfunction\s+{old_name}\b',  # JS functions
            rf'\b{old_name}\s*=\s*function',  # JS function assignments
            rf'\b{old_name}\(',  # Function calls
        ]
        
        for root, dirs, files in os.walk("."):
            if '__pycache__' in root or '.git' in root:
                continue
            for file in files:
                if any(file.endswith(ext) for ext in file_types):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        original_content = content
                        
                        # Aplica toate pattern-urile
                        for pattern in patterns:
                            content = re.sub(pattern, lambda m: m.group().replace(old_name, new_name), content)
                        
                        if content != original_content:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            modified_files.append(filepath)
                            
                    except Exception as e:
                        console.print(f"[red]Error refactoring {filepath}: {e}[/red]")
        
        if modified_files:
            console.print(f"[green]✅ Refactored '{old_name}' to '{new_name}' in {len(modified_files)} files:[/green]")
            for file in modified_files:
                console.print(f"  📄 {file}")
        else:
            console.print(f"[yellow]No occurrences of '{old_name}' found[/yellow]")
    
    def apply_design_pattern(self, pattern_type, target_files=None):
        """Aplica design patterns comune"""
        if target_files is None:
            target_files = glob.glob("*.py")
        
        if pattern_type.lower() == "singleton":
            singleton_code = '''\nclass Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
'''
            
            for file in target_files:
                if os.path.exists(file):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if "class Singleton" not in content:
                            content += singleton_code
                            with open(file, 'w', encoding='utf-8') as f:
                                f.write(content)
                            console.print(f"[green]✅ Added Singleton pattern to {file}[/green]")
                    except Exception as e:
                        console.print(f"[red]Error applying pattern to {file}: {e}[/red]")
        
        elif pattern_type.lower() == "factory":
            factory_code = '''\nclass Factory:
    @staticmethod
    def create(type_name, *args, **kwargs):
        # Add your factory logic here
        pass
'''
            
            for file in target_files:
                if os.path.exists(file):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if "class Factory" not in content:
                            content += factory_code
                            with open(file, 'w', encoding='utf-8') as f:
                                f.write(content)
                            console.print(f"[green]✅ Added Factory pattern to {file}[/green]")
                    except Exception as e:
                        console.print(f"[red]Error applying pattern to {file}: {e}[/red]")
        
        else:
            console.print(f"[yellow]Pattern '{pattern_type}' not supported. Available: singleton, factory[/yellow]")
    
    def batch_create_structure(self, structure_type):
        """Creeaza structuri de proiect comune"""
        if structure_type.lower() == "flask":
            structure = {
                "app.py": '''from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return "Hello, World!"\n\nif __name__ == '__main__':\n    app.run(debug=True)\n''',
                "requirements.txt": "Flask>=2.0.0\n",
                "templates/index.html": '''<!DOCTYPE html>\n<html>\n<head>\n    <title>Flask App</title>\n</head>\n<body>\n    <h1>Welcome to Flask!</h1>\n</body>\n</html>\n''',
                "static/style.css": "body { font-family: Arial, sans-serif; }\n"
            }
        
        elif structure_type.lower() == "fastapi":
            structure = {
                "main.py": '''from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"Hello": "World"}\n\n@app.get("/items/{item_id}")\ndef read_item(item_id: int, q: str = None):\n    return {"item_id": item_id, "q": q}\n''',
                "requirements.txt": "fastapi>=0.68.0\nuvicorn>=0.15.0\n"
            }
        
        elif structure_type.lower() == "react":
            structure = {
                "package.json": '''{\n  "name": "react-app",\n  "version": "1.0.0",\n  "dependencies": {\n    "react": "^18.0.0",\n    "react-dom": "^18.0.0"\n  }\n}\n''',
                "src/App.js": '''import React from 'react';\n\nfunction App() {\n  return (\n    <div>\n      <h1>Hello React!</h1>\n    </div>\n  );\n}\n\nexport default App;\n''',
                "src/index.js": '''import React from 'react';\nimport ReactDOM from 'react-dom';\nimport App from './App';\n\nReactDOM.render(<App />, document.getElementById('root'));\n'''
            }
        
        else:
            console.print(f"[yellow]Structure '{structure_type}' not supported. Available: flask, fastapi, react[/yellow]")
            return
        
        # Creeaza fisierele
        created_files = []
        for filepath, content in structure.items():
            try:
                os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                created_files.append(filepath)
            except Exception as e:
                console.print(f"[red]Error creating {filepath}: {e}[/red]")
        
        if created_files:
            console.print(f"[green]✅ Created {structure_type} project structure:[/green]")
            for file in created_files:
                console.print(f"  📄 {file}")
    
    def debug_code(self, filepath):
        """Analizeaza codul pentru erori si probleme"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            issues = []
            lines = code.split('\n')
            
            # Detecteaza probleme comune
            for i, line in enumerate(lines, 1):
                # Python issues
                if filepath.endswith('.py'):
                    if 'print(' in line and line.strip().startswith('print('):
                        issues.append((i, "Debug print statement", "warning"))
                    if 'import *' in line:
                        issues.append((i, "Wildcard import (avoid)", "warning"))
                    if len(line) > 100:
                        issues.append((i, "Line too long (>100 chars)", "style"))
                    if 'TODO' in line or 'FIXME' in line:
                        issues.append((i, "TODO/FIXME comment", "info"))
                
                # JavaScript issues
                elif filepath.endswith('.js'):
                    if 'console.log(' in line:
                        issues.append((i, "Debug console.log statement", "warning"))
                    if 'var ' in line:
                        issues.append((i, "Use let/const instead of var", "warning"))
                    if '==' in line and '===' not in line:
                        issues.append((i, "Use === instead of ==", "warning"))
            
            # Syntax check pentru Python
            if filepath.endswith('.py'):
                try:
                    compile(code, filepath, 'exec')
                except SyntaxError as e:
                    issues.append((e.lineno or 0, f"Syntax Error: {e.msg}", "error"))
            
            # Afiseaza rezultatele
            if issues:
                table = Table(title=f"Code Analysis: {filepath}")
                table.add_column("Line", style="cyan")
                table.add_column("Issue", style="white")
                table.add_column("Type", style="magenta")
                
                for line_num, issue, issue_type in issues:
                    color = "red" if issue_type == "error" else "yellow" if issue_type == "warning" else "blue"
                    table.add_row(str(line_num), issue, f"[{color}]{issue_type}[/{color}]")
                
                console.print(table)
            else:
                console.print(f"[green]✅ No issues found in {filepath}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing {filepath}: {e}[/red]")
    
    def run_with_profiling(self, filepath):
        """Executa cod cu profiling de performanta"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.py':
            # Creeaza script de profiling
            profile_script = f'''
import cProfile
import pstats
import io
from pstats import SortKey

if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    
    # Executa codul
    exec(open("{filepath}").read())
    
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(10)  # Top 10 functii
    print(s.getvalue())
'''
            
            try:
                result = subprocess.run(['python', '-c', profile_script], 
                                      capture_output=True, text=True, cwd='.')
                
                console.print(f"[green]Performance Profile for {filepath}:[/green]")
                if result.stdout:
                    console.print(Panel(result.stdout, title="Profiling Results", border_style="blue"))
                if result.stderr:
                    console.print(Panel(result.stderr, title="Errors", border_style="red"))
                    
            except Exception as e:
                console.print(f"[red]Profiling failed: {e}[/red]")
        
        else:
            console.print(f"[yellow]Profiling not supported for {ext} files[/yellow]")
    
    def suggest_fixes(self, filepath):
        """Sugereaza fix-uri pentru probleme comune"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            suggestions = []
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                if filepath.endswith('.py'):
                    # Python suggestions
                    if 'range(len(' in line:
                        suggestions.append((i, "Use enumerate() instead of range(len())", 
                                          line.strip(), line.replace('range(len(', 'enumerate(')))
                    
                    if '.keys():' in line and 'for ' in line:
                        suggestions.append((i, "Iterate directly over dict, not .keys()", 
                                          line.strip(), line.replace('.keys():', ':')))
                    
                    if 'if len(' in line and ') > 0:' in line:
                        suggestions.append((i, "Use 'if container:' instead of 'if len(container) > 0:'", 
                                          line.strip(), line.replace('if len(', 'if ').replace(') > 0:', ':')))
                
                elif filepath.endswith('.js'):
                    # JavaScript suggestions
                    if 'for (var i = 0' in line:
                        suggestions.append((i, "Use for...of or forEach() instead of traditional for loop", 
                                          line.strip(), "// Use: for (const item of array) { ... }"))
            
            if suggestions:
                console.print(f"[yellow]💡 Optimization suggestions for {filepath}:[/yellow]")
                for line_num, suggestion, old_code, new_code in suggestions:
                    console.print(f"\n[cyan]Line {line_num}:[/cyan] {suggestion}")
                    console.print(f"[red]- {old_code}[/red]")
                    console.print(f"[green]+ {new_code}[/green]")
            else:
                console.print(f"[green]✅ No optimization suggestions for {filepath}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing {filepath}: {e}[/red]")
    
    def test_runner(self, test_pattern="test_*.py"):
        """Ruleaza teste si arata rezultatele"""
        test_files = glob.glob(test_pattern)
        
        if not test_files:
            console.print(f"[yellow]No test files found matching '{test_pattern}'[/yellow]")
            return
        
        console.print(f"[green]Running tests matching '{test_pattern}'...[/green]")
        
        for test_file in test_files:
            try:
                result = subprocess.run(['python', '-m', 'pytest', test_file, '-v'], 
                                      capture_output=True, text=True, cwd='.')
                
                console.print(f"\n[cyan]📋 {test_file}:[/cyan]")
                if result.returncode == 0:
                    console.print(f"[green]✅ PASSED[/green]")
                else:
                    console.print(f"[red]❌ FAILED[/red]")
                
                if result.stdout:
                    console.print(Panel(result.stdout, title="Test Output", border_style="green" if result.returncode == 0 else "red"))
                    
            except FileNotFoundError:
                # Fallback la unittest
                try:
                    result = subprocess.run(['python', '-m', 'unittest', test_file.replace('.py', '').replace('/', '.')], 
                                          capture_output=True, text=True, cwd='.')
                    
                    console.print(f"\n[cyan]📋 {test_file}:[/cyan]")
                    if result.returncode == 0:
                        console.print(f"[green]✅ PASSED[/green]")
                    else:
                        console.print(f"[red]❌ FAILED[/red]")
                    
                    if result.stdout or result.stderr:
                        output = result.stdout + result.stderr
                        console.print(Panel(output, title="Test Output", border_style="green" if result.returncode == 0 else "red"))
                        
                except Exception as e:
                    console.print(f"[red]Error running {test_file}: {e}[/red]")
    
    def terminal_command(self, command):
        """Executa comenzi de terminal integrate"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd='.')
            
            console.print(f"[cyan]$ {command}[/cyan]")
            
            if result.stdout:
                console.print(Panel(result.stdout, title="Output", border_style="green"))
            
            if result.stderr:
                console.print(Panel(result.stderr, title="Error", border_style="red"))
            
            console.print(f"[dim]Exit code: {result.returncode}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Command failed: {e}[/red]")
    
    def preview_file(self, filepath):
        """Preview pentru fisiere HTML/Markdown"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if ext == '.md':
                # Markdown preview
                from rich.markdown import Markdown
                console.print(Panel(
                    Markdown(content),
                    title=f"📄 {filepath} (Markdown Preview)",
                    border_style="blue"
                ))
            
            elif ext == '.html':
                # HTML preview (simplified)
                import re
                # Extract title
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                title = title_match.group(1) if title_match else "HTML Document"
                
                # Extract body content (simplified)
                body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
                body_content = body_match.group(1) if body_match else content
                
                # Remove HTML tags for preview
                clean_content = re.sub(r'<[^>]+>', '', body_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                
                console.print(Panel(
                    f"Title: {title}\n\n{clean_content[:500]}{'...' if len(clean_content) > 500 else ''}",
                    title=f"🌐 {filepath} (HTML Preview)",
                    border_style="blue"
                ))
            
            elif ext == '.json':
                # JSON preview with formatting
                import json as json_lib
                try:
                    parsed = json_lib.loads(content)
                    formatted = json_lib.dumps(parsed, indent=2)
                    syntax = Syntax(formatted, "json", theme="monokai")
                    console.print(Panel(
                        syntax,
                        title=f"📋 {filepath} (JSON Preview)",
                        border_style="blue"
                    ))
                except json_lib.JSONDecodeError as e:
                    console.print(f"[red]Invalid JSON: {e}[/red]")
            
            else:
                console.print(f"[yellow]Preview not supported for {ext} files[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error previewing {filepath}: {e}[/red]")
    
    def syntax_check_realtime(self, filepath):
        """Syntax checking in timp real"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            errors = []
            
            if ext == '.py':
                # Python syntax check
                try:
                    compile(content, filepath, 'exec')
                    console.print(f"[green]✅ {filepath}: Syntax OK[/green]")
                except SyntaxError as e:
                    errors.append(f"Line {e.lineno}: {e.msg}")
                
                # Import check
                import ast
                try:
                    tree = ast.parse(content)
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                    
                    # Check if imports exist
                    missing_imports = []
                    for imp in imports[:5]:  # Check first 5
                        try:
                            __import__(imp.split('.')[0])
                        except ImportError:
                            missing_imports.append(imp)
                    
                    if missing_imports:
                        errors.append(f"Missing imports: {', '.join(missing_imports)}")
                        
                except:
                    pass
            
            elif ext == '.js':
                # Basic JavaScript syntax check
                brackets = {'(': ')', '[': ']', '{': '}'}
                stack = []
                
                for i, char in enumerate(content):
                    if char in brackets:
                        stack.append((char, i))
                    elif char in brackets.values():
                        if not stack:
                            errors.append(f"Unmatched closing bracket '{char}' at position {i}")
                        else:
                            open_char, _ = stack.pop()
                            if brackets[open_char] != char:
                                errors.append(f"Mismatched brackets at position {i}")
                
                if stack:
                    errors.append(f"Unclosed brackets: {[char for char, _ in stack]}")
                
                if not errors:
                    console.print(f"[green]✅ {filepath}: Basic syntax OK[/green]")
            
            elif ext == '.json':
                # JSON syntax check
                import json as json_lib
                try:
                    json_lib.loads(content)
                    console.print(f"[green]✅ {filepath}: Valid JSON[/green]")
                except json_lib.JSONDecodeError as e:
                    errors.append(f"JSON Error: {e.msg} at line {e.lineno}")
            
            # Display errors
            if errors:
                console.print(f"[red]❌ {filepath}: Syntax errors found:[/red]")
                for error in errors:
                    console.print(f"  • {error}")
                    
        except Exception as e:
            console.print(f"[red]Error checking {filepath}: {e}[/red]")
    
    def live_file_monitor(self, filepath, duration=30):
        """Monitorizeaza fisierul pentru modificari"""
        if not os.path.exists(filepath):
            console.print(f"[red]File {filepath} not found[/red]")
            return
        
        import time
        
        console.print(f"[yellow]🔍 Monitoring {filepath} for {duration} seconds...[/yellow]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        
        last_modified = os.path.getmtime(filepath)
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                current_modified = os.path.getmtime(filepath)
                
                if current_modified != last_modified:
                    console.print(f"[green]📝 {filepath} was modified![/green]")
                    self.syntax_check_realtime(filepath)
                    last_modified = current_modified
                
                time.sleep(1)
            
            console.print(f"[yellow]Monitoring stopped after {duration} seconds[/yellow]")
            
        except KeyboardInterrupt:
            console.print("[yellow]Monitoring stopped by user[/yellow]")
    
    def clear_conversation(self):
        self.conversation = []