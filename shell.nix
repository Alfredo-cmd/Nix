{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    # Python principal
    python313
    python313Packages.pip

    # Dependências do Nix
    python313Packages.google-genai
    python313Packages.requests
    python313Packages.psutil
    python313Packages.python-dotenv
    python313Packages.soundfile

    # Áudio / voz
    pipewire
    espeak-ng
    ffmpeg
    sox

    # Bibliotecas nativas
    stdenv.cc.cc
		zlib

    # Utilitários
    git
  ];

  shellHook = ''
		export PYTHONNOUSERSITE=1
		export PYTHONPATH=""
		export HF_HOME="$PWD/.hf-cache"
		export HF_HUB_DISABLE_TELEMETRY=1
		export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
		export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH"

		echo "======================================"
		echo " Nix - ambiente principal"
		echo " Python: $(python --version)"
		echo "======================================"
	'';
}