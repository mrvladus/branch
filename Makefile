all: run

clean:
	rm -rf .build/ .flatpak-builder/

run:
	meson .build --prefix=/usr
	sudo ninja -C .build install
	branch
	sudo ninja -C .build uninstall

install:
	meson .build --prefix=/usr
	sudo ninja -C .build install

uninstall:
	sudo ninja -C .build uninstall

flatpak_build:
	flatpak-builder .build com.github.mrvladus.Branch.json --force-clean --install --user

flatpak_run:
	flatpak run com.github.mrvladus.Branch