class PermissionManager:

    SAFE = "safe"
    CONFIRM = "confirm"
    BLOCKED = "blocked"

    def __init__(self):
        self.permissions = {
            "get_system_info": self.SAFE,
            "list_directory": self.SAFE,
            "list_directory_recursive": self.SAFE,
            "read_file": self.SAFE,
            "write_file": self.CONFIRM,
        }

        self.session_allowed = set()

    def get_permission(self, tool_name):
        if tool_name in self.session_allowed:
            return self.SAFE

        return self.permissions.get(
            tool_name,
            self.CONFIRM
        )

    def grant_for_session(self, tool_name):
        self.session_allowed.add(tool_name)

    def revoke_for_session(self, tool_name):
        self.session_allowed.discard(tool_name)
