# 🚀 Cómo Empezar - Guía Rápida

## En 3 Pasos Simples

### ⚡ Opción Rápida (5 minutos)

Ejecuta este archivo en Windows:
```
quick_start.bat
```

Eso es todo! El sistema:
1. Instalará dependencias
2. Entrenará el modelo
3. Abrirá la interfaz web

---

### 📝 Opción Manual

#### Paso 1: Instalar dependencias
```bash
pip install -r requirements.txt
```

#### Paso 2: Entrenar el modelo
```bash
python train_model.py
```

#### Paso 3: Ejecutar la interfaz
```bash
streamlit run src/ui/app.py
```

#### Abrir navegador
```
http://localhost:8501
```

---

## 🎯 ¿Qué Puedes Hacer?

### 1️⃣ Evaluar Clientes (UI Web)
La forma más fácil de probar el sistema:
1. Abre `http://localhost:8501`
2. Llena formulario con datos del cliente
3. Click "EVALUAR SOLICITUD"
4. Ver resultado instantáneo

### 2️⃣ Usar la API (Integración)
Para integrar con otros sistemas:
```bash
python src/api/main.py
```
Luego ve a `http://localhost:8000/docs`

### 3️⃣ Probar la API
```bash
python test_api.py
```

---

## 📊 Datos de Prueba

El sistema viene con **1000 registros sintéticos** en:
```
data/raw/credit_data_synthetic.csv
```

### ¿Quieres usar tus propios datos?

1. Crea archivo CSV con tus datos históricos
2. Ponlo en `data/raw/mis_datos.csv`
3. Edita `train_model.py` línea 25
4. Ejecuta `python train_model.py`

---

## 📱 Casos de Uso

### En la Oficina:
1. Cliente llega y solicita préstamo
2. Empleado abre la UI
3. Captura datos básicos
4. Sistema decide en 1 segundo
5. Empleado procede según resultado

### Integrado en Sistema:
```python
import requests

datos_cliente = {...}
respuesta = requests.post(
    "http://localhost:8000/evaluar",
    json=datos_cliente
)
print(respuesta.json()['decision'])
```

---

## 🆘 Solución de Problemas

### Error: "Modelo no encontrado"
**Solución**: Ejecuta primero `python train_model.py`

### Error: "Module not found"
**Solución**: Instala dependencias `pip install -r requirements.txt`

### Puerto 8501 en uso
**Solución**: Cierra otras instancias de Streamlit o usa otro puerto:
```bash
streamlit run src/ui/app.py --server.port 8502
```

### API no responde
**Solución**: Verifica que esté corriendo `python src/api/main.py`

---

## 📚 Documentación

- **README.md**: Documentación completa
- **GUIA_VENTA_B2B.md**: Para vender el producto
- **Código fuente**: Carpeta `src/`

---

## 💡 Ejemplos de Clientes

### Cliente Bueno (será APROBADO):
- Edad: 35
- Ingreso: $30,000
- Historial: 100% puntualidad
- Préstamos pagados: 3/3

### Cliente Malo (será RECHAZADO):
- Edad: 25
- Ingreso: $8,000
- Historial: 40% puntualidad
- Atrasos: 45 días promedio

### Cliente Medio (REVISAR MANUAL):
- Edad: 30
- Ingreso: $18,000
- Historial: 75% puntualidad
- Cliente nuevo: 3 meses

---

## 🎓 Próximos Pasos

1. ✅ **Probar el sistema** con datos de ejemplo
2. ✅ **Entrenar con tus datos** reales
3. ✅ **Integrar con tu sistema** vía API
4. ✅ **Personalizar** scores y tasas en `config/config.yaml`
5. ✅ **Deploy a producción** (Docker, cloud, etc.)

---

## 🤝 Soporte

¿Necesitas ayuda?
- 📧 Email: soporte@credisonar.com
- 📱 WhatsApp: +52 XXX XXX XXXX
- 📖 Docs: README.md

---

**¡Listo para empezar!** 🎉

Ejecuta: `python train_model.py`
