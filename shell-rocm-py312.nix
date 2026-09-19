{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (ps: [
      ps.torchWithRocm
      ps.kokoro
    ]))
  ];

  shellHook = ''
    echo "======================================"
    echo " Nix - Kokoro + ROCm + Python 3.12"
    echo " Python: $(python --version)"
    echo "======================================"
  '';
}
