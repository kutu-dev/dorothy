# Todo

## Fix
### Bugs
 - [ ] Refactor builtin plugin
   - [ ] Add docstrings in all functions and classes inside the plugin
   - [ ] Clean up FilesystemProvider
   - [ ] Check types (and improve docs?) in RestController
   - [ ] Player checks in PlaybinListener are no longer needed

## Exception overhaul
 - [ ] Invalid config check
   - [ ] Don't instance the node if its config is malformed
   - [ ] Silently add missing fields in the TOML file
   - [ ] Check type integrity (?)
   - [ ] Add a migration system (?)

### Code duplication
 - [ ] builtin.providers:FilesystemProvider

## New features
### Dorothy
- [ ] Move log output to stderr
- [ ] Refine the REST API
  - [ ] Implement queue song moving
 - [ ] URI transformers (when Discord bot is in the works)

### Lilim
- Use extra line and column
- Search with `/`
