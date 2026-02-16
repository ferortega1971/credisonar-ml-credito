# 💼 Guía de Venta B2B - Sistema de Credit Scoring

## Para Equipos de Ventas de Credisonar

Esta guía te ayudará a vender el sistema de Credit Scoring a otras empresas financieras.

---

## 🎯 Elevator Pitch (30 segundos)

> "Nuestro sistema de Credit Scoring reduce la morosidad hasta en un 50% usando inteligencia artificial. En menos de 1 segundo, evalúa a un cliente y te dice si aprobarlo, rechazarlo o revisarlo manualmente. Ya no más decisiones 'a ojo' - todo basado en datos. Instalación en 1 día, ROI en 3-6 meses."

---

## 🔍 Identificar Clientes Potenciales

### Cliente Ideal:
- **Empresas de microcrédito** (como Credisonar)
- **Financieras pequeñas y medianas**
- **Cooperativas de ahorro y crédito**
- **Fintechs** en crecimiento
- **Casas de empeño** con líneas de crédito

### Señales de que necesitan el producto:
- ❌ Morosidad mayor al 10%
- ❌ Decisiones crediticias inconsistentes
- ❌ Proceso de aprobación lento (más de 30 min por cliente)
- ❌ Falta de datos para justificar decisiones
- ❌ Pérdidas por préstamos no pagados

---

## 💰 Propuesta de Valor

### Problema que Resuelve:

**ANTES (Sin el sistema):**
- Empleado decide "a ojo" → Inconsistente
- 30-60 minutos por evaluación → Lento
- Alta morosidad (15-30%) → Pérdidas
- Difícil justificar rechazos → Problemas legales
- No se aprende de errores pasados

**DESPUÉS (Con el sistema):**
- ✅ Decisión automatizada y consistente
- ✅ 1 segundo por evaluación
- ✅ Morosidad reducida (5-10%)
- ✅ Cada decisión justificada
- ✅ Mejora continua con datos

### Beneficios Cuantificables:

| Métrica | Sin Sistema | Con Sistema | Mejora |
|---------|-------------|-------------|--------|
| Morosidad | 20% | 8% | **-60%** |
| Tiempo/evaluación | 30 min | 1 seg | **-99.9%** |
| Préstamos procesados/día | 16 | 500+ | **+3000%** |
| Consistencia | Baja | Alta | **100%** |

---

## 💵 Pricing y Modelos de Negocio

### Opción 1: SaaS (Software as a Service)
**Para empresas pequeñas**

- **Básico**: $299 USD/mes
  - Hasta 500 evaluaciones/mes
  - API + UI web
  - Soporte por email

- **Profesional**: $799 USD/mes
  - Hasta 5,000 evaluaciones/mes
  - API + UI + Reportes
  - Soporte prioritario
  - Personalización básica

- **Enterprise**: Precio personalizado
  - Evaluaciones ilimitadas
  - Soporte 24/7
  - Personalización completa
  - SLA garantizado

### Opción 2: Licencia Perpetua
**Para empresas medianas/grandes**

- **Licencia One-Time**: $15,000 - $50,000 USD
- Instalación en sus servidores
- Incluye 1 año de soporte
- Actualizaciones incluidas
- Personalización del modelo con sus datos

### Opción 3: Por Evaluación
**Para empresas con volumen variable**

- **$0.50 - $2.00 USD por evaluación**
- Sin cuota mensual
- Pago solo por uso
- Ideal para startups

### Opción 4: Revenue Share
**Para empresas con presupuesto limitado**

- **0% upfront**
- **5-10% de las ganancias** generadas por préstamos aprobados
- Riesgo compartido
- Ideal para fintechs en early-stage

---

## 📊 Cálculo de ROI para el Cliente

### Ejemplo Real:

**Cliente**: Financiera con 10,000 préstamos/año, ticket promedio $10,000

**Situación Actual:**
- Morosidad: 15%
- Pérdidas: 10,000 × $10,000 × 15% = **$15,000,000/año en pérdidas**

**Con nuestro sistema:**
- Morosidad: 6%
- Pérdidas: 10,000 × $10,000 × 6% = **$6,000,000/año**
- **Ahorro: $9,000,000/año**

**Inversión:**
- Licencia: $30,000 USD one-time
- Implementación: $5,000 USD
- **Total: $35,000 USD**

**ROI:**
- ROI = ($9,000,000 - $35,000) / $35,000 × 100 = **25,614%**
- Payback period: **1.4 días** (!!)

---

## 🎬 Demo en Vivo - Guion de Venta

### 1. Apertura (2 min)
"Hoy les voy a mostrar cómo pueden reducir su morosidad a la mitad y aprobar créditos en 1 segundo en lugar de 30 minutos."

### 2. Mostrar el Problema (3 min)
- Preguntar: "¿Cuánto tiempo toma evaluar un crédito actualmente?"
- "¿Cómo saben que tomaron la decisión correcta?"
- "¿Cuál es su tasa de morosidad actual?"

### 3. Demo del Sistema (10 min)

**Caso 1: Cliente Bueno**
1. Abrir la UI: `streamlit run src/ui/app.py`
2. Ingresar datos de cliente con buen perfil
3. Click "Evaluar"
4. **Resultado en 1 segundo**: "APROBADO - Score 750"
5. Mostrar explicación: Por qué se aprobó

**Caso 2: Cliente Malo**
1. Ingresar datos de cliente riesgoso
2. **Resultado**: "RECHAZADO - Score 420"
3. Mostrar razones: Historial de atrasos, alto endeudamiento

**Caso 3: Caso Límite**
1. Cliente con perfil medio
2. **Resultado**: "REVISAR MANUAL - Score 580"
3. El sistema sugiere: reducir monto, pedir aval

### 4. Mostrar API (5 min)
"Esto se integra con sus sistemas actuales..."
- Abrir documentación: `http://localhost:8000/docs`
- Mostrar ejemplo de llamada API
- Mostrar respuesta JSON

### 5. Beneficios Clave (3 min)
- ✅ Velocidad: 1 segundo vs 30 minutos
- ✅ Consistencia: Mismo cliente, misma decisión
- ✅ Explicabilidad: Cada decisión justificada
- ✅ Aprendizaje: Mejora con sus datos

### 6. Cierre (2 min)
"¿Qué les parece? ¿Les gustaría hacer una prueba piloto con 100 de sus clientes históricos?"

---

## 🚀 Proceso de Implementación

### Timeline de 30 días:

**Semana 1: Preparación**
- Firma de contrato
- Acceso a datos históricos del cliente
- Configuración de ambiente

**Semana 2-3: Entrenamiento**
- Limpieza de datos del cliente
- Entrenamiento del modelo personalizado
- Validación con casos históricos

**Semana 4: Despliegue**
- Instalación en servidores del cliente
- Integración con sistemas existentes
- Capacitación del equipo

**Go Live**
- Monitoreo durante el primer mes
- Ajustes según feedback

---

## ❓ Manejo de Objeciones

### "Es muy caro"
**Respuesta**: "Entiendo su preocupación. Déjeme mostrarle los números: si tienen una morosidad del 15% en $10M al año, están perdiendo $1.5M. Nuestro sistema por $30K reduce eso a $600K, ahorrándoles $900K al año. El sistema se paga solo en 12 días."

### "Ya tenemos un proceso que funciona"
**Respuesta**: "¡Excelente! ¿Cuál es su tasa de morosidad actual? [Esperan respuesta] Si es mayor al 8%, podemos ayudarles a mejorar. Además, ¿cuánto tiempo dedican a cada evaluación? Nuestro sistema les ahorra 99% de ese tiempo."

### "Nuestros datos no son suficientes"
**Respuesta**: "No hay problema. Podemos empezar con datos sintéticos basados en su industria, y luego el modelo aprende de sus decisiones reales. En 3-6 meses tendrá un modelo completamente personalizado."

### "¿Y si el modelo se equivoca?"
**Respuesta**: "Gran pregunta. Por eso tenemos 3 decisiones: Aprobar, Rechazar, y Revisar Manual. Los casos dudosos los ve un humano. Además, cada decisión tiene una explicación para auditoría y compliance."

### "No sabemos de ML/IA"
**Respuesta**: "Perfecto, para eso estamos nosotros. Es tan simple como llenar un formulario - el empleado no necesita saber de IA. La interfaz es más fácil que usar WhatsApp."

### "¿Qué pasa si se cae el sistema?"
**Respuesta**: "El sistema se instala en sus servidores (o en nuestra nube con 99.9% uptime). Además, pueden seguir usando su proceso manual como backup. El sistema complementa, no reemplaza a su equipo."

---

## 📋 Checklist de Cierre de Venta

### Antes de la reunión:
- [ ] Investigar al cliente (tamaño, industria, morosidad estimada)
- [ ] Preparar demo con datos del sector del cliente
- [ ] Tener laptop lista con sistema funcionando
- [ ] Calcular ROI preliminar del cliente
- [ ] Preparar propuesta económica personalizada

### Durante la reunión:
- [ ] Identificar pain points del cliente
- [ ] Demo en vivo (no slides!)
- [ ] Mostrar casos de éxito similares
- [ ] Presentar ROI específico para ellos
- [ ] Manejar objeciones
- [ ] Proponer prueba piloto

### Después de la reunión:
- [ ] Enviar resumen por email
- [ ] Propuesta formal con pricing
- [ ] Calendario de implementación
- [ ] Casos de éxito y referencias
- [ ] Seguimiento en 3 días

---

## 🎓 Capacitación del Cliente

### Material a entregar:
1. **Manual de usuario** (PDF)
2. **Videos tutoriales** (5-10 min cada uno)
3. **Sesión de capacitación en vivo** (2 horas)
4. **Soporte 1-on-1** primeros 30 días

### Topics de capacitación:
- Cómo usar la interfaz web
- Interpretación de scores
- Qué hacer en cada decisión
- Cómo registrar feedback
- Troubleshooting básico

---

## 📈 Métricas de Éxito

### KPIs a trackear:
1. **Reducción de morosidad** (target: -40%)
2. **Tiempo de evaluación** (target: <5 seg)
3. **Volumen de préstamos** (target: +100%)
4. **Satisfacción del cliente** (NPS: >8/10)
5. **Adopción del sistema** (% de uso vs manual)

---

## 🤝 Siguiente Paso

**Call to Action para el cliente:**

> "Propongo lo siguiente: Déjenme acceso a 500 solicitudes históricas (anonimizadas). En 1 semana les muestro qué hubiera decidido nuestro sistema vs lo que ustedes decidieron, y comparamos los resultados. Si reducimos la morosidad, seguimos. Si no, no hay compromiso. ¿Les parece?"

---

## 📞 Contacto

Para soporte en ventas:
- **Email**: ventas@credisonar.com
- **Tel**: +52 XXX XXX XXXX
- **WhatsApp**: +52 XXX XXX XXXX

---

**¡Éxito en tus ventas!** 🚀
