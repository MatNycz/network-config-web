import os
import time
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from app.extensions import db
from app.models import Device, Interface
from app import create_app

app = create_app()

WATCH_DIRECTORY = os.path.abspath('./xml_files')
print(f"[INFO] Watching directory: {WATCH_DIRECTORY}")

file_hashes = {}

def get_file_hash(file_path):
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

class XMLHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory or not event.src_path.endswith('.xml'):
            return
        time.sleep(1.0)

        with app.app_context():
            print(f"[INFO] Event on: {event.src_path}")
            self.process_xml(event.src_path)

    def process_xml(self, file_path):
        print(f"[DEBUG] Parsing XML file: {file_path}")

        current_hash = get_file_hash(file_path)
        if current_hash is None:
            print(f"[ERROR] Could not read file {file_path}")
            return

        if file_path in file_hashes and file_hashes[file_path] == current_hash:
            print(f"[INFO] File unchanged, skipping: {file_path}")
            return

        file_hashes[file_path] = current_hash

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            name_elem = root.find('name')
            status_elem = root.find('status')
            if name_elem is None or status_elem is None:
                print(f"[WARNING] Missing <name> or <status> in {file_path}")
                return

            name = name_elem.text.strip()
            status = status_elem.text.strip()

            if not name:
                print(f"[WARNING] Empty device name in {file_path}")
                return

            # Aktualny czas w strefie Europe/Warsaw
            warsaw_tz = pytz.timezone('Europe/Warsaw')
            now = datetime.now(warsaw_tz)

            device = Device.query.filter_by(name=name).first()
            if not device:
                device = Device(name=name, status=status, created_at=now)
                db.session.add(device)
            else:
                device.status = status
                device.created_at = now 

            db.session.commit()

            print(f"[INFO] Updating interfaces for device '{name}'")
            Interface.query.filter_by(device_id=device.id).delete()
            db.session.commit()

            interfaces = root.find('interfaces')
            if interfaces is not None:
                for iface in interfaces.findall('interface'):
                    interface = Interface(
                        device_id=device.id,
                        name=(iface.findtext('name') or '').strip(),
                        ipv4=(iface.findtext('ipv4') or '').strip(),
                        ipv6=(iface.findtext('ipv6') or '').strip(),
                        mask=(iface.findtext('mask') or '').strip(),
                        status=(iface.findtext('status') or 'unknown').strip()
                    )
                    db.session.add(interface)
                db.session.commit()

            print(f"[SUCCESS] Finished processing {file_path}")

        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {str(e)}")
            db.session.rollback()

def start_watcher():
    event_handler = XMLHandler()

    with app.app_context():
        for filename in os.listdir(WATCH_DIRECTORY):
            if filename.endswith('.xml'):
                filepath = os.path.join(WATCH_DIRECTORY, filename)
                print(f"[INFO] Processing existing file on startup: {filepath}")
                event_handler.process_xml(filepath)

    observer = PollingObserver(timeout=1)
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
    observer.start()
    print(f"[WATCHING] Folder: {WATCH_DIRECTORY}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Stopping observer...")
        observer.stop()
    observer.join()

if __name__ == '__main__':
    start_watcher()
