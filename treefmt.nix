{ pkgs, ... }:
{
  projectRootFile = "flake.nix";
  programs = {
    nixfmt.enable = true;
    black.enable = true;
    mypy = {
      enable = true;
      directories = {
        src = {
          directory = "zrm";
          extraPythonPackages = with pkgs.python3Packages; [
            types-pyyaml
            types-tqdm
          ];
        };
      };
    };
  };
}
