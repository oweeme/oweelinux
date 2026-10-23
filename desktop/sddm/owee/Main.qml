// Inicio de sesión de OweeLinux. Solo usa QtQuick (sin Controls): ligero y sin dependencias raras.
// Se configura con theme.conf(.user): position = left|center|right · variant = full|side · background = imagen (ruta o relativa al tema) · bgcolor · accent y los textos.
import QtQuick

Rectangle {
    id: root
    width: 1280; height: 720
    color: config.bgcolor || "#102019"

    readonly property string pos: (config.position === "left" || config.position === "right") ? config.position : "center"
    readonly property bool side: config.variant === "side" && pos !== "center"
    readonly property color accent: config.accent || "#2A9D8F"
    readonly property string bgSource: {
        var b = config.background || "";
        if (b === "") return "";
        return b.charAt(0) === "/" ? "file://" + b : Qt.resolvedUrl(b);
    }
    readonly property real formW: Math.min(420, width * 0.86)
    readonly property real panelW: side ? Math.max(formW + 80, width * 0.40) : 0
    property int userIndex: Math.max(0, userModel.lastIndex)
    property int sessionIndex: Math.max(0, sessionModel.lastIndex)
    readonly property bool preview: config.preview === "1"           // vista previa desde Ajustes: no entra a ninguna sesión; Ajustes la cierra a los 16 s (Qt.quit() no cierra el saludador de SDDM) y aquí corre la cuenta atrás
    property int previewLeft: 15
    property string failure: ""
    property string sessLabel: ""
    property string faceSrc: ""
    onUserIndexChanged: updateFace()
    property var okSessions: []                      // posiciones de las sesiones que se ofrecen (OweeLinux y Plasma); el asistente, el instalador y «labwc» a pelo NUNCA: llevan a una pantalla negra o al asistente otra vez
    onSessionIndexChanged: sessLabel = sessionName()

    // ── fondo ────────────────────────────────────────────────────────────────
    Image {                                         // imagen completa, o solo la parte que deja libre el panel en el estilo «lateral»
        id: bg
        visible: root.bgSource !== ""
        y: 0; height: parent.height
        x: root.side && root.pos === "left" ? root.panelW : 0
        width: root.side ? parent.width - root.panelW : parent.width
        source: root.bgSource
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        smooth: true
    }
    Rectangle {                                     // velo para que se lea el formulario sobre cualquier foto
        anchors.fill: bg; visible: bg.visible && !root.side
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: root.pos === "left" ? "#b3000000" : (root.pos === "right" ? "#00000000" : "#66000000") }
            GradientStop { position: 0.5; color: root.pos === "center" ? "#80000000" : "#40000000" }
            GradientStop { position: 1.0; color: root.pos === "right" ? "#b3000000" : (root.pos === "left" ? "#00000000" : "#66000000") }
        }
    }
    Rectangle {                                     // panel sólido del estilo «lateral»
        visible: root.side
        y: 0; height: parent.height; width: root.panelW
        x: root.pos === "left" ? 0 : parent.width - root.panelW
        color: Qt.darker(root.color, 1.15)
    }

    // ── formulario ───────────────────────────────────────────────────────────
    Column {
        id: form
        spacing: 14
        width: root.formW
        anchors.verticalCenter: parent.verticalCenter
        x: {
            if (root.pos === "left")  return root.side ? (root.panelW - width) / 2 : Math.max(32, root.width * 0.08)
            if (root.pos === "right") return root.side ? root.width - root.panelW + (root.panelW - width) / 2 : root.width - width - Math.max(32, root.width * 0.08)
            return (root.width - width) / 2
        }

        Image {                                     // foto de perfil del usuario elegido (si no tiene o no carga, el koi del logo)
            id: face
            width: 96; height: 96; smooth: true; anchors.horizontalCenter: parent.horizontalCenter
            fillMode: Image.PreserveAspectFit; asynchronous: true
            source: root.faceSrc !== "" ? root.faceSrc : Qt.resolvedUrl("logo.png")
            onStatusChanged: if (status === Image.Error) source = Qt.resolvedUrl("logo.png")
        }
        Text {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#EFF0F1"; font.pixelSize: 56; font.weight: Font.Light
            text: Qt.formatTime(new Date(), "HH:mm")
        }
        Text {
            id: dateText
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#cfd3d4"; font.pixelSize: 16
            text: Qt.formatDate(new Date(), "dddd, d MMMM yyyy")
        }
        Timer { interval: 1000; running: true; repeat: true; onTriggered: { clock.text = Qt.formatTime(new Date(), "HH:mm"); dateText.text = Qt.formatDate(new Date(), "dddd, d MMMM yyyy") } }

        Item { width: 1; height: 6 }

        // usuario (si hay varios, se puede cambiar tocando el nombre)
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 10
            Repeater {
                id: userRepeater
                model: userModel
                onItemAdded: root.updateFace()
                delegate: Rectangle {
                    property string uname: model.name
                    property string uicon: String(model.icon)
                    visible: userModel.count === 1 ? index === root.userIndex : true
                    width: nameText.implicitWidth + 28; height: 34; radius: 17
                    color: index === root.userIndex ? root.accent : "#33ffffff"
                    Text { id: nameText; anchors.centerIn: parent; color: "#ffffff"; font.pixelSize: 15; text: model.realName !== "" ? model.realName : model.name }
                    MouseArea { anchors.fill: parent; onClicked: { root.userIndex = index; root.failure = ""; pw.forceActiveFocus() } }
                }
            }
        }

        Rectangle {                                 // campo de contraseña
            id: field
            width: parent.width; height: 48; radius: 10
            color: "#26ffffff"
            border.width: pw.activeFocus ? 2 : 1
            border.color: pw.activeFocus ? root.accent : "#55ffffff"
            Text {
                visible: pw.text.length === 0
                anchors.verticalCenter: parent.verticalCenter; x: 16
                color: "#aab0b2"; font.pixelSize: 16; text: config.password || "Contraseña"
            }
            TextInput {
                id: pw
                anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 56
                verticalAlignment: TextInput.AlignVCenter
                echoMode: TextInput.Password; passwordCharacter: "•"
                color: "#ffffff"; font.pixelSize: 18; clip: true; focus: true
                onAccepted: root.doLogin()
                Keys.onEscapePressed: { text = ""; root.failure = "" }
            }
            Rectangle {                             // botón de entrar
                width: 38; height: 38; radius: 8; color: root.accent
                anchors.right: parent.right; anchors.rightMargin: 5; anchors.verticalCenter: parent.verticalCenter
                Text { anchors.centerIn: parent; color: "#ffffff"; font.pixelSize: 22; text: "›" }
                MouseArea { anchors.fill: parent; onClicked: root.doLogin() }
            }
            SequentialAnimation on x {             // sacudida al equivocarse
                id: shake; running: false
                NumberAnimation { to: field.x - 10; duration: 50 } NumberAnimation { to: field.x + 10; duration: 80 } NumberAnimation { to: field.x; duration: 50 }
            }
        }
        Text {                                      // aviso: cómo entrar / error
            width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
            font.pixelSize: 14
            color: root.failure !== "" ? "#F06548" : "#c9cecf"
            text: root.failure !== "" ? root.failure : (config.hint || "Escribe tu contraseña y pulsa Intro")
        }
        Text {                                      // sesión (si hay más de una, tocar para cambiar)
            visible: root.okSessions.length > 1 && root.sessLabel !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#aab0b2"; font.pixelSize: 13
            text: "▾ " + root.sessLabel
            MouseArea { anchors.fill: parent; onClicked: root.sessionIndex = root.okSessions[(root.okSessions.indexOf(root.sessionIndex) + 1) % root.okSessions.length] }
        }

        Item { width: 1; height: 8 }

        Row {                                       // apagar, reiniciar, reposo
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 22
            Repeater {
                model: [ { t: config.suspend || "Reposo", ok: sddm.canSuspend, a: 0 }, { t: config.reboot || "Reiniciar", ok: sddm.canReboot, a: 1 }, { t: config.poweroff || "Apagar", ok: sddm.canPowerOff, a: 2 } ]
                delegate: Text {
                    visible: modelData.ok
                    color: ma.containsMouse ? "#ffffff" : "#c9cecf"; font.pixelSize: 14; text: modelData.t
                    MouseArea { id: ma; anchors.fill: parent; anchors.margins: -8; hoverEnabled: true; onClicked: modelData.a === 0 ? sddm.suspend() : (modelData.a === 1 ? sddm.reboot() : sddm.powerOff()) }
                }
            }
        }
    }

    // nombres por posición: se leen de los elementos del Repeater (los roles numéricos del modelo no son estables entre versiones)
    Repeater {
        id: sessionRepeater
        model: sessionModel
        delegate: Item { property string sname: model.name; property string sfile: String(model.file) }
        onItemAdded: root.pickSessions()
    }
    function pickSessions() {
        var ok = [], lite = -1;
        for (var i = 0; i < sessionRepeater.count; i++) {
            var it = sessionRepeater.itemAt(i);
            if (it && /(owee-lite|plasma|plasmax11)\.desktop$/.test(it.sfile)) { ok.push(i); if (/owee-lite\.desktop$/.test(it.sfile)) lite = i }
        }
        okSessions = ok
        if (ok.length > 0 && ok.indexOf(root.sessionIndex) < 0) root.sessionIndex = lite >= 0 ? lite : ok[0]     // la última sesión no era de las que se ofrecen: se usa OweeLinux
        sessLabel = sessionName()
    }
    function updateFace() {
        var it = userRepeater.itemAt(root.userIndex); var p = it ? it.uicon : "";
        faceSrc = (p === "" || p === "undefined") ? "" : (p.charAt(0) === "/" ? "file://" + p : p)
    }
    function userName() { var it = userRepeater.itemAt(root.userIndex); return it ? it.uname : "" }
    function sessionName() { var it = sessionRepeater.itemAt(root.sessionIndex); return it ? it.sname : "" }
    function doLogin() { if (pw.text.length === 0) return; sddm.login(userName(), pw.text, root.sessionIndex) }

    Connections {
        target: sddm
        function onLoginFailed() { root.failure = config.wrong || "Contraseña incorrecta"; pw.text = ""; shake.start(); pw.forceActiveFocus() }
    }
    Component.onCompleted: pw.forceActiveFocus()

    Rectangle {                                         // aviso de la vista previa (solo desde Ajustes → Acceso)
        visible: root.preview; z: 100
        anchors.top: parent.top; anchors.horizontalCenter: parent.horizontalCenter; anchors.topMargin: 14
        width: pvText.implicitWidth + 40; height: 42; radius: 21; color: "#E63946"
        Text { id: pvText; anchors.centerIn: parent; color: "#ffffff"; font.pixelSize: 16; font.bold: true; text: (config.previewtext || "Vista previa: se cierra sola en {0} s").replace("{0}", root.previewLeft) }
    }
    Timer { running: root.preview; repeat: true; interval: 1000; onTriggered: if (root.previewLeft > 0) root.previewLeft-- }
}
