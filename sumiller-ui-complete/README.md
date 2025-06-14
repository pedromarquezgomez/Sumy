# Sumiller UI - Interfaz de Usuario Completa

Esta es la interfaz de usuario completa y autoportante del Sumiller Digital con integración Firebase.

## 🎯 Características

- **Vue.js 3** con Composition API
- **Firebase Authentication** con Google Sign-In
- **Firestore** para almacenamiento de conversaciones
- **Diseño responsivo** con Tailwind CSS
- **Chat en tiempo real** con el Sumiller Digital
- **Historial de conversaciones** persistente

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
npm install
```

### 2. Configuración de Firebase
El archivo `.env` ya está configurado con el proyecto `maitre-ia`:

```bash
VITE_MAITRE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=AIzaSyCyslmRlkyaQjQjqBgU__5EwDTwbElMSUE
VITE_FIREBASE_AUTH_DOMAIN=maitre-ia.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=maitre-ia
# ... más configuraciones
```

### 3. Ejecutar en Desarrollo
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

### 4. Construir para Producción
```bash
npm run build
```

## 🔧 Configuración del Backend

La UI está configurada para conectarse al backend del Sumiller en:
- **Desarrollo**: `http://localhost:8000`
- **Producción**: Configurar `VITE_MAITRE_URL` en `.env`

## 🐳 Docker

### Construir imagen
```bash
docker build -t sumiller-ui .
```

### Ejecutar contenedor
```bash
docker run -p 3000:80 sumiller-ui
```

## 🔥 Firebase

### Configuración requerida en Firebase Console:

1. **Authentication**:
   - Habilitar Google Sign-In
   - Agregar dominios autorizados

2. **Firestore**:
   - Crear base de datos
   - Configurar reglas de seguridad

3. **Hosting** (opcional):
   ```bash
   npm install -g firebase-tools
   firebase login
   firebase deploy
   ```

## 📁 Estructura del Proyecto

```
sumiller-ui-complete/
├── src/
│   ├── App.vue              # Componente principal
│   │   ├── Login.vue        # Componente de login
│   │   └── ConversationHistory.vue
│   └── main.js              # Punto de entrada
├── public/                  # Archivos estáticos
├── .env                     # Variables de entorno
├── .firebaserc             # Configuración Firebase CLI
├── firebase.json           # Configuración de hosting
├── Dockerfile              # Imagen Docker
├── package.json            # Dependencias
└── vite.config.ts          # Configuración Vite
```

## 🎨 Funcionalidades

### Autenticación
- Login con Google
- Persistencia de sesión
- Logout seguro

### Chat
- Interfaz conversacional
- Respuestas estructuradas del Sumiller
- Indicadores de carga
- Manejo de errores

### Historial
- Guardado automático en Firestore
- Recuperación de conversaciones
- Asociación por usuario

## 🔒 Seguridad

- Variables de entorno para configuración sensible
- Autenticación requerida para usar el chat
- Reglas de Firestore para proteger datos
- Validación de tokens en el backend

## 🚀 Despliegue

### Firebase Hosting
```bash
npm run build
firebase deploy
```

### Docker
```bash
docker build -t sumiller-ui .
docker run -p 80:80 sumiller-ui
```

### Vercel/Netlify
1. Conectar repositorio
2. Configurar variables de entorno
3. Deploy automático

## 📊 Monitoreo

- Firebase Analytics configurado
- Logs de errores en consola
- Métricas de uso en Firebase Console

## 🛠️ Desarrollo

### Scripts disponibles:
- `npm run dev` - Servidor de desarrollo
- `npm run build` - Construir para producción
- `npm run preview` - Vista previa de build
- `npm run lint` - Linter de código

### Tecnologías:
- Vue.js 3
- TypeScript
- Vite
- Tailwind CSS
- Firebase SDK
- Axios

¡La aplicación está lista para usar! 🍷 