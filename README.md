![Self-Enhancing AI Logo](assets/logo.png)

# 🧠 Self-Enhancing AI Codebase (v0.01)

> Ein experimentelles Framework zur Erforschung der KI-gesteuerten Codeoptimierung

## 🚀 Projektübersicht

Das Self-Enhancing AI Codebase Projekt (Version 0.01) ist ein innovatives Experiment, das künstliche Intelligenz nutzt, um autonom seinen eigenen Quellcode zu verbessern und zu erweitern. Dieses System verwendet fortschrittliche Sprachmodelle, um Code zu analysieren, Verbesserungen vorzuschlagen, umzusetzen und zu überprüfen, und schafft so ein sich selbst entwickelndes Software-Ökosystem.

## ✨ Hauptfunktionen

1. **🤖 Autonome Verbesserung**: Das System kann eigenständig Verbesserungsideen generieren, bewerten und implementieren.
2. **👥 Multi-Agent-Architektur**: Nutzt separate Agenten für Codegenerierung und Kontrolle/Überprüfung.
3. **🎛️ Interaktive Benutzerkontrolle**: Ermöglicht Benutzern, vorgeschlagene Änderungen zu genehmigen, zu testen oder zu verwerfen.
4. **🔄 Versionskontrolle-Integration**: Arbeitet nahtlos mit Git für das Änderungsmanagement.
5. **💰 Kostenüberwachung**: Überwacht und berichtet über API-Nutzung und damit verbundene Kosten.

## 🏗️ Systemarchitektur

![Systemarchitektur Diagramm](assets/0_01_flowchart_self_enhancer.png)

Das Projekt besteht aus mehreren Schlüsselkomponenten:

- **CodeAgent**: Verantwortlich für die Generierung von Verbesserungsideen, Planung von Implementierungen und Vorschlagen von Codeänderungen.
- **ControllingAgent**: Bewertet Ideen, überprüft Implementierungen und gewährleistet die Qualitätskontrolle.
- **Enhancer**: Der Hauptorchestrator, der die Verbesserungszyklen und Benutzerinteraktionen verwaltet.

## 🔄 Verbesserungsprozess

1. **💡 Ideengenerierung**: Das System analysiert den aktuellen Codebase und schlägt potenzielle Verbesserungen vor.
2. **⚖️ Ideenbewertung**: Ideen werden basierend auf ihrer potenziellen Auswirkung und Machbarkeit bewertet.
3. **📝 Implementierungsplanung**: Für jede ausgewählte Idee wird ein schrittweiser Plan erstellt.
4. **🛠️ Codemodifikation**: Das System schlägt spezifische Codeänderungen vor, um jeden Schritt umzusetzen.
5. **🔍 Überprüfung und Iteration**: Vorgeschlagene Änderungen werden überprüft, möglicherweise modifiziert und iteriert, bis sie zufriedenstellend sind.
6. **👍 Benutzergenehmigung**: Benutzer können wählen, ob sie Änderungen testen, direkt anwenden oder verwerfen möchten.

## 🚀 Erste Schritte

1. Klonen Sie das Repository
2. Installieren Sie die Abhängigkeiten: `pip install -r requirements.txt`
3. Richten Sie Ihren OpenAI API-Schlüssel in einer `.env`-Datei ein
4. Führen Sie den Enhancer aus: `python enhancer.py`

## ⚙️ Konfiguration

Das Projekt verwendet Umgebungsvariablen zur Konfiguration. Erstellen Sie eine `.env`-Datei mit folgendem Inhalt:
