import os
import subprocess
from typing import Callable
from gi.repository import Adw, Gtk, Gio
from gettext import gettext as _


from .data import data
from .settings import get_settings
from .utils import Spinner, show_toast, show_message, threaded, threaded_callback


@Gtk.Template(resource_path="/com/github/mrvladus/branch/repo.ui")
class RepoPage(Adw.PreferencesPage):
    __gtype_name__ = "RepoPage"

    push_btn = Gtk.Template.Child()
    commit_msg = Gtk.Template.Child()
    branches_row = Gtk.Template.Child()
    merge_row = Gtk.Template.Child()

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.update_branches_row()
        self.update_merge_row()

    def update_branches_row(self) -> None:
        self.get_branches()
        self.branches_row.props.title = self.branches_list[0]
        if len(self.branches_list) == 1:
            return
        self.branches_rows = []
        for branch in self.branches_list:
            btn = Gtk.Button(
                icon_name="object-select-symbolic", valign=Gtk.Align.CENTER
            )
            row = Adw.ActionRow(title=branch, activatable_widget=btn)
            row.add_suffix(btn)
            self.branches_rows.append(row)
            btn.connect("clicked", self.on_branch_changed, row)
            if branch != self.current_branch:
                self.branches_row.add_row(row)

    def clear_branches_row(self):
        for i in range(1, len(self.branches_rows)):
            self.branches_row.remove(self.branches_rows[i])
        self.branches_rows.clear()

    def get_branches(self):
        """
        Get all branches.
        """
        self.branches_list = (
            subprocess.getoutput(f"cd {self.path} && LANG=C git branch")
            .replace(" ", "")
            .splitlines()
        )
        for branch in self.branches_list:
            if branch.startswith("*"):
                self.branches_list.insert(
                    0, self.branches_list.pop(self.branches_list.index(branch))
                )
                self.branches_list[0] = branch.lstrip("*")
        # Set current branch
        self.current_branch = self.branches_list[0]

    def on_branch_changed(self, btn, row) -> None:
        """
        Commit changes and change branch.
        """
        settings = get_settings()
        if settings["email"] == "":
            show_toast(_("Email is not set"))
            return
        if settings["name"] == "":
            show_toast(_("Name is not set"))
            return
        self.current_branch = row.props.title
        self.branches_row.props.expanded = False
        self.branches_row.props.title = row.props.title
        subprocess.getoutput(
            f"cd {self.path} && git add -A && git -c user.name='{settings['name']}' -c user.email='{settings['email']}' commit -a --allow-empty-message -m ''"
        )
        out = subprocess.getoutput(
            f"cd {self.path} && git checkout {self.current_branch}"
        )
        self.clear_merge_row()
        self.update_merge_row()
        self.clear_branches_row()
        self.update_branches_row()
        show_message(out)

    def update_merge_row(self):
        """
        Fills merge expander row.
        """
        self.get_branches()
        # Hide button if branch is only one
        if len(self.branches_list) == 1:
            self.merge_row.props.visible = False
            return
        # Action rows list
        self.merge_rows = []
        # Add merge row for each branch
        for i in range(1, len(self.branches_list)):
            btn = Gtk.Button(
                icon_name="object-select-symbolic", valign=Gtk.Align.CENTER
            )
            btn.connect("clicked", self.on_merge, self.branches_list[i])
            row = Adw.ActionRow(title=self.branches_list[i], activatable_widget=btn)
            row.add_suffix(btn)
            self.merge_row.add_row(row)
            self.merge_rows.append(row)

    def clear_merge_row(self):
        """
        Remove all rows from merge row.
        """
        for row in self.merge_rows:
            self.merge_row.remove(row)
        self.merge_rows.clear()

    def on_merge(self, btn: Gtk.Button, branch: str) -> None:
        """
        Merge branches.
        """
        self.merge_row.props.expanded = False
        # Commit
        settings = get_settings()
        if settings["email"] == "":
            show_toast(_("Email is not set"))
            return
        if settings["name"] == "":
            show_toast(_("Name is not set"))
            return
        self.merge_row.props.sensitive = False
        self.merge_start(settings, branch)

    @threaded
    def merge_start(self, settings: dict, branch: str):
        subprocess.getoutput(
            f"cd {self.path} && git add -A && git -c user.name='{settings['name']}' -c user.email='{settings['email']}' commit -m '{_('Merge with')} {branch}'"
        )
        # Merge
        out = subprocess.getoutput(f"cd {self.path} && git merge {branch}")
        threaded_callback(self.merge_end, out)

    def merge_end(self, msg):
        self.merge_row.props.sensitive = True
        show_message(msg)

    @Gtk.Template.Callback()
    def on_commit_btn_clicked(self, btn: Gtk.Button) -> None:
        """
        Commit changes.
        """
        settings = get_settings()
        if settings["email"] == "":
            show_toast(_("Email is not set"))
            return
        if settings["name"] == "":
            show_toast(_("Name is not set"))
            return
        out = subprocess.getoutput(
            f"cd {self.path} && git add -A && git -c user.name='{settings['name']}' -c user.email='{settings['email']}' commit -m '{self.commit_msg.props.text}'"
        )
        show_message(out)
        # Set widgets state
        self.commit_msg.props.text = ""

    @Gtk.Template.Callback()
    def on_push_btn_clicked(self, btn: Gtk.Button) -> None:
        """
        Push to origin. Calls push_start() in thread.
        """
        settings = get_settings()
        if settings["github_username"] == "":
            show_toast(_("GitHub username is not set"))
            return
        if settings["github_token"] == "":
            show_toast(_("Token is not set"))
            return
        origin = subprocess.getoutput(
            f"cd {self.path} && git config --get remote.origin.url"
        )
        if "github" not in origin:
            show_toast(_("Must be a GitHub repo to push"))
            return
        btn.props.sensitive = False
        self.push_start(origin, settings)

    @threaded
    def push_start(self, origin: str, settings: dict) -> None:
        """
        Push changes.
        """
        out = subprocess.getoutput(
            f"cd {self.path} && git push https://{settings['github_token']}@{origin.split('https://')[1]}"
        )
        threaded_callback(self.push_end, out)

    def push_end(self, out) -> None:
        """
        Called when push completed.
        """
        show_message(out)
        self.push_btn.props.sensitive = True

    def delete(self) -> None:
        """
        Remove line from repo file.
        """
        with open(data["repo_file"], "r") as f:
            lines = f.readlines()
        with open(data["repo_file"], "w") as f:
            for line in lines:
                if self.path not in line:
                    f.write(line)
