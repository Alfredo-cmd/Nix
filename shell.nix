{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python313
    python313Packages.pip
    python313Packages.google-genai
    python313Packages.requests
    python313Packages.psutil
    python313Packages.python-dotenv
    python3Packages.requests

    pipewire
    espeak-ng
  ];
}
