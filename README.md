# Sistema de Recomendación - Arquitectura Kappa con MongoDB Atlas

Sistema de recomendación de música en tiempo real que usa MongoDB Atlas como base de datos en la nube.

## Características

- **Arquitectura Kappa**: Procesamiento en tiempo real con una sola capa
- **MongoDB Atlas**: Base de datos NoSQL en la nube (gratis)
- **Interfaz Streamlit**: 4 pestañas interactivas
- **Tiempo Real**: Todas las interacciones se guardan inmediatamente
- **Escalable**: MongoDB Atlas crece según necesidad

## Diferencias con la Versión Anterior

| Aspecto | Versión CSV | Versión MongoDB |
|---------|-------------|-----------------|
| Almacenamiento | Archivo local | Nube (MongoDB Atlas) |
| Persistencia | Temporal | Permanente |
| Escalabilidad | Limitada | Ilimitada |
| Acceso | Solo local | Desde cualquier lugar |
| Interacciones | En memoria | Guardadas en DB |
| Backups | Manual | Automático |

## Requisitos

- Ubuntu 20.04+
- Python 3.8+
- Cuenta en MongoDB Atlas (gratis)
- 4 GB RAM
- Puerto 8501 disponible

## Instalación

### Paso 1: Configurar MongoDB Atlas

Sigue la guía completa en `MONGODB_SETUP.md` para:
1. Crear cuenta en MongoDB Atlas
2. Crear cluster gratuito
3. Configurar acceso
4. Obtener URI de conexión

### Paso 2: Migrar Datos

```bash
cd spotify-kappa-mongodb

# Instalar pymongo
pip3 install pymongo

# Migrar CSV a MongoDB
python3 scripts/migrate_to_mongodb.py "TU_MONGODB_URI_AQUI"
```

Ejemplo:
```bash
python3 scripts/migrate_to_mongodb.py "mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/"
```

### Paso 3: Configurar la Aplicación

Opción A - Variable de entorno:
```bash
export MONGODB_URI="mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/"
```

Opción B - Archivo de secrets:
```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
[mongodb]
uri = "mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/"
EOF
```

### Paso 4: Ejecutar

```bash
./start.sh
```

Abre en tu navegador:
```
http://IP-DE-TU-SERVIDOR:8501
```

## Arquitectura

### Flujo de Datos

```
Usuario interactúa
    ↓
Evento → MongoDB (user_interactions)
    ↓
Procesador actualiza modelo
    ↓
Popularidad → MongoDB (track_popularity)
    ↓
Recomendaciones personalizadas
```

### Colecciones en MongoDB

1. **tracks** (4,832 documentos)
   - Catálogo de canciones
   - Características de audio
   - Metadatos

2. **user_interactions** (crece con el uso)
   - Todas las interacciones en tiempo real
   - play, like, skip
   - Timestamp de cada evento

3. **track_popularity** (actualizada continuamente)
   - Popularidad de cada canción
   - Calculada desde interacciones
   - Sincronización automática

## Uso

### Buscar y Recomendar

1. Ve a la pestaña "Recomendaciones"
2. Busca una canción
3. Obtén recomendaciones personalizadas
4. Da "like" a canciones que te gusten

Todas las interacciones se guardan en MongoDB.

### Ver Trending

1. Ve a "Trending en Tiempo Real"
2. Observa las canciones más populares
3. Se actualiza con cada interacción

### Simular Actividad

1. Ve a "Simulador de Eventos"
2. Selecciona número de eventos
3. Haz clic en "Simular Actividad"
4. Observa cómo se guardan en MongoDB

### Verificar en MongoDB Atlas

1. Ve a tu cluster en MongoDB Atlas
2. Haz clic en "Browse Collections"
3. Verás las 3 colecciones con datos

## Ventajas de MongoDB Atlas

### 1. Persistencia

Todos los datos se guardan permanentemente en la nube. Si reinicias el servidor, los datos persisten.

### 2. Escalabilidad

MongoDB Atlas crece automáticamente según necesidad. No hay límites de almacenamiento.

### 3. Disponibilidad

Accede a tus datos desde cualquier lugar. No necesitas estar en el servidor.

### 4. Backups

MongoDB Atlas hace backups automáticos. Puedes restaurar datos en cualquier momento.

### 5. Consultas Rápidas

Índices optimizados para consultas rápidas. Búsquedas en milisegundos.

## Estructura del Proyecto

```
spotify-kappa-mongodb/
├── app.py                          # Aplicación Streamlit
├── src/
│   └── kappa_processor_mongodb.py  # Procesador con MongoDB
├── scripts/
│   └── migrate_to_mongodb.py       # Script de migración
├── data/
│   └── dataset.csv                 # Dataset original
├── requirements.txt                # Dependencias
├── start.sh                        # Script de inicio
├── README.md                       # Este archivo
└── MONGODB_SETUP.md                # Guía de MongoDB Atlas
```

## Comparación: Arquitectura Lambda vs Kappa

### Lambda

```
Capa Batch (histórico)
    ↓
Capa de Velocidad (real-time)
    ↓
Capa de Servicio (fusión)
```

**Ventajas**: Bueno para análisis histórico
**Desventajas**: Complejo, código duplicado

### Kappa

```
Stream de Eventos
    ↓
Procesador Único
    ↓
Modelo Actualizado
```

**Ventajas**: Simple, todo en tiempo real
**Desventajas**: Reprocesamiento más costoso

## Monitoreo

### En MongoDB Atlas

1. Ve a tu cluster
2. Haz clic en "Metrics"
3. Observa:
   - Conexiones activas
   - Operaciones por segundo
   - Uso de almacenamiento
   - Uso de red

### En la Aplicación

La barra lateral muestra:
- Total de canciones
- Usuarios activos
- Interacciones guardadas
- Eventos en cola

## Troubleshooting

### Error: "No se encontró la configuración de MongoDB"

Configura la variable de entorno o el archivo de secrets. Ver `MONGODB_SETUP.md`.

### Error: "Authentication failed"

Verifica que usuario y contraseña sean correctos en la URI.

### Error: "Connection timeout"

Verifica que hayas agregado tu IP en "Network Access" en MongoDB Atlas.

### Error: "No hay datos en MongoDB"

Ejecuta el script de migración:
```bash
python3 scripts/migrate_to_mongodb.py "TU_MONGODB_URI"
```

## Seguridad

- **No compartas tu URI**: Contiene tu contraseña
- **Usa variables de entorno**: No pongas la URI en el código
- **Restringe IPs**: Solo permite IPs conocidas en MongoDB Atlas
- **Contraseñas fuertes**: Usa contraseñas seguras

## Límites del Plan Gratuito

MongoDB Atlas M0 (gratis):
- Almacenamiento: 512 MB
- RAM: 512 MB compartida
- Conexiones: 500 simultáneas

Para este proyecto: < 5 MB usado (suficiente).

## Comandos Útiles

```bash
# Iniciar aplicación
./start.sh

# Migrar datos
python3 scripts/migrate_to_mongodb.py "MONGODB_URI"

# Ver logs
tail -f ~/.streamlit/logs/streamlit.log

# Detener aplicación
pkill -f streamlit
```

## Próximos Pasos

1. Configura MongoDB Atlas (ver `MONGODB_SETUP.md`)
2. Migra los datos
3. Configura la URI
4. Inicia la aplicación
5. Prueba las recomendaciones
6. Verifica que los datos se guarden en MongoDB

## Recursos

- MongoDB Atlas: https://www.mongodb.com/cloud/atlas
- Documentación MongoDB: https://docs.mongodb.com/
- PyMongo: https://pymongo.readthedocs.io/
