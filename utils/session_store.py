"""Where each scraper keeps its saved browser session (cookies + local storage).

Session files contain live Google cookies, so they are kept out of the project
root in a git-ignored `sessions/` folder and made readable only by the current
user. Older versions wrote `<name>_state.json` to the project root; those are
moved here automatically the first time they are needed.
"""

import os
import shutil

SESSIONS_DIR = "sessions"


def _secure(path):
	try:
		os.chmod(path, 0o600)
	except OSError:
		pass  # chmod is a no-op / unsupported on some platforms (e.g. Windows)


def state_path(name):
	"""Returns the path for a scraper's session file, migrating a legacy root-level file if present."""
	os.makedirs(SESSIONS_DIR, exist_ok=True)
	try:
		os.chmod(SESSIONS_DIR, 0o700)
	except OSError:
		pass

	path = os.path.join(SESSIONS_DIR, f"{name}_state.json")
	legacy = f"{name}_state.json"

	if os.path.exists(legacy) and not os.path.exists(path):
		shutil.move(legacy, path)
		print(f"Moved saved session {legacy} -> {path}")

	if os.path.exists(path):
		_secure(path)

	return path


def secure_state_file(path):
	"""Call after the browser writes a session file to lock down its permissions."""
	if os.path.exists(path):
		_secure(path)
