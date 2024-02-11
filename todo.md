# Todo
## Next
Remember that this is an indicative, and you shouldn't use it as the only reference when developing.

- [ ] Refine the REST API
- - [ ] Split play and resume and make `play_from_queue_given_index` work in the TUI.
  - [ ] Improve the summary of play_pause
  - [ ] Implement queue song moving
- [ ] Make a fully working queue frontend with the TUI
  - [ ] Implement all the endpoints from the API
  - [ ] Improve keybindings
- [ ] Scan and rescan function in any provider

---

## Quirks
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
