{ pkgs, ... }:
{
  projectRootFile = "flake.nix";
  programs = {
    nixfmt.enable = true;
    black.enable = true;
    mypy = {
      enable = false;
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
