#!@PYTHON@
import os, gi, sys, signal, locale, gettext

gi.require_version("Adw", "1")

pkgdatadir = "@pkgdatadir@"
localedir = "@localedir@"

sys.path.insert(1, pkgdatadir)
signal.signal(signal.SIGINT, signal.SIG_DFL)
locale.bindtextdomain("branch", localedir)
locale.textdomain("branch")
gettext.install("branch", localedir)

if __name__ == "__main__":
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(pkgdatadir, "branch.gresource"))
    resource._register()

    from branch import application

    sys.exit(application.main())
