# Release Checklist

A small checklist for turning Hermes Shadow Stats from a local prototype into a cleaner public repo.

## Before first push/update

- [x] Add install instructions
- [x] Add CLI usage examples
- [x] Add tests for core scan/render flow
- [x] Add `.gitignore`
- [x] Remove generated editable-install metadata from git
- [x] Add design notes
- [x] Add plugin prototype notes
- [x] Add SVG export mode

## Good next polish

- [ ] add screenshots or a rendered SVG example under `examples/`
- [ ] add GitHub Actions for `pytest`
- [ ] add semantic versioning / changelog policy
- [ ] add LICENSE badge / CI badge to README
- [ ] add `examples/` sample outputs for markdown, ascii, and svg
- [ ] decide whether plugin lives in this repo or a dedicated plugin repo

## Nice-to-have release items

- [ ] publish a tagged `v0.1.0`
- [ ] add a short roadmap section to README
- [ ] add one-sentence comparison vs direct Hermes core integration
- [ ] add an issue template for stat ideas / class ideas / render ideas
