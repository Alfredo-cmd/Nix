{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
    ffmpeg
    sox
    git
    stdenv.cc.cc
  ];

  shellHook = ''
    export PYTHONNOUSERSITE=1
    export HF_HOME="$PWD/.hf-cache"
    export HF_HUB_DISABLE_TELEMETRY=1

    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"

    echo "======================================"
    echo " Qwen3-TTS 0.6B - ambiente de teste"
    echo " Python: $(python --version)"
    echo "======================================"
  '';
}