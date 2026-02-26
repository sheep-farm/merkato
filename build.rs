// build.rs
// Compiles Blueprint UI files and GLib resources at build time.

use std::path::Path;
use std::process::Command;

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let src_dir = format!("{}/src", manifest_dir);
    let blp_dir = format!("{}/blp", src_dir);

    // Compile Blueprint files to UI XML
    let blueprints = ["window", "list_stock", "search_stock", "alert_dialog", "alerts_view"];

    for name in &blueprints {
        let blp_path = format!("{}/{}.blp", blp_dir, name);
        let ui_path = format!("{}/{}.ui", blp_dir, name);

        println!("cargo:rerun-if-changed={}", blp_path);

        if Path::new(&blp_path).exists() {
            let output = Command::new("blueprint-compiler")
                .args(["compile", "--output", &ui_path, &blp_path])
                .output()
                .expect(
                    "Failed to run blueprint-compiler. Please install it:\n  \
                     pip install blueprint-compiler\n  or\n  \
                     flatpak install org.gnome.Platform.Compat.i386//45",
                );

            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                panic!("Blueprint compilation failed for {name}: {stderr}");
            }
        }
    }

    // Compile GLib Resource bundle
    println!("cargo:rerun-if-changed={}/merkato.gresource.xml", src_dir);
    println!("cargo:rerun-if-changed={}/style.css", src_dir);
    println!("cargo:rerun-if-changed={}/gtk/help-overlay.ui", src_dir);

    let gresource_xml = format!("{}/merkato.gresource.xml", src_dir);
    let gresource_out = format!("{}/merkato.gresource", src_dir);

    if Path::new(&gresource_xml).exists() {
        let output = Command::new("glib-compile-resources")
            .current_dir(&src_dir)
            .args([
                "merkato.gresource.xml",
                &format!("--target={}", gresource_out),
                "--sourcedir=.",
                "--sourcedir=blp",
            ])
            .output()
            .expect("Failed to run glib-compile-resources. Please install glib2-tools.");

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            panic!("GResource compilation failed: {stderr}");
        }
    }
}
