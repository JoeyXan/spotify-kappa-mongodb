"""
Procesador Kappa con MongoDB
Procesa eventos en tiempo real y guarda en MongoDB Atlas
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict, deque
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
import threading
import time

class KappaProcessorMongoDB:
    """
    Procesador de eventos en tiempo real - Arquitectura Kappa con MongoDB
    """
    
    def __init__(self, mongodb_uri, database_name='spotify_kappa'):
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        
        self.scaler = StandardScaler()
        self.tracks_df = None
        self.similarity_matrix = None
        self.track_popularity = defaultdict(int)
        self.event_queue = deque(maxlen=10000)
        
        self.audio_features = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness',
            'liveness', 'valence', 'tempo'
        ]
        
        self.lock = threading.Lock()
        self.is_running = False
        self.processor_thread = None
        
    def connect_mongodb(self):
        """Conecta a MongoDB Atlas"""
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[self.database_name]
            print("Conectado a MongoDB Atlas")
            return True
        except Exception as e:
            print(f"Error conectando a MongoDB: {e}")
            return False
        
    def load_data_from_mongodb(self):
        """Carga datos desde MongoDB"""
        if not self.db:
            if not self.connect_mongodb():
                return False
        
        print("Cargando datos desde MongoDB...")
        
        # Obtener todas las canciones
        tracks_collection = self.db['tracks']
        tracks_cursor = tracks_collection.find({})
        tracks_list = list(tracks_cursor)
        
        if not tracks_list:
            print("ERROR: No hay datos en MongoDB. Ejecuta migrate_to_mongodb.py primero.")
            return False
        
        # Convertir a DataFrame
        self.tracks_df = pd.DataFrame(tracks_list)
        
        # Eliminar campo _id de MongoDB
        if '_id' in self.tracks_df.columns:
            self.tracks_df = self.tracks_df.drop('_id', axis=1)
        
        # Preparar features
        features = self.tracks_df[self.audio_features].fillna(0)
        features_scaled = self.scaler.fit_transform(features)
        
        # Calcular similitud
        self.similarity_matrix = cosine_similarity(features_scaled)
        
        # Cargar popularidad desde MongoDB
        self._load_popularity_from_mongodb()
        
        print(f"Datos cargados: {len(self.tracks_df)} canciones")
        return True
        
    def _load_popularity_from_mongodb(self):
        """Carga popularidad de canciones desde MongoDB"""
        popularity_collection = self.db['track_popularity']
        
        for doc in popularity_collection.find({}):
            self.track_popularity[doc['track_id']] = doc['popularity']
        
    def start_processing(self):
        """Inicia el procesamiento de eventos"""
        if self.is_running:
            return
            
        self.is_running = True
        self.processor_thread = threading.Thread(target=self._process_events_loop, daemon=True)
        self.processor_thread.start()
        print("Procesador de eventos iniciado")
        
    def stop_processing(self):
        """Detiene el procesamiento"""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=2)
        print("Procesador detenido")
        
    def _process_events_loop(self):
        """Loop de procesamiento de eventos"""
        while self.is_running:
            if self.event_queue:
                with self.lock:
                    event = self.event_queue.popleft()
                    self._process_single_event(event)
            else:
                time.sleep(0.1)
                
    def add_event(self, user_id, track_id, interaction_type='play'):
        """Agrega un evento y lo guarda en MongoDB"""
        event = {
            'user_id': user_id,
            'track_id': track_id,
            'interaction_type': interaction_type,
            'timestamp': datetime.now()
        }
        
        # Guardar en MongoDB
        try:
            interactions_collection = self.db['user_interactions']
            interactions_collection.insert_one(event.copy())
        except Exception as e:
            print(f"Error guardando interacción en MongoDB: {e}")
        
        # Agregar a cola de procesamiento
        self.event_queue.append(event)
        
        # Procesar inmediatamente si no hay thread
        if not self.is_running:
            with self.lock:
                self._process_single_event(event)
        
        return event
        
    def _process_single_event(self, event):
        """Procesa un evento individual"""
        track_id = event['track_id']
        interaction_type = event['interaction_type']
        
        # Actualizar popularidad
        weight = {'play': 1, 'like': 3, 'skip': -1}.get(interaction_type, 1)
        self.track_popularity[track_id] += weight
        
        # Actualizar en MongoDB (batch cada 10 eventos para eficiencia)
        if len(self.event_queue) % 10 == 0:
            self._sync_popularity_to_mongodb()
        
    def _sync_popularity_to_mongodb(self):
        """Sincroniza popularidad con MongoDB"""
        try:
            popularity_collection = self.db['track_popularity']
            
            for track_id, popularity in self.track_popularity.items():
                popularity_collection.update_one(
                    {'track_id': track_id},
                    {'$set': {'popularity': popularity, 'updated_at': datetime.now()}},
                    upsert=True
                )
        except Exception as e:
            print(f"Error sincronizando popularidad: {e}")
            
    def get_recommendations(self, track_id, user_id=None, top_n=10):
        """Genera recomendaciones en tiempo real"""
        with self.lock:
            track_idx = self.tracks_df[self.tracks_df['track_id'] == track_id].index
            
            if len(track_idx) == 0:
                return []
            
            track_idx = track_idx[0]
            
            # Similitudes base
            sim_scores = list(enumerate(self.similarity_matrix[track_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:top_n*2]
            
            # Aplicar boost de popularidad
            boosted_scores = []
            for idx, score in sim_scores:
                track = self.tracks_df.iloc[idx]
                popularity_boost = self.track_popularity.get(track['track_id'], 0) * 0.01
                final_score = score + popularity_boost
                boosted_scores.append((idx, final_score, track))
            
            # Personalización por usuario
            if user_id:
                user_preferences = self._get_user_preferences_from_mongodb(user_id)
                if user_preferences:
                    liked_genres = user_preferences.get('liked_genres', set())
                    
                    for i, (idx, score, track) in enumerate(boosted_scores):
                        if track['track_genre'] in liked_genres:
                            boosted_scores[i] = (idx, score * 1.2, track)
            
            # Top N final
            boosted_scores = sorted(boosted_scores, key=lambda x: x[1], reverse=True)
            boosted_scores = boosted_scores[:top_n]
            
            recommendations = []
            for idx, score, track in boosted_scores:
                recommendations.append({
                    'track_id': track['track_id'],
                    'track_name': track['track_name'],
                    'artists': track['artists'],
                    'track_genre': track['track_genre'],
                    'score': float(score),
                    'popularity': self.track_popularity.get(track['track_id'], 0)
                })
            
            return recommendations
    
    def _get_user_preferences_from_mongodb(self, user_id):
        """Obtiene preferencias de usuario desde MongoDB"""
        try:
            interactions_collection = self.db['user_interactions']
            
            # Obtener últimas 100 interacciones
            user_interactions = list(interactions_collection.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(100))
            
            if not user_interactions:
                return None
            
            # Extraer géneros de canciones con like
            liked_tracks = [i['track_id'] for i in user_interactions if i['interaction_type'] == 'like']
            
            liked_genres = set()
            for track_id in liked_tracks:
                track_row = self.tracks_df[self.tracks_df['track_id'] == track_id]
                if not track_row.empty:
                    liked_genres.add(track_row.iloc[0]['track_genre'])
            
            return {
                'liked_genres': liked_genres,
                'total_interactions': len(user_interactions)
            }
        except Exception as e:
            print(f"Error obteniendo preferencias: {e}")
            return None
    
    def get_user_profile(self, user_id):
        """Obtiene perfil de usuario desde MongoDB"""
        try:
            interactions_collection = self.db['user_interactions']
            
            # Obtener todas las interacciones del usuario
            user_interactions = list(interactions_collection.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(100))
            
            if not user_interactions:
                return None
            
            liked = [i for i in user_interactions if i['interaction_type'] == 'like']
            played = [i for i in user_interactions if i['interaction_type'] == 'play']
            skipped = [i for i in user_interactions if i['interaction_type'] == 'skip']
            
            return {
                'user_id': user_id,
                'total_interactions': len(user_interactions),
                'likes': len(liked),
                'plays': len(played),
                'skips': len(skipped),
                'recent_tracks': user_interactions[:5]
            }
        except Exception as e:
            print(f"Error obteniendo perfil: {e}")
            return None
    
    def get_trending_tracks(self, top_n=10):
        """Obtiene trending tracks"""
        with self.lock:
            sorted_tracks = sorted(
                self.track_popularity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
            
            trending = []
            for track_id, popularity in sorted_tracks:
                track_row = self.tracks_df[self.tracks_df['track_id'] == track_id]
                if not track_row.empty:
                    track = track_row.iloc[0]
                    trending.append({
                        'track_id': track_id,
                        'track_name': track['track_name'],
                        'artists': track['artists'],
                        'track_genre': track['track_genre'],
                        'popularity': popularity
                    })
            
            return trending
    
    def get_stats(self):
        """Obtiene estadísticas del sistema"""
        try:
            interactions_collection = self.db['user_interactions']
            
            total_interactions = interactions_collection.count_documents({})
            unique_users = len(interactions_collection.distinct('user_id'))
            
            return {
                'total_tracks': len(self.tracks_df),
                'total_users': unique_users,
                'total_interactions': total_interactions,
                'events_in_queue': len(self.event_queue),
                'trending_count': len([p for p in self.track_popularity.values() if p > 0])
            }
        except Exception as e:
            print(f"Error obteniendo stats: {e}")
            return {
                'total_tracks': len(self.tracks_df) if self.tracks_df is not None else 0,
                'total_users': 0,
                'total_interactions': 0,
                'events_in_queue': len(self.event_queue),
                'trending_count': 0
            }
    
    def close(self):
        """Cierra conexión a MongoDB"""
        self.stop_processing()
        if self.client:
            self.client.close()
            print("Conexión a MongoDB cerrada")
