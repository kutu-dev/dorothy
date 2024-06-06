# Todo
 - [ ] Pass `just check`.
 - [ ] Refactor builtin plugin.
    - [ ] Make `builtin` plugin modules private.
    - [ ] Fix imports from `dorothy`.
    - [ ] Remove code duplication at `FilesystemProvider`.
    - [ ] Check types and improve docs in RestController.
    - [ ] Remove player checks in PlaybinListener. 
    - [ ] Improve the REST API:
        - [ ] Implement queue song moving.
        - [ ] Static and non production mode for the Swagger docs.
    - [ ] Add docstring in all the project.
 
 - [ ] Make invalid config checker.
   - [ ] Don't instance the node if its config is malformed.
   - [ ] Silently add missing fields in the TOML file.
   - [ ] Check type integrity (?).
   - [ ] Add a migration system (??).

 - [ ] Cleanup `plugin_handler.py`.

- [ ] Add new features to Dorothy:
    - [ ] Logging to `stderr`.
    - [ ] Add playlist support.
    - [ ] Implement Discord box listener (???).

- [ ] Add new features to Lilim:
    - [ ] Use extra line and column.
    - [ ] Searching with `/`.
    - [ ] Match features with the REST API.
