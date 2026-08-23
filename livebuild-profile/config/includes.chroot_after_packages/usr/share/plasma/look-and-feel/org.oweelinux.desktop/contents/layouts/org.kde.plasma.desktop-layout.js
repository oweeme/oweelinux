var panel = new Panel
panel.location = "top"

// Panel fino: ~28% más bajo que el default de Plasma
// (2 * Math.floor(gridUnit * 2.5 / 2)), sin taskbar/pager abajo.
panel.height = 2 * Math.floor(gridUnit * 1.8 / 2)

panel.addWidget("org.kde.plasma.kickoff")
panel.addWidget("org.kde.plasma.panelspacer")
panel.addWidget("org.kde.plasma.digitalclock")
panel.addWidget("org.kde.plasma.panelspacer")
panel.addWidget("org.kde.plasma.systemtray")

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = 'org.kde.image';
}
