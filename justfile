# Merkato build helpers

set shell := ["bash", "-cu"]

# Default: run tests and a release build
all: test build-release

# Run cargo tests
test:
    cargo test

# Run a local release build
cargo-release:
    cargo build --release

# Configure meson build directory
meson-setup:
    meson setup _build

# Build with meson (used by Flatpak)
meson-build: meson-setup
    ninja -C _build

# Run the app locally via cargo
cargo-run:
    cargo run --release

# Generate Flatpak cargo-sources.json from Cargo.lock
flatpak-cargo-sources:
    #!/usr/bin/env bash
    set -euo pipefail
    TOOLS_DIR="${FLATPAK_BUILDER_TOOLS:-$HOME/.local/share/flatpak-builder-tools}"
    if [ ! -d "$TOOLS_DIR/cargo" ]; then
        echo "Cloning flatpak-builder-tools..."
        git clone https://github.com/flatpak/flatpak-builder-tools.git "$TOOLS_DIR"
    fi
    python3 "$TOOLS_DIR/cargo/flatpak-cargo-generator.py" Cargo.lock -o cargo-sources.json

# Build the Flatpak locally (requires org.gnome.Sdk//49 and rust-stable)
flatpak-build:
    flatpak-builder --force-clean --repo=flatpak-repo flatpak-build com.ekonomikas.merkato.json

# Clean build artifacts
clean:
    rm -rf _build target flatpak-build flatpak-repo
