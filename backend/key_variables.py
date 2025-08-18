COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m", 
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m"
}

USER_COMMANDS = ["debug", "exit", "help", "reset"]

FILE_VERBS = [
    # ES
    "crear", "crea", "genera", "generar", "escribe", "escribir", "abre", "abrir",
    "edita", "editar", "modifica", "modificar", "renombra", "renombrar",
    "copia", "copiar", "mueve", "mover", "borra", "borrar", "elimina", "eliminar",
    "lista", "listar", "muestra", "mostrar", "busca", "buscar", "aplica patch", "parchea",
    "comprime", "descomprime", "inicializa", "inicializar",
    # EN
    "make", "create", "generate", "write", "open", "edit", "modify", "rename", "copy",
    "move", "delete", "remove", "list", "show", "search", "apply patch", "compress", "unzip", "init"
]

FILE_TOKENS = [
    "archivo", "carpeta", "directorio", "ruta", "workspace", "repo", "fichero",
    "file", "folder", "directory", "path", "repository", "repo",
    ".py", ".js", ".ts", ".cpp", ".c", ".h", ".java", ".json", ".md", "makefile", "requirements.txt", "package.json"
]

SHELL_TOKENS = [
    "mkdir", "rm", "mv", "cp", "ls", "cat", "pwd", "chmod", "chown", "grep", "find", "tree", "tar", "zip", "unzip"
]

CODE_TOKENS = [
    "run", "execute", "compile", "build", "test", "install", "format", "lint", "scaffold",
    "ejecuta", "corre", "compila", "construye", "prueba", "instala", "formatea", "analiza", "inicializa",
    "python", "python3", "pip", "uv", "poetry", "pipenv", "node", "npm", "yarn", "pnpm", "npx",
    "pytest", "flake8", "black", "eslint", "prettier", "tsc", "gcc", "g++", "clang", "make"
]

GIT_TOKENS = [
    "git clone", "git init", "git status", "git add", "git commit", "git push", "git pull",
    "git fetch", "git merge", "git rebase", "git checkout", "git switch", "git branch",
    "git stash", "git tag", "git log", "git reset", "git revert", "git submodule"
]

PATTERNS_STRONG = [
    r"^\s*(make|create|generate|write)\s+(a|an|un|una)?\s*(code|script|program|file|folder|directory|repo)\b",
    r"^\s*(crea|crear|genera|generar|escribe|escribir)\s+(un[ao]?|el|la)?\s*(archivo|carpeta|directorio|fichero)\b",
    r"\b(in which|what)\s+directory\s+am\s+i\b",                     # EN
    r"\b(en\s+qué|en\s+que)\s+directorio\s+estoy\b",                  # ES
    r"\b(list|show)\s+files\s+in\b|\b(lista|muestra)\s+archivos\s+en\b",
    r"\bapply\s+patch\b|\baplica(r)?\s+patch\b",
]

NEGATIVE_THEORY = [
    r"^\s*(what\s+is|qué\s+es|que\s+es)\b",
    r"^\s*(explain|explícame|explicame)\b",
    r"\bdifference\s+between\b|\bdiferencia\s+entre\b",
]

TEMPLATES = {
    "conversation": """
{instruction}

This is some information you should know: {knowledge}

Here is the conversation history: {conversation_history}

Question: {question}

Answer:
""",

    "agent": """
{instruction}

Knowledge: {knowledge}

Conversation history: {conversation_history}

Question: {question}

Answer:
"""
}
