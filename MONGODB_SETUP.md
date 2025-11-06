# Configuración de MongoDB Atlas

Esta guía te ayudará a configurar MongoDB Atlas (gratis) para el sistema de recomendación.

## Paso 1: Crear Cuenta en MongoDB Atlas

1. Ve a https://www.mongodb.com/cloud/atlas/register
2. Regístrate con tu email (o usa Google/GitHub)
3. Confirma tu email

## Paso 2: Crear un Cluster Gratuito

1. Después de iniciar sesión, haz clic en **"Build a Database"**
2. Selecciona **"M0 FREE"** (Shared)
3. Elige un proveedor de nube:
   - AWS (recomendado)
   - Google Cloud
   - Azure
4. Selecciona una región cercana a ti
5. Dale un nombre al cluster (ej: `spotify-kappa`)
6. Haz clic en **"Create"**

Espera 1-3 minutos mientras se crea el cluster.

## Paso 3: Configurar Acceso a la Base de Datos

### 3.1 Crear Usuario de Base de Datos

1. En la pantalla de "Security Quickstart", crea un usuario:
   - **Username**: `spotify_user` (o el que prefieras)
   - **Password**: Genera una contraseña segura (guárdala)
   - Haz clic en **"Create User"**

**IMPORTANTE**: Guarda el usuario y contraseña, los necesitarás después.

### 3.2 Configurar Acceso desde Cualquier IP

1. En "Where would you like to connect from?":
   - Selecciona **"My Local Environment"**
   - En "IP Access List", haz clic en **"Add My Current IP Address"**
   - O mejor, agrega `0.0.0.0/0` para permitir acceso desde cualquier IP
   - Haz clic en **"Finish and Close"**

## Paso 4: Obtener la URI de Conexión

1. En el dashboard, haz clic en **"Connect"** en tu cluster
2. Selecciona **"Connect your application"**
3. Selecciona:
   - **Driver**: Python
   - **Version**: 3.12 or later
4. Copia la **Connection String** (URI)

Se verá algo así:
```
mongodb+srv://spotify_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

5. **Reemplaza `<password>`** con tu contraseña real

Ejemplo final:
```
mongodb+srv://spotify_user:MiPassword123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

## Paso 5: Migrar Datos a MongoDB

### 5.1 Copiar el CSV

```bash
cp /ruta/al/dataset.csv ~/spotify-kappa-mongodb/data/
```

### 5.2 Instalar pymongo

```bash
pip3 install pymongo
```

### 5.3 Ejecutar Migración

```bash
cd ~/spotify-kappa-mongodb

python3 scripts/migrate_to_mongodb.py "TU_MONGODB_URI_AQUI"
```

Ejemplo:
```bash
python3 scripts/migrate_to_mongodb.py "mongodb+srv://spotify_user:MiPassword123@cluster0.xxxxx.mongodb.net/"
```

Deberías ver:
```
=== Migración de CSV a MongoDB ===

Conectando a MongoDB...
Conexión exitosa

Leyendo CSV: data/dataset.csv
Total de canciones: 114,000

Seleccionando muestra representativa...
Canciones seleccionadas: 4,832
Géneros: 114

Limpiando colección existente...
Convirtiendo a documentos MongoDB...
Insertando 4,832 documentos...
Insertados: 4,832 documentos

Creando índices...
Índices creados

Verificando migración...
Total de documentos en MongoDB: 4,832

=== Migración completada exitosamente ===
```

## Paso 6: Configurar la Aplicación

### Opción A: Variable de Entorno

```bash
export MONGODB_URI="mongodb+srv://spotify_user:MiPassword123@cluster0.xxxxx.mongodb.net/"
```

Para que sea permanente, agrégalo a `~/.bashrc`:
```bash
echo 'export MONGODB_URI="mongodb+srv://spotify_user:MiPassword123@cluster0.xxxxx.mongodb.net/"' >> ~/.bashrc
source ~/.bashrc
```

### Opción B: Archivo de Secrets (Streamlit)

Crea el archivo `.streamlit/secrets.toml`:

```bash
mkdir -p .streamlit
nano .streamlit/secrets.toml
```

Contenido:
```toml
[mongodb]
uri = "mongodb+srv://spotify_user:MiPassword123@cluster0.xxxxx.mongodb.net/"
```

Guarda y cierra (Ctrl+O, Enter, Ctrl+X).

## Paso 7: Ejecutar la Aplicación

```bash
./start.sh
```

O manualmente:
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Verificar Conexión

Puedes verificar que todo funciona visitando MongoDB Atlas:

1. Ve a tu cluster en MongoDB Atlas
2. Haz clic en **"Browse Collections"**
3. Deberías ver la base de datos `spotify_kappa` con 3 colecciones:
   - `tracks`: Catálogo de canciones (4,832 documentos)
   - `user_interactions`: Interacciones de usuarios (se llena al usar la app)
   - `track_popularity`: Popularidad de canciones (se actualiza en tiempo real)

## Colecciones en MongoDB

### 1. tracks

Almacena el catálogo de canciones.

Ejemplo de documento:
```json
{
  "track_id": "5SuOikwiRyPMVoIQDJUgSV",
  "track_name": "Shape of You",
  "artists": "Ed Sheeran",
  "track_genre": "pop",
  "danceability": 0.825,
  "energy": 0.652,
  "valence": 0.931,
  "tempo": 95.977,
  ...
}
```

### 2. user_interactions

Guarda todas las interacciones en tiempo real.

Ejemplo de documento:
```json
{
  "user_id": "usuario_demo",
  "track_id": "5SuOikwiRyPMVoIQDJUgSV",
  "interaction_type": "like",
  "timestamp": ISODate("2024-10-30T14:30:00Z")
}
```

### 3. track_popularity

Mantiene la popularidad actualizada de cada canción.

Ejemplo de documento:
```json
{
  "track_id": "5SuOikwiRyPMVoIQDJUgSV",
  "popularity": 15,
  "updated_at": ISODate("2024-10-30T14:35:00Z")
}
```

## Límites del Plan Gratuito

MongoDB Atlas M0 (gratis) incluye:

- **Almacenamiento**: 512 MB
- **RAM**: 512 MB compartida
- **Conexiones**: 500 simultáneas
- **Backups**: No incluidos (pero puedes exportar manualmente)

Para este proyecto, 512 MB es más que suficiente:
- 4,832 canciones ≈ 2 MB
- 10,000 interacciones ≈ 1 MB
- Total: < 5 MB

## Troubleshooting

### Error: "Authentication failed"

Verifica que:
1. El usuario y contraseña sean correctos
2. Hayas reemplazado `<password>` en la URI
3. El usuario tenga permisos de lectura/escritura

### Error: "Connection timeout"

Verifica que:
1. Hayas agregado tu IP en "Network Access"
2. O hayas agregado `0.0.0.0/0` para permitir todas las IPs
3. Tu firewall no esté bloqueando MongoDB (puerto 27017)

### Error: "No se encontró el archivo dataset.csv"

```bash
# Copiar el dataset
cp /ruta/al/dataset.csv ~/spotify-kappa-mongodb/data/
```

### Error: "ModuleNotFoundError: No module named 'pymongo'"

```bash
pip3 install pymongo
```

## Seguridad

### Recomendaciones

1. **No compartas tu URI**: Contiene tu contraseña
2. **Usa variables de entorno**: No pongas la URI en el código
3. **Restringe IPs**: Si es posible, solo permite tu IP
4. **Usa contraseñas fuertes**: Genera contraseñas seguras
5. **Rota credenciales**: Cambia la contraseña periódicamente

### Cambiar Contraseña

1. Ve a "Database Access" en MongoDB Atlas
2. Haz clic en "Edit" en tu usuario
3. Haz clic en "Edit Password"
4. Genera una nueva contraseña
5. Actualiza tu URI en la aplicación

## Monitoreo

### Ver Actividad en MongoDB Atlas

1. Ve a tu cluster
2. Haz clic en **"Metrics"**
3. Verás gráficas de:
   - Conexiones
   - Operaciones por segundo
   - Uso de red
   - Uso de almacenamiento

### Ver Logs

1. Ve a **"Logs"** en el menú izquierdo
2. Verás todas las operaciones realizadas

## Backup Manual

Para hacer backup de tus datos:

1. Ve a tu cluster
2. Haz clic en **"Browse Collections"**
3. Selecciona una colección
4. Haz clic en **"Export Collection"**
5. Descarga el archivo JSON

## Próximos Pasos

Una vez configurado MongoDB Atlas:

1. Ejecuta la migración de datos
2. Inicia la aplicación Streamlit
3. Prueba las recomendaciones
4. Verifica que las interacciones se guarden en MongoDB
5. Observa el trending actualizándose en tiempo real

## Recursos Adicionales

- Documentación oficial: https://docs.mongodb.com/
- MongoDB Atlas: https://www.mongodb.com/cloud/atlas
- PyMongo: https://pymongo.readthedocs.io/
