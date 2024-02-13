# Todo
## Next
Remember that this is an indicative, and you shouldn't use it as the only reference when developing.

- [ ] Clean up and refine the FilesystemProvider code to make it compatible with artists filtering and more metadata data
- [ ] Refine the REST API
  - [ ] Improve the summary of play_pause
  - [ ] Implement queue song moving
- [ ] Scan and rescan function in any provider

---

## Quirks
 - [ ] Terminal breaks on exit or crash of `lilim`
 - [ ] Disable is not working
 - [ ] LOGGER OUTPUT TO STDERR(?)
 - [ ] DISABLE COLOR IN PIPING
 - [ ] Fix circular import in nodes and models and add converting string to Resource type
 - [ ] Reduce duplicated code in
 - [ ] URI transformers (when Discord bot is in the works)

---

## Code duplication
 - [ ] Resource id duplicated type
- [ ] PluginHandler
- [ ] Orchestrator
- [ ] builtin.providers:FilesystemProvider

---

## Exception overhaul
 - [ ] Invalid config checker
 - [ ] When a Exception occurs loading a plugin
 - [ ] When cleanup instead of return bool (?)
