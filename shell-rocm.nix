{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python313.withPackages (ps: [
      ps.torchWithRocm
      ps.pip
    ]))

    pkgs.rocmPackages.rocminfo
  ];

  shellHook = ''
    echo "======================================"
    echo " Nix - teste ROCm"
    echo " Python: $(python --version)"
    echo "======================================"
  '';
}
