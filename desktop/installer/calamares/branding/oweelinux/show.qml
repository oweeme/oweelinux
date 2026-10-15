import QtQuick 2.0
import calamares.slideshow 1.0

// Una sola diapositiva, sin animaciones: lo que ve quien espera mientras se copia el sistema.
Presentation {
    id: presentation
    Slide {
        Rectangle { anchors.fill: parent; color: "#102019" }
        Image { id: logo; source: "owee-logo.png"; width: 120; height: 120; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: parent.height / 5 }
        Text { anchors.top: logo.bottom; anchors.topMargin: 24; anchors.horizontalCenter: parent.horizontalCenter; color: "#EFF0F1"; font.pixelSize: 26; text: "OweeLinux" }
        Text { anchors.top: logo.bottom; anchors.topMargin: 72; anchors.horizontalCenter: parent.horizontalCenter; color: "#9fb3aa"; font.pixelSize: 15
               text: "Instalando… Al reiniciar crearás tu usuario." }
    }
}
