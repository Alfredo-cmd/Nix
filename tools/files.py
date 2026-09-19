from pathlib import Path


def list_directory(path: str):
    """Lista arquivos e pastas de um diretório."""

    directory = Path(path).expanduser().resolve()

    if not directory.exists():
        return {"erro": f"O caminho não existe: {directory}"}

    if not directory.is_dir():
        return {"erro": f"O caminho não é um diretório: {directory}"}

    items = []

    try:
        for item in sorted(
            directory.iterdir(),
            key=lambda p: p.name.lower()
        ):
            items.append({
                "nome": item.name,
                "tipo": "pasta" if item.is_dir() else "arquivo"
            })
    except PermissionError:
        return {"erro": f"Permissão negada para acessar: {directory}"}

    return {
        "caminho": str(directory),
        "itens": items
    }


def list_directory_recursive(
    path: str,
    max_depth: int = 3,
    max_items: int = 200
):
    """Lista recursivamente arquivos e pastas."""

    directory = Path(path).expanduser().resolve()

    if not directory.exists():
        return {"erro": f"O caminho não existe: {directory}"}

    if not directory.is_dir():
        return {"erro": f"O caminho não é um diretório: {directory}"}

    max_depth = max(0, min(max_depth, 3))
    max_items = max(1, min(max_items, 500))

    items = []
    truncated = False

    def scan(current_path: Path, depth: int):
        nonlocal truncated

        if depth > max_depth or truncated:
            return

        try:
            children = sorted(
                current_path.iterdir(),
                key=lambda p: p.name.lower()
            )
        except PermissionError:
            items.append({
                "caminho": str(current_path),
                "erro": "Permissão negada"
            })
            return

        for child in children:
            if len(items) >= max_items:
                truncated = True
                return

            relative_path = child.relative_to(directory)

            items.append({
                "caminho": str(relative_path),
                "tipo": "pasta" if child.is_dir() else "arquivo"
            })

            if child.is_dir():
                scan(child, depth + 1)

    scan(directory, 0)

    return {
        "caminho": str(directory),
        "profundidade_maxima": max_depth,
        "total_itens": len(items),
        "limitado": truncated,
        "itens": items
    }


def read_file(path: str, max_chars: int = 20000):
    """Lê o conteúdo de um arquivo de texto."""

    file_path = Path(path).expanduser().resolve()

    if not file_path.exists():
        return {"erro": f"O arquivo não existe: {file_path}"}

    if not file_path.is_file():
        return {"erro": f"O caminho não é um arquivo: {file_path}"}

    max_chars = max(1, min(max_chars, 50000))

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            content = file.read(max_chars + 1)

    except PermissionError:
        return {"erro": f"Permissão negada para ler: {file_path}"}

    except UnicodeDecodeError:
        return {
            "erro": (
                "O arquivo não parece ser um arquivo de texto UTF-8: "
                f"{file_path}"
            )
        }

    except OSError as error:
        return {"erro": f"Não foi possível ler o arquivo: {error}"}

    truncated = len(content) > max_chars

    if truncated:
        content = content[:max_chars]

    return {
        "caminho": str(file_path),
        "conteudo": content,
        "limitado": truncated,
        "limite_caracteres": max_chars
    }


def write_file(path: str, content: str):
    """Cria ou substitui um arquivo dentro da pasta pessoal do usuário."""

    file_path = Path(path).expanduser().resolve()
    home = Path.home().resolve()

    try:
        file_path.relative_to(home)
    except ValueError:
        return {
            "erro": (
                "Por segurança, write_file só pode modificar "
                "arquivos dentro da pasta pessoal do usuário."
            )
        }

    if file_path.exists() and file_path.is_dir():
        return {
            "erro": f"O caminho é uma pasta, não um arquivo: {file_path}"
        }

    try:
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

    except PermissionError:
        return {
            "erro": f"Permissão negada para escrever: {file_path}"
        }

    except OSError as error:
        return {
            "erro": f"Não foi possível escrever o arquivo: {error}"
        }

    return {
        "sucesso": True,
        "caminho": str(file_path),
        "caracteres_escritos": len(content)
    }
