# 🚀 Desplegar Sistema ML de Crédito en Streamlit Cloud (GRATIS)

## ¿Qué es Streamlit Cloud?
Es el servicio oficial y GRATUITO de Streamlit para hospedar aplicaciones web. Tu secretaria podrá acceder desde cualquier navegador con una URL tipo: `https://tu-app.streamlit.app`

---

## 📋 Requisitos Previos

1. ✅ Cuenta de GitHub (gratis)
2. ✅ Cuenta de Streamlit Cloud (gratis)
3. ✅ Credenciales de tu MySQL en GoDaddy

---

## 🔧 PASO 1: Crear cuenta en GitHub

1. Ve a https://github.com/signup
2. Crea tu cuenta (usa tu email)
3. Verifica tu email

---

## 🔧 PASO 2: Subir el código a GitHub

### Opción A: Desde GitHub Desktop (MÁS FÁCIL)

1. **Descargar GitHub Desktop:**
   - Ve a https://desktop.github.com/
   - Instala la aplicación

2. **Configurar:**
   - Abre GitHub Desktop
   - Ve a File > Options > Sign in
   - Inicia sesión con tu cuenta de GitHub

3. **Crear repositorio:**
   - File > New Repository
   - **Name:** `credisonar-ml-credito`
   - **Local Path:** `C:\Desarrollos\projectos2026\proyecto1ML`
   - ✅ Make this private (MUY IMPORTANTE)
   - Click "Create Repository"

4. **Publicar a GitHub:**
   - Click en "Publish repository"
   - ✅ Verifica que esté marcado "Keep this code private"
   - Click "Publish Repository"

### Opción B: Desde línea de comandos

```bash
cd C:\Desarrollos\projectos2026\proyecto1ML
git init
git add .
git commit -m "Sistema ML de Crédito - Versión inicial"
git branch -M main
# Crea el repo en GitHub primero, luego:
git remote add origin https://github.com/TU_USUARIO/credisonar-ml-credito.git
git push -u origin main
```

---

## 🔧 PASO 3: Crear cuenta en Streamlit Cloud

1. Ve a https://streamlit.io/cloud
2. Click en "Sign up"
3. **Selecciona "Continue with GitHub"** (esto es importante)
4. Autoriza Streamlit para acceder a tu GitHub

---

## 🔧 PASO 4: Desplegar la aplicación

1. **En Streamlit Cloud dashboard:**
   - Click "New app"

2. **Configurar el deploy:**
   - **Repository:** `TU_USUARIO/credisonar-ml-credito`
   - **Branch:** `main`
   - **Main file path:** `app_prediccion_v3.py`
   - **App URL (opcional):** `credisonar-creditos` (personaliza la URL)

3. **Configurar SECRETS (MUY IMPORTANTE):**
   - Click en "Advanced settings"
   - En la sección "Secrets", pega esto:

   ```toml
   [mysql]
   host = "92.204.216.38"
   port = 3306
   database = "sigcrec10"
   user = "sigcrec_user"
   password = "Skidata2013*"
   ```

   > ⚠️ **IMPORTANTE:** Estos secrets NO se subirán a GitHub, quedan solo en Streamlit Cloud

4. **Deploy:**
   - Click "Deploy!"
   - Espera 2-5 minutos mientras instala dependencias
   - ¡Listo! Tendrás una URL como: `https://credisonar-creditos.streamlit.app`

---

## 🔧 PASO 5: Probar la aplicación

1. Abre la URL generada
2. Ingresa una cédula de prueba: `12748551`
3. Completa los datos y verifica que funcione

---

## 📱 PASO 6: Compartir con tu secretaria

1. **Copia la URL:** `https://credisonar-creditos.streamlit.app`
2. Envíala a tu secretaria por WhatsApp/Email
3. Ella podrá acceder desde:
   - Su computadora (Chrome, Edge, Firefox)
   - Su celular (navegador móvil)
   - Tablet

> 💡 **TIP:** Puede agregarla a favoritos o crear un acceso directo en el escritorio

---

## 🔄 Actualizar la aplicación

Cuando hagas cambios al código:

**Con GitHub Desktop:**
1. Abre GitHub Desktop
2. Verás los archivos modificados
3. Escribe un resumen: "Mejoras en validación"
4. Click "Commit to main"
5. Click "Push origin"
6. ¡Streamlit Cloud se actualiza automáticamente en 1-2 minutos!

**Con línea de comandos:**
```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

---

## ⚠️ Limitaciones del plan GRATUITO

- ✅ 1 app privada gratis
- ✅ 1 GB de RAM
- ✅ 1 CPU compartido
- ✅ Uso ilimitado (horas)
- ⚠️ Si la app no se usa por 7 días, "hiberna" (se reactiva al visitarla)
- ⚠️ Para 1-10 usuarios simultáneos está perfecto

---

## 🆘 Problemas comunes

### Error: "Module not found"
- **Solución:** Verifica que `requirements.txt` esté en la raíz del repo
- Re-despliega desde Streamlit Cloud: Settings > Reboot app

### Error de conexión a MySQL
- **Solución:** Verifica que los secrets estén bien escritos
- Verifica que GoDaddy permita conexiones desde IP externa
- En GoDaddy cPanel > Remote MySQL > Add `%` (permitir todas las IPs)

### App muy lenta
- **Normal:** Primera carga es lenta (carga el modelo ML)
- **Solución:** Considera reducir el tamaño del modelo si es muy pesado

### "This app has gone to sleep"
- **Normal:** La app hibernó por inactividad
- **Solución:** Click "Yes, get this app back up!" - tarda 30 segundos

---

## 🔐 Seguridad

✅ **Tu código está seguro:**
- Repo privado en GitHub (solo tú lo ves)
- Secrets en Streamlit Cloud (encriptados)
- No compartes credenciales de MySQL en el código

⚠️ **Importante:**
- NO hagas el repo público (tiene código de negocio sensible)
- Cambia la contraseña de MySQL periódicamente
- Si quieres restringir acceso, considera usar autenticación

---

## 💰 ¿Y si necesito más recursos?

Si la app crece y necesitas más poder:
- **Streamlit Community Cloud:** Gratis (lo que estás usando)
- **Streamlit for Teams:** $250/mes (múltiples apps, más recursos, SSO)
- **Alternativas:**
  - Railway.app (gratis con límites)
  - Render.com (gratis con límites)
  - Heroku ($7/mes)

---

## 📞 Soporte

- **Documentación oficial:** https://docs.streamlit.io/streamlit-community-cloud
- **Foro comunidad:** https://discuss.streamlit.io/
- **GitHub Issues:** Para reportar bugs del proyecto

---

## ✅ Checklist final

- [ ] Cuenta GitHub creada
- [ ] Código subido a repo privado
- [ ] Cuenta Streamlit Cloud creada
- [ ] Secrets configurados correctamente
- [ ] App desplegada y funcionando
- [ ] Probada con cédula real
- [ ] URL compartida con secretaria
- [ ] Secretaria probó y funciona

---

¡LISTO! Tu sistema ML está en la nube y accesible 24/7. 🎉
