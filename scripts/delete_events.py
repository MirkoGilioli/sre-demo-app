#!/usr/bin/env python3
import os
from google.cloud import firestore

def delete_all_events():
    # We will use the known default configuration to avoid PyYAML dependency
    db_name = "sre-demo"
    collection_name = "agenda_events"

    # Firestore Setup
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
    if emulator_host:
        print(f"Connecting to Firestore Emulator at {emulator_host} with DB '{db_name}'")
        db = firestore.Client(database=db_name)
    else:
        print(f"Connecting to Firestore Cloud DB '{db_name}'")
        db = firestore.Client(database=db_name)

    collection_ref = db.collection(collection_name)
    
    print(f"Target Collection: {collection_name}")
    
    confirm = input(f"Are you sure you want to delete ALL documents from '{collection_name}'? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return

    batch_size = 500
    deleted_count = 0
    
    while True:
        docs = list(collection_ref.limit(batch_size).stream())
        if not docs:
            break
        
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            deleted_count += 1
        
        batch.commit()
        print(f"Deleted {len(docs)} documents... (Total: {deleted_count})")

    if deleted_count == 0:
        print(f"No documents found in collection '{collection_name}'.")
    else:
        print(f"Successfully deleted all {deleted_count} events from '{collection_name}'.")

if __name__ == "__main__":
    delete_all_events()
