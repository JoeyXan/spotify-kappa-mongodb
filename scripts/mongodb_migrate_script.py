#!/usr/bin/env python3
import sys
import pandas as pd
from pymongo import MongoClient

def migrate_to_mongodb(uri):
    print("\n=== Migracion de CSV a MongoDB ===\n")
    print("Conectando a MongoDB...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.server_info()
        print("Conexion exitosa\n")
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    db = client['spotify_kappa']
    tracks = db['tracks']
    
    print("Leyendo CSV...")
    df = pd.read_csv('data/dataset.csv')
    print(f"Total canciones: {len(df):,}\n")
    
    if len(df) > 10000:
        print("Seleccionando muestra...")
        df = df.groupby('track_genre', group_keys=False).apply(
            lambda x: x.sample(min(len(x), max(1, int(len(x) * 0.05))))
        )
        print(f"Seleccionadas: {len(df):,}\n")
    
    print("Limpiando coleccion...")
    tracks.delete_many({})
    
    print(f"Insertando {len(df):,} documentos...")
    docs = df.to_dict('records')
    result = tracks.insert_many(docs)
    print(f"Insertados: {len(result.inserted_ids):,}\n")
    
    print("Creando indices...")
    try:
        tracks.create_index("track_id", unique=True)
        tracks.create_index("track_genre")
        tracks.create_index("artists")
        print("Indices creados\n")
    except Exception as e:
        print(f"Advertencia: {e}\n")
    
    count = tracks.count_documents({})
    print(f"Total en MongoDB: {count:,}")
    print("\n=== Completado ===\n")
    
    client.close()
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 migrate_to_mongodb.py <MONGODB_URI>")
        sys.exit(1)
    migrate_to_mongodb(sys.argv[1])
