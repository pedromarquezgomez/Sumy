# 🚀 Inicio Rápido - Sumiller UI

## ⚡ Ejecutar en 3 pasos

### 1. Instalar dependencias
```bash
npm install
```

### 2. Ejecutar aplicación
```bash
npm run dev
```

### 3. Abrir navegador
```
http://localhost:5173
```

## 🔥 Firebase ya configurado

✅ **Proyecto**: maitre-ia  
✅ **Autenticación**: Google Sign-In habilitado  
✅ **Firestore**: Base de datos configurada  
✅ **Variables**: Archivo `.env` incluido  

## 🎯 Funcionalidades listas

- **Login con Google** - Clic en "Iniciar Sesión"
- **Chat con Sumiller** - Pregunta sobre vinos
- **Historial** - Se guarda automáticamente
- **Responsive** - Funciona en móvil y desktop

## 🐳 Docker (alternativo)

```bash
# Construir
docker build -t sumiller-ui .

# Ejecutar
docker run -p 3000:80 sumiller-ui
```

## 🔧 Backend requerido

La UI necesita el backend del Sumiller ejecutándose en:
```
http://localhost:8000
```

## 📱 Uso

1. **Abrir** `http://localhost:5173`
2. **Login** con cuenta de Google
3. **Chatear** con el Sumiller Digital
4. **Disfrutar** las recomendaciones de vinos 🍷

¡Listo para usar! 🎉 