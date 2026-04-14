# Hermes Plugin Prototype

This repository now includes a prototype Hermes plugin wrapper under:

- `hermes_plugin/plugin.yaml`
- `hermes_plugin/__init__.py`

## Goal

Prove that Hermes Shadow Stats can be wrapped as a Hermes plugin without requiring a core patch.

## Current behavior

The prototype registers a Hermes CLI command:

- `hermes shadow-stats --home ~/.hermes --name Hermes`

Internally it:

1. scans the target Hermes home
2. builds the derived character profile
3. returns the markdown status window

## Installation sketch

Copy or symlink the folder into your Hermes user plugin directory:

```bash
mkdir -p ~/.hermes/plugins/shadow-stats
cp -R hermes_plugin/* ~/.hermes/plugins/shadow-stats/
```

or symlink it during development:

```bash
mkdir -p ~/.hermes/plugins/shadow-stats
ln -s ~/Code/Hermes-Shadow-Stats/hermes_plugin/plugin.yaml ~/.hermes/plugins/shadow-stats/plugin.yaml
ln -s ~/Code/Hermes-Shadow-Stats/hermes_plugin/__init__.py ~/.hermes/plugins/shadow-stats/__init__.py
```

## Why keep it minimal

The current plugin wrapper avoids assumptions about Hermes runtime internals.

That makes it useful as a bridge step:

- today: read-only command wrapper
- next: richer plugin command UX
- later: hook-based growth journal and live progression
