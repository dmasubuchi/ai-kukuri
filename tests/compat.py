"""Platform capabilities used to skip POSIX-only tests."""
import os
import tempfile

IS_WINDOWS = os.name == 'nt'


def _can_symlink():
    with tempfile.TemporaryDirectory() as d:
        try:
            os.symlink(d, os.path.join(d, 'link'), target_is_directory=True)
        except (OSError, NotImplementedError, AttributeError):
            return False
    return True


CAN_SYMLINK = _can_symlink()
