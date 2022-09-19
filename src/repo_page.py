import os
import subprocess
from typing import Callable
from gi.repository import Adw, Gtk, Gio
from gettext import gettext as _


from .data import data
from .settings import get_settings
from .utils import Spinner, show_toast, show_message, threaded, threaded_callback


@Gtk.Template(resource_path="/com/github/mrvladus/branch/repo.ui")
class RepoPage(Adw.PreferencesGroup):
    __gtype_name__ = "RepoPage"

    push_btn = Gtk.Template.Child()
    commit_msg = Gtk.Template.Child()
    branches = Gtk.Template.Child()
    merge_row = Gtk.Template.Child()

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.props.description += self.path
        self.init_branches()
        self.update_merge_row()

    def init_branches(self) -> None:
        """
        Add list button as suffix to the branch row.
        Create label instead of list button if branch is only one.
        """
        self.get_branches()
        if len(self.branches_list) == 1:
            self.branch_list_btn = Gtk.Label(label=self.current_branch)
            self.branches.props.subtitle = ""
        else:
            self.branch_list_btn = Gtk.ComboBoxText(valign=Gtk.Align.CENTER)
            # Add branches to list button
            for branch in self.branches_list:
                self.branch_list_btn.append_text(branch)
            # Set current branch active
            self.branch_list_btn.set_active(0)
            self.branch_list_btn.connect("popup", self.on_branch_popup)
            self.branch_list_btn.connect("changed", self.on_branch_changed)
        self.branches.add_suffix(self.branch_list_btn)

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

    def on_branch_popup(self, widget: Gtk.ComboBoxText):
        """
        Remember previously active branch.
        """
        self.prev_branch = widget.get_active_text()
        self.prev_branch_id = widget.get_active_id()

    def on_branch_changed(self, widget: Gtk.ComboBoxText) -> None:
        """
        Commit changes and change branch.
        """
        self.current_branch = widget.get_active_text()
        settings = get_settings()
        if settings["email"] == "":
            show_toast(_("Email is not set"))
            widget.set_active_id(self.prev_branch_id)
            return
        if settings["name"] == "":
            show_toast(_("Name is not set"))
            widget.set_active_id(self.prev_branch_id)
            return
        subprocess.getoutput(
            f"cd {self.path} && git add -A && git -c user.name='{settings['name']}' -c user.email='{settings['email']}' commit -a --allow-empty-message -m ''"
        )
        out = subprocess.getoutput(
            f"cd {self.path} && git checkout {self.current_branch}"
        )
        self.clear_merge_row()
        self.update_merge_row()
        show_message(out)

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
