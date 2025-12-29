# CodeMate CLI

🤖 **Advanced AI coding assistant with full file system access**

CodeMate CLI is a powerful terminal-based AI assistant that helps you with coding, file management, debugging, and project analysis. Think of it as your personal coding companion!

## ✨ Features

- 🔍 **Smart file operations** - Create, read, modify files with AI assistance
- 🚀 **Streaming responses** - Real-time AI responses
- 🔧 **Advanced debugging** - Code analysis, profiling, and optimization suggestions
- 📁 **Project intelligence** - Auto-detects project type and dependencies
- 🔄 **Batch operations** - Bulk file modifications and refactoring
- 🖥️ **Terminal integration** - Execute system commands
- 📊 **File monitoring** - Real-time syntax checking
- 🎨 **Rich interface** - Colored output with syntax highlighting

## 🚀 Quick Install

### Windows:
```bash
git clone https://github.com/yourusername/codemate-cli.git
cd codemate-cli
pip install -r requirements.txt
python install.py
```

### Linux/Mac:
```bash
git clone https://github.com/yourusername/codemate-cli.git
cd codemate-cli
chmod +x install.sh
./install.sh
```

### Usage:
```bash
codemate
```

## 📋 Requirements

- Python 3.7+
- Internet connection (for AI features)
- Terminal/Command Prompt

## 🎯 Quick Commands

### File Operations:
- `/files` - List project files
- `/search <text>` - Search in all files
- `/run <file>` - Execute code files
- `/backup` - Create project backup

### Development Tools:
- `/debug <file>` - Analyze code for issues
- `/profile <file>` - Performance profiling
- `/test [pattern]` - Run tests
- `/git` - Git status

### Batch Operations:
- `/batch replace <old> <new>` - Replace text in all files
- `/batch rename <old> <new>` - Rename functions/classes
- `/batch create <type>` - Create project structure (flask, react, etc.)

### Integrations:
- `/cmd <command>` - Execute terminal commands
- `/preview <file>` - Preview HTML/Markdown/JSON
- `/monitor <file>` - Monitor file changes

## 💡 Examples

```bash
# Natural language commands
"Create a Flask REST API with user authentication"
"Review my Python code and suggest improvements"
"Debug the error in calculator.py"
"Show me the project structure"

# Quick commands
/search "function"
/debug app.py
/batch create flask
/run test.py
```

## 🛠️ Manual Installation

If automatic installation fails:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python cli_main.py

# Or use batch file (Windows)
codemate_local.bat
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use and modify!

## 🆘 Support

If you encounter any issues:
1. Check that Python 3.7+ is installed
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Try running locally: `python cli_main.py`

---

**Made with ❤️ for developers who love efficient coding!**
