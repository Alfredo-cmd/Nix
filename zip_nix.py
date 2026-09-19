from pathlib import Path
import zipfile

ROOT = Path.cwd()
OUTPUT = ROOT.parent / "Nix-para-analise.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".qwen-venv",
    ".hf-cache",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".wav",
    ".mp3",
    ".ogg",
    ".flac",
    ".mp4",
    ".zip",
}

EXCLUDE_FILES = {
    ".env",
}

with zipfile.ZipFile(
    OUTPUT,
    "w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as zf:

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        if any(part in EXCLUDE_DIRS for part in relative.parts):
            continue

        if path.name in EXCLUDE_FILES:
            continue

        if path.suffix.lower() in EXCLUDE_EXTENSIONS:
            continue

        zf.write(path, relative)

print()
print("======================================")
print("      ZIP DO NIX CRIADO")
print("======================================")
print(f"Arquivo: {OUTPUT}")
print(f"Tamanho: {OUTPUT.stat().st_size / 1024 / 1024:.2f} MB")
print()
print("Excluídos:")
print("  .git / ambientes virtuais / cache")
print("  arquivos .env")
print("  áudios e arquivos pesados")
print("======================================")
