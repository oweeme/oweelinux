#include <gtk/gtk.h>
#include <stdio.h>
#include <string.h>
static void report(const char *tag) {
  FILE *f = fopen("/proc/self/smaps_rollup", "r"); char line[256]; double rss=0,pss=0,pc=0,pd=0; if(!f) return;
  while (fgets(line, sizeof line, f)) { double v; if (sscanf(line, "Rss: %lf", &v)==1) rss=v; else if (sscanf(line, "Pss: %lf", &v)==1) pss=v;
    else if (sscanf(line, "Private_Clean: %lf", &v)==1) pc=v; else if (sscanf(line, "Private_Dirty: %lf", &v)==1) pd=v; }
  fclose(f); printf("RESULT %s: Rss=%.0f Pss=%.0f USS=%.0f MB\n", tag, rss/1024, pss/1024, (pc+pd)/1024); fflush(stdout);
}
static gboolean done(gpointer app) { report("c-gtk4"); g_application_quit(G_APPLICATION(app)); return FALSE; }
static void activate(GtkApplication *app, gpointer d) {
  GtkWidget *w = gtk_application_window_new(app); gtk_window_set_default_size(GTK_WINDOW(w), 300, 40);
  gtk_window_set_child(GTK_WINDOW(w), gtk_label_new("hola")); gtk_window_present(GTK_WINDOW(w)); g_timeout_add_seconds(6, done, app);
}
int main(int argc, char **argv) { GtkApplication *app = gtk_application_new("org.t.c", 0); g_signal_connect(app, "activate", G_CALLBACK(activate), NULL); int s = g_application_run(G_APPLICATION(app), argc, argv); return s; }
