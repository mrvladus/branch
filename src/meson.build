subdir('resources')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
	input: 'branch.py',
	output: 'branch',
	configuration: conf,
	install: true,
	install_dir: get_option('bindir')
)

branch_sources = [
	'__init__.py',
	'application.py',
	'data.py',
	'add_dialog.py',
	'repo_page.py',
	'settings.py',
	'utils.py',
]
moduledir = join_paths(pkgdatadir, meson.project_name())
install_data(branch_sources, install_dir: moduledir)
