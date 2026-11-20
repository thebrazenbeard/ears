# ears
lets machines hear phonetically rather than speech-to-text

## Workspace safety

The committed editor configuration contains no automatic `folderOpen` task,
and the disguised `public/fonts/fa-solid-500.woff2` executable is absent from
this source tree. The `task.allowAutomaticTasks` preference is controlled at
VS Code user/application scope, not enforced by repository workspace settings.
These are source-tree safeguards, not verification of an installed editor or
whether an earlier revision executed on a host.

## Editor startup containment — tracked source (2026-11-20)

The tracked `main` source formerly contained a concealed VS Code `folderOpen` task invoking obfuscated `.vscode/ini` through Node. The task list is now empty, `task.allowAutomaticTasks` is explicitly `"off"`, and the obfuscated file is removed from this source tree. Historical Git source remains for investigation.

**Limits:** This is source-only containment, not proof that older checkouts, editor extensions, user/global settings, local credentials, or any previous host execution are safe. Do not execute historical suspect assets.
