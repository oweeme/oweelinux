use gtk4 as gtk;
use gtk::prelude::*;
use gtk::glib;
fn report(tag: &str) {
    let t = std::fs::read_to_string("/proc/self/smaps_rollup").unwrap();
    let g = |k: &str| -> f64 { t.lines().find(|l| l.starts_with(k)).and_then(|l| l.split_whitespace().nth(1)).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) / 1024.0 };
    println!("RESULT {}: Rss={:.0} Pss={:.0} USS={:.0} MB", tag, g("Rss:"), g("Pss:"), g("Private_Clean:") + g("Private_Dirty:"));
}
fn main() {
    let app = gtk::Application::builder().application_id("org.t.rs").build();
    app.connect_activate(|a| {
        let w = gtk::ApplicationWindow::builder().application(a).default_width(300).default_height(40).child(&gtk::Label::new(Some("hola"))).build();
        w.present();
        let a2 = a.clone();
        glib::timeout_add_seconds_local(6, move || { report("rust-gtk4-rs"); a2.quit(); glib::ControlFlow::Break });
    });
    app.run();
}
