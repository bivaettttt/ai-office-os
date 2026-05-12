# Legacy Tools

These tools are legacy helpers used by old agent endpoints.

`shell_tool.py` executes shell commands through `subprocess` and must not be used
by new autonomous agent runtime code without explicit permissions, sandboxing,
allowlists, and audit logging.

`file_tool.py` and `project_tool.py` can write files and create project
structure. Keep them out of new execution flows until a capability and permission
model exists.
