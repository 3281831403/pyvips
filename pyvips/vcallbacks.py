# record exceptions raised by user callbacks

# libvips calls back into Python (custom source/target and progress callbacks)
# through cffi callbacks. When one of those user callbacks raises an
# exception, cffi swallows it and returns a default value to libvips, so the
# caller never sees the real error -- it just gets a truncated image or a
# silent success. We catch the exception inside the marshalers, store it here,
# and re-raise it in the top-level call once libvips has unwound.

_callback_error = None


def set_callback_error(exc):
    """Record an exception raised by a callback.

    The first exception wins: once a callback has failed we keep returning an
    error to libvips, and later callbacks may raise again during unwinding.
    """
    global _callback_error
    if _callback_error is None:
        _callback_error = exc


def check_callback_error():
    """Re-raise any callback exception, then clear it.

    Call this after a libvips call that may have triggered callbacks. If a
    callback raised, the original exception (with its original type and
    message) is raised here.
    """
    global _callback_error
    if _callback_error is not None:
        exc = _callback_error
        _callback_error = None

        # the callback failure will usually have left a libvips error behind,
        # clear it so the next image is not polluted
        from pyvips import vips_lib
        vips_lib.vips_error_clear()

        raise exc
