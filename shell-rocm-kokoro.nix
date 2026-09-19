{ pkgs ? import <nixpkgs> {} }:

let
  py = pkgs.python313Packages;

  torchRocm = py.torchWithRocm;

  curatedTransformersRocm =
    py.curated-transformers.override {
      torch = torchRocm;
    };

  spacyCuratedTransformersRocm =
    py.spacy-curated-transformers.override {
      torch = torchRocm;
      curated-transformers = curatedTransformersRocm;
    };

  misakiRocm =
    py.misaki.override {
      torch = torchRocm;
      spacy-curated-transformers = spacyCuratedTransformersRocm;
    };

  kokoroRocm =
    py.kokoro.override {
      torch = torchRocm;
      misaki = misakiRocm;
      spacy-curated-transformers = spacyCuratedTransformersRocm;
    };

in
pkgs.mkShell {
  packages = [
    (pkgs.python313.withPackages (ps: [
      kokoroRocm
    ]))
  ];

  shellHook = ''
    echo "======================================"
    echo " Nix - Kokoro + ROCm"
    echo " Python: $(python --version)"
    echo "======================================"
  '';
}
