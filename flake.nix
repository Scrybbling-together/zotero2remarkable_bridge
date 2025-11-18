{
  description = "Nix flakes";

  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
        systems.follows = "flake-utils/systems";
      };
    };

    git-hooks.url = "github:cachix/git-hooks.nix";
    treefmt-nix.url = "github:numtide/treefmt-nix";

  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      poetry2nix,
      git-hooks,
      treefmt-nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        p2n = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };

        zot_x_rm = p2n.mkPoetryApplication {
          buildInputs = [ pkgs.inkscape ];

          projectDir = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type: true;
          };
          preferWheels = true;
          overrides = p2n.overrides.withDefaults (
            final: prev: {
              remarks = prev.remarks.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ];
              });
              rmc = prev.rmc.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ];
              });
            }
          );
        };
        treefmtEval = treefmt-nix.lib.evalModule pkgs ./treefmt.nix;
      in
      {
        formatter =
          let
            config = self.checks.${system}.pre-commit-check.config;
            inherit (config) package configFile;
            script = ''
              ${pkgs.lib.getExe package} run --all-files --config ${configFile}
            '';
          in
          pkgs.writeShellScriptBin "pre-commit-run" script;
        checks = {
          pre-commit-check = git-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              treefmt = {
                enable = true;
                name = "treefmt";
                description = "Format all files with treefmt";
                entry = "${pkgs.lib.getExe treefmtEval.config.build.wrapper} --fail-on-change";
                pass_filenames = false;
                stages = [ "pre-commit" ];
              };
            };
          };
          formatting = treefmtEval.${system}.config.build.check self;
        };
        devShells.default =
          let
            inherit (self.checks.${system}.pre-commit-check) shellHook enabledPackages;
          in
          pkgs.mkShell {
            inherit shellHook;
            buildInputs = [
              pkgs.rmapi
              pkgs.poetry
              pkgs.zotero
              zot_x_rm

              treefmtEval.config.build.wrapper
            ] ++ enabledPackages;
          };
        packages.default = zot_x_rm;
      }
    );
}
