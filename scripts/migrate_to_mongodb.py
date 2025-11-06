"""
Script de migración de CSV a MongoDB Atlas
Migra el dataset de Spotify a MongoDB en la nube
"""

import pandas as pd
from pymongo import MongoClient
import sys
import os

def migrate_csv_to_mongodb(csv_path, mongodb_uri, database_name='spotify_kappa'):
    """
    Migra el CSV de Spotify a MongoDB Atlas
    """
    print("=== Migración de CSV a MongoDB ===\n")
    
    # Conectar a MongoDB
    print(f"Conectando a MongoDB...")
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("Conexión exitosa\n")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a MongoDB")
        print(f"Detalles: {e}")
        return False
    
    db = client[database_name]
    
    # Leer CSV
    print(f"Leyendo CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Total de canciones: {len(df):,}\n")
    
    # Tomar muestra representativa (para no saturar MongoDB gratis)
    print("Seleccionando muestra representativa...")
    df_sample = df.groupby('track_genre', group_keys=False).apply(
        lambda x: x.sample(min(len(x), 50), random_state=42)
    ).reset_index(drop=True)
    print(f"Canciones seleccionadas: {len(df_sample):,}")
    print(f"Géneros: {df_sample['track_genre'].nunique()}\n")
    
    # Limpiar colección existente
    tracks_collection = db['tracks']
    print("Limpiando colección existente...")
    tracks_collection.delete_many({})
    
    # Convertir a documentos
    print("Convirtiendo a documentos MongoDB...")
    tracks_documents = df_sample.to_dict('records')
    
    # Insertar en MongoDB
    print(f"Insertando {len(tracks_documents):,} documentos...")
    result = tracks_collection.insert_many(tracks_documents)
    print(f"Insertados: {len(result.inserted_ids):,} documentos\n")
    
    # Crear índices
    print("Creando índices...")
    tracks_collection.create_index('track_id', unique=True)
    tracks_collection.create_index('track_name')
    tracks_collection.create_index('track_genre')
    tracks_collection.create_index('artists')
    print("Índices creados\n")
    
    # Verificar
    print("Verificando migración...")
    count = tracks_collection.count_documents({})
    print(f"Total de documentos en MongoDB: {count:,}")
    
    # Mostrar ejemplo
    sample_doc = tracks_collection.find_one()
    print("\nEjemplo de documento:")
    print(f"  Track: {sample_doc.get('track_name')}")
    print(f"  Artist: {sample_doc.get('artists')}")
    print(f"  Genre: {sample_doc.get('track_genre')}")
    
    print("\n=== Migración completada exitosamente ===")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python migrate_to_mongodb.py <MONGODB_URI>")
        print("\nEjemplo:")
        print('python migrate_to_mongodb.py "mongodb+srv://usuario:password@cluster.mongodb.net/"')
        sys.exit(1)
    
    mongodb_uri = sys.argv[1]
    csv_path = "data/dataset.csv"
    
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el archivo {csv_path}")
        sys.exit(1)
    
    success = migrate_csv_to_mongodb(csv_path, mongodb_uri)
    sys.exit(0 if success else 1)
