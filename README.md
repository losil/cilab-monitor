# Term Paper Aufgabe 15

## Aufgabenstellung

Abgeänderte Aufgabenstellung Nr. 3:
Docker Container mit Monitoring Script, welches mehrere TCP-Destinations überwachen kann. Die zu überwachenden Destinations werden mit einer YAML-Datei konfiguriert. Falls eine Verbindung nicht erreichbar ist (mit Schwellwerten in Minuten), wird per E-Mail oder sonst einer Nachricht (SMS) informiert.

## Umsetzung

Umgesetzt wurde die Monitoring-Lösung mit Python3. Der Skript läut dabei in einem Docker-Container.
Alle Dependecies werden im Dockerfile aufgelöst. Damit der Skript erfolgreich ausgeführt werden kann, muss ein Gmail-Account in der Konfiguration hinterlegt werden.
Das Passwort wird verschlüsselt abgelegt. Die zu überwachende Server bzw. deren Ports werden in einer Konfiuration festgesetzt.

## Konfiguration

Zur Ausführung wird eine Konfigurationsdatei benötigt. Zur Darstellug wird das YAML-Format verwendet.

```yaml
---
# ./config.yml

hosts:
  server1.localdomain:
    - 22
    - 443
  server2.localdomain:
    - 22
    - 80

check_interval: 20 # value in seconds
max_failures: 2 # max failed connect attemps before notification is sent
log_level: info #info or debug are supported values

mail:
  server: smtp.gmail.com
  port: 587
  from: example@gmail.com
  to:
    - name@stud.hslu.ch
    - name@hotmail.com
```

### Mail Account Passwort verschlüsseln

Damit das Passwort nicht Klartext in Sourcecode oder in der Konfigurationsdatei zu finden ist, wird es verschlüsselt. Diese Python Commands können auf dem Docker Host ausgeführt werden.

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()

cipher_suite = Fernet(key)
ciphered_text = cipher_suite.encrypt(b"SuperSecretPassword")
with open('/etc/monitoring/key.bin', 'wb') as file:
    file.write(key)
    file.close()
with open('/etc/monitoring/password.bin','wb') as file:
    file.write(ciphered_text)
    file.close()

```

Die Erstellen Files werden in den Container gemappt.

## Installation mit Docker

Mit dem vorbereiten `Dockerfile` kann ein Docker-Image gebuildet werden, welches sich starten lässt und mit dem Monitoren beginnt.

```bash
git pull git@gitlab.enterpriselab.ch:cil-19hs/cil-19hs-15.git
docker build cil-19hs-15/
docker tag ${IMAGE_ID} cilab-monitoring:latest
```

Anschliessend kann der Docker-Container gestarten werden. Dabei wird ein anderes Config-File in den Container gemountet, damit es nicht jedesmal von Git überschrieben wird.

```bash
docker run -d -v /etc/monitoring/config.yml:/opt/monitoring/config.yml \
-v /etc/monitoring/password.bin:/opt/monitoring/password.bin \
-v /etc/monitoring/key.bin:/opt/monitoring/key.bin \
--name cilab-monitoring cilab-monitoring
```
