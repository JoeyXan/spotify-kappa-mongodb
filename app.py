"""
Sistema de Recomendación de Música - Arquitectura Kappa con MongoDB
Aplicación Streamlit
"""

import streamlit as st
import pandas as pd
import sys
import os
import time
import random

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from kappa_processor_mongodb import KappaProcessorMongoDB

st.set_page_config(
    page_title="Recomendador Kappa - MongoDB",
    page_icon="🍃",
    layout="wide"
)

# Configuración de MongoDB
@st.cache_resource
def get_mongodb_uri():
    """Obtiene URI de MongoDB desde variables de entorno o secrets"""
    # Intentar desde Streamlit secrets
    if hasattr(st, 'secrets') and 'mongodb' in st.secrets:
        return st.secrets['mongodb']['uri']
    
    # Intentar desde variable de entorno
    mongodb_uri = os.getenv('MONGODB_URI')
    if mongodb_uri:
        return mongodb_uri
    
    return None

# Inicializar procesador
@st.cache_resource
def load_processor():
    mongodb_uri = get_mongodb_uri()
    
    if not mongodb_uri:
        st.error("No se encontró la configuración de MongoDB. Ver documentación.")
        st.stop()
    
    processor = KappaProcessorMongoDB(mongodb_uri)
    
    if not processor.load_data_from_mongodb():
        st.error("Error cargando datos desde MongoDB. Verifica la conexión.")
        st.stop()
    
    processor.start_processing()
    return processor

# Estado de sesión
if 'user_id' not in st.session_state:
    st.session_state.user_id = "usuario_demo"
if 'last_interaction' not in st.session_state:
    st.session_state.last_interaction = None

# Cargar procesador
try:
    processor = load_processor()
except Exception as e:
    st.error(f"Error inicializando el sistema: {e}")
    st.info("""
    **Configuración requerida:**
    
    1. Crea un archivo `.streamlit/secrets.toml`
    2. Agrega tu URI de MongoDB:
    
    ```toml
    [mongodb]
    uri = "mongodb+srv://usuario:password@cluster.mongodb.net/"
    ```
    
    O configura la variable de entorno `MONGODB_URI`
    """)
    st.stop()

# Header
st.title("Sistema de Recomendación de Música")
st.markdown("**Arquitectura Kappa** con **MongoDB Atlas** ☁")

# Sidebar
with st.sidebar:
    st.header("Configuración")
    
    user_id = st.text_input("ID de Usuario", value=st.session_state.user_id)
    st.session_state.user_id = user_id
    
    st.divider()
    
    st.header("Estado del Sistema")
    stats = processor.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Canciones", f"{stats['total_tracks']:,}")
        st.metric("Usuarios", stats['total_users'])
    with col2:
        st.metric("Interacciones", stats['total_interactions'])
        st.metric("En Cola", stats['events_in_queue'])
    
    st.divider()
    
    # Perfil de usuario
    profile = processor.get_user_profile(user_id)
    if profile:
        st.subheader("Tu Actividad")
        st.write(f"▶ Plays: {profile['plays']}")
        st.write(f"❤ Likes: {profile['likes']}")
        st.write(f"⏭ Skips: {profile['skips']}")
    
    st.divider()
    st.caption("🍃 Datos en MongoDB Atlas")

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs([
    "Recomendaciones",
    "Arquitectura con MongoDB",
    "Trending en Tiempo Real",
    "Simulador de Eventos"
])

# TAB 1: Recomendaciones
with tab1:
    st.header("Obtener Recomendaciones")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Buscar canción",
            placeholder="Escribe el nombre de una canción..."
        )
        
        if search_query:
            matches = processor.tracks_df[
                processor.tracks_df['track_name'].str.contains(search_query, case=False, na=False)
            ].head(10)
            
            if not matches.empty:
                st.subheader("Resultados")
                
                selected_track = st.selectbox(
                    "Selecciona una canción:",
                    options=matches.index,
                    format_func=lambda x: f"{matches.loc[x, 'track_name']} - {matches.loc[x, 'artists']}"
                )
                
                if st.button("Obtener Recomendaciones", type="primary"):
                    track_info = matches.loc[selected_track]
                    
                    # Registrar interacción (se guarda en MongoDB)
                    processor.add_event(
                        user_id=st.session_state.user_id,
                        track_id=track_info['track_id'],
                        interaction_type='play'
                    )
                    
                    st.success(f"Reproduciendo: {track_info['track_name']}")
                    st.caption("Interacción guardada en MongoDB")
                    
                    # Obtener recomendaciones
                    recommendations = processor.get_recommendations(
                        track_id=track_info['track_id'],
                        user_id=st.session_state.user_id,
                        top_n=10
                    )
                    
                    st.subheader("Recomendaciones Personalizadas")
                    
                    for idx, rec in enumerate(recommendations, 1):
                        with st.container():
                            col_a, col_b, col_c, col_d = st.columns([3, 2, 1, 1])
                            
                            with col_a:
                                st.markdown(f"**{idx}. {rec['track_name']}**")
                                st.caption(f"{rec['artists']}")
                            
                            with col_b:
                                st.caption(f"Género: {rec['track_genre']}")
                            
                            with col_c:
                                st.metric("Score", f"{rec['score']:.2f}")
                            
                            with col_d:
                                if st.button("❤", key=f"like_{idx}"):
                                    processor.add_event(
                                        user_id=st.session_state.user_id,
                                        track_id=rec['track_id'],
                                        interaction_type='like'
                                    )
                                    st.success("Like guardado en MongoDB")
                                    time.sleep(0.5)
                                    st.rerun()
                            
                            st.divider()
            else:
                st.warning("No se encontraron canciones")
    
    with col2:
        st.info("""
        **Arquitectura Kappa + MongoDB**
        
        - Datos en la nube (MongoDB Atlas)
        - Interacciones guardadas en tiempo real
        - Procesamiento continuo
        - Recomendaciones personalizadas
        """)

# TAB 2: Arquitectura
with tab2:
    st.header("Arquitectura Kappa con MongoDB Atlas")
    
    st.markdown("""
    Sistema de recomendación en tiempo real con base de datos en la nube.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Flujo de Datos")
        st.code("""
Usuario interactúa
    ↓
Evento a MongoDB
    ↓
Procesador actualiza modelo
    ↓
Recomendaciones personalizadas
        """)
    
    with col2:
        st.subheader("Colecciones MongoDB")
        st.code("""
tracks:
  - Catálogo de canciones
  - 4,832 documentos

user_interactions:
  - Interacciones en tiempo real
  - play, like, skip

track_popularity:
  - Popularidad actualizada
  - Sincronización automática
        """)
    
    st.divider()
    
    st.subheader("Ventajas de MongoDB Atlas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Escalabilidad**
        - Base de datos en la nube
        - Crece según necesidad
        - Sin límites de almacenamiento
        """)
    
    with col2:
        st.markdown("""
        **Disponibilidad**
        - Acceso desde cualquier lugar
        - Alta disponibilidad
        - Backups automáticos
        """)
    
    with col3:
        st.markdown("""
        **Flexibilidad**
        - Esquema flexible (NoSQL)
        - Consultas rápidas
        - Índices optimizados
        """)
    
    st.divider()
    
    st.subheader("Métricas del Sistema")
    
    stats = processor.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Canciones en MongoDB", f"{stats['total_tracks']:,}")
    with col2:
        st.metric("Usuarios Activos", stats['total_users'])
    with col3:
        st.metric("Interacciones Guardadas", stats['total_interactions'])
    with col4:
        st.metric("Eventos en Cola", stats['events_in_queue'])

# TAB 3: Trending
with tab3:
    st.header("Canciones Trending en Tiempo Real")
    
    st.markdown("Popularidad calculada desde interacciones guardadas en MongoDB")
    
    trending = processor.get_trending_tracks(top_n=20)
    
    if trending:
        for idx, track in enumerate(trending, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                
                with col1:
                    st.markdown(f"**#{idx}**")
                
                with col2:
                    st.markdown(f"**{track['track_name']}**")
                    st.caption(track['artists'])
                
                with col3:
                    st.caption(f"Género: {track['track_genre']}")
                
                with col4:
                    st.metric("🔥", track['popularity'])
                
                st.divider()
    else:
        st.info("No hay datos de trending aún. Interactúa con canciones para generar trending.")

# TAB 4: Simulador
with tab4:
    st.header("Simulador de Actividad de Usuarios")
    
    st.markdown("Simula usuarios interactuando con canciones. Todas las interacciones se guardan en MongoDB.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_events = st.slider("Número de eventos a simular", 5, 50, 20)
        
        if st.button("Simular Actividad", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(num_events):
                # Seleccionar usuario y canción aleatoria
                user = f"user_{random.randint(1, 10)}"
                track = processor.tracks_df.sample(1).iloc[0]
                interaction = random.choices(
                    ['play', 'like', 'skip'],
                    weights=[0.7, 0.2, 0.1]
                )[0]
                
                # Registrar evento (se guarda en MongoDB)
                processor.add_event(user, track['track_id'], interaction)
                
                # Actualizar progreso
                progress = (i + 1) / num_events
                progress_bar.progress(progress)
                status_text.text(f"Evento {i+1}/{num_events}: {user} - {interaction} - {track['track_name'][:30]}")
                
                time.sleep(0.1)
            
            st.success(f"{num_events} eventos simulados y guardados en MongoDB")
            time.sleep(1)
            st.rerun()
    
    with col2:
        st.info("""
        **Tipos de interacciones:**
        
        - ▶ **Play**: Reproducción (+1 popularidad)
        - ❤ **Like**: Me gusta (+3 popularidad)
        - ⏭ **Skip**: Saltar (-1 popularidad)
        
        Todas las interacciones se guardan en MongoDB Atlas en tiempo real.
        """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; padding: 1rem;">
    <p>Sistema de Recomendación de Música - Arquitectura Kappa con MongoDB Atlas</p>
    <p>Procesamiento en Tiempo Real | Base de Datos en la Nube</p>
</div>
""", unsafe_allow_html=True)
