import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import sqlite3
import math
from datetime import datetime
import requests
import os
from io import BytesIO

# CONFIGURACIÓN - Usar variables de entorno
TOKEN = os.getenv('TOKEN')
ADMIN_USERS = [int(x) for x in os.getenv('ADMIN_USERS', '123456789').split(',')]
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

# Estados para las conversaciones
RIESGO_INPUT, COMENTARIO_INPUT, FOTO_INPUT = range(3)

class BotSocavones:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Configura la base de datos SQLite"""
        self.conn = sqlite3.connect('socavones_bot.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                fugas_agua REAL,
                humedad_suelo REAL,
                nivel_freatico REAL,
                mantenimiento REAL,
                riesgo_calculado REAL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                comentario TEXT,
                tipo TEXT,
                ubicacion TEXT,
                foto_url TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida"""
        user = update.effective_user
        welcome_text = f"""
🚧 SISTEMA DE ALERTA TEMPRANA - SOCAVONES IZTAPALAPA 🚧

¡Hola {user.first_name}! Soy tu asistente para monitoreo de riesgo de socavones.

📍 *Col. José López Portillo, Iztapalapa*
📊 *Basado en análisis estadístico 2022-2024*
🔄 *Bot siempre activo - 24/7*

*Comandos disponibles:*
/calcular - Calcular riesgo de socavones
/reporte - Ver mi último reporte
/info - Información importante y emergencias
/comentario - Reportar observaciones o fugas (con foto)
/help - Ayuda e información
        """
        
        keyboard = [
            ["/calcular", "/reporte"],
            ["/info", "/comentario"],
            ["/help"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /info - Información importante"""
        info_text = """
🔍 *INFORMACIÓN IMPORTANTE - BASADA EN ANÁLISIS CIENTÍFICO*

📊 *FACTORES CLAVE IDENTIFICADOS:*

1️⃣ *FUGAS DE AGUA* 🚰
• Correlación: +0.96 (MUY ALTA)
• Las fugas erosionan el subsuelo

2️⃣ *HUMEDAD DEL SUELO* 💧
• Correlación: +0.95 (MUY ALTA)
• Suelos arcillosos más inestables

3️⃣ *NIVEL FREÁTICO* 📉
• Correlación: -0.96 (MUY ALTA)
• Nivel profundo = suelo quebradizo

🚨 *TELÉFONOS DE EMERGENCIA:*
• Protección Civil: 911
• Sistema de Aguas: 5654-3210
• Locatel: 5658-1111

*📍 Col. José López Portillo, Iztapalapa*
        """
        await update.message.reply_text(info_text, parse_mode='Markdown')

    async def comentario_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el proceso para reportar comentarios"""
        instruction_text = """
📝 *SISTEMA DE REPORTES CON FOTO*

Puedes reportar:
• Fugas de agua visibles
• Hundimientos o grietas
• Socavones detectados

*¿Quieres incluir una foto?*
Las fotos ayudan a la verificación.

Selecciona una opción:
        """
        keyboard = [
            ["📝 Solo texto", "📸 Texto y foto"],
            ["❌ Cancelar"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            instruction_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return COMENTARIO_INPUT

    async def procesar_opcion_comentario(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa la opción seleccionada para el comentario"""
        opcion = update.message.text
        
        if opcion == "📝 Solo texto":
            await update.message.reply_text(
                "✍️ *Modo solo texto*\n\nPor favor escribe tu comentario:",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return COMENTARIO_INPUT
            
        elif opcion == "📸 Texto y foto":
            await update.message.reply_text(
                "📸 *Modo texto con foto*\n\nPrimero escribe tu comentario, luego podrás adjuntar una foto:",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['con_foto'] = True
            return COMENTARIO_INPUT
            
        else:
            await update.message.reply_text("Operación cancelada.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    async def procesar_comentario(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa los comentarios reportados por usuarios"""
        try:
            comentario = update.message.text.strip()
            user_id = update.effective_user.id
            
            if len(comentario) < 10:
                await update.message.reply_text("❌ El comentario es muy corto. Por favor proporciona más detalles.")
                return COMENTARIO_INPUT
            
            context.user_data['comentario_temp'] = comentario
            
            if context.user_data.get('con_foto'):
                await update.message.reply_text(
                    "📸 *Ahora puedes enviar la foto*\n\nToma una foto o selecciona una de tu galería.\nEscribe /saltar si no quieres adjuntar foto.",
                    parse_mode='Markdown'
                )
                return FOTO_INPUT
            else:
                return await self.finalizar_comentario(update, context, comentario, None)
            
        except Exception as e:
            logging.error(f"Error procesando comentario: {e}")
            await update.message.reply_text("❌ Error al procesar el comentario. Intenta nuevamente.")
            return ConversationHandler.END

    async def procesar_foto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa la foto enviada por el usuario"""
        try:
            if update.message.text and update.message.text.lower() == '/saltar':
                comentario = context.user_data.get('comentario_temp')
                if comentario:
                    return await self.finalizar_comentario(update, context, comentario, None)
                else:
                    await update.message.reply_text("❌ Primero debes escribir un comentario.")
                    return COMENTARIO_INPUT
            
            photo_file = await update.message.photo[-1].get_file()
            foto_url = await self.subir_foto_a_cloud(photo_file)
            
            comentario = context.user_data.get('comentario_temp')
            if comentario:
                return await self.finalizar_comentario(update, context, comentario, foto_url)
            else:
                await update.message.reply_text("❌ Error: No se encontró el comentario.")
                return ConversationHandler.END
                
        except Exception as e:
            logging.error(f"Error procesando foto: {e}")
            await update.message.reply_text("❌ Error al procesar la foto. Intenta nuevamente o escribe /saltar.")
            return FOTO_INPUT

    async def subir_foto_a_cloud(self, photo_file):
        """Sube la foto a ImgBB"""
        try:
            photo_bytes = BytesIO()
            await photo_file.download_to_memory(photo_bytes)
            photo_bytes.seek(0)
            
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                files={'image': photo_bytes},
                data={'key': IMGBB_API_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['url']
            else:
                logging.error(f"Error subiendo foto: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error en subir_foto_a_cloud: {e}")
            return None

    async def finalizar_comentario(self, update: Update, context: ContextTypes.DEFAULT_TYPE, comentario: str, foto_url: str = None):
        """Finaliza el proceso de comentario"""
        try:
            user_id = update.effective_user.id
            tipo_reporte = self.clasificar_comentario(comentario)
            
            self.guardar_comentario(user_id, comentario, tipo_reporte, foto_url)
            respuesta = self.generar_respuesta_reporte(tipo_reporte, comentario, foto_url)
            
            if 'comentario_temp' in context.user_data:
                del context.user_data['comentario_temp']
            if 'con_foto' in context.user_data:
                del context.user_data['con_foto']
            
            if foto_url:
                await update.message.reply_photo(
                    photo=foto_url,
                    caption=respuesta,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(respuesta, parse_mode='Markdown')
            
            if tipo_reporte in ["FUGA_AGUA", "SOCAVON", "HUNDIMIENTO"]:
                await self.notificar_administradores(context, user_id, comentario, tipo_reporte, foto_url)
            
            return ConversationHandler.END
            
        except Exception as e:
            logging.error(f"Error finalizando comentario: {e}")
            await update.message.reply_text("❌ Error al guardar el comentario.")
            return ConversationHandler.END

    def clasificar_comentario(self, comentario):
        """Clasifica el tipo de reporte"""
        comentario_lower = comentario.lower()
        
        if any(palabra in comentario_lower for palabra in ['fuga', 'agua', 'tubería', 'escape']):
            return "FUGA_AGUA"
        elif any(palabra in comentario_lower for palabra in ['socavón', 'socavon', 'hoyo', 'hundimiento']):
            return "SOCAVON"
        elif any(palabra in comentario_lower for palabra in ['grieta', 'fisura', 'agrietamiento']):
            return "GRIETA"
        else:
            return "OBSERVACION"

    def guardar_comentario(self, user_id, comentario, tipo_reporte, foto_url=None):
        """Guarda el comentario en la base de datos"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO comentarios (user_id, comentario, tipo, foto_url)
            VALUES (?, ?, ?, ?)
        ''', (user_id, comentario, tipo_reporte, foto_url))
        self.conn.commit()

    def generar_respuesta_reporte(self, tipo_reporte, comentario, foto_url=None):
        """Genera respuesta personalizada"""
        base_respuestas = {
            "FUGA_AGUA": "✅ *REPORTE DE FUGA REGISTRADO*\n\nAcciones: Mantener distancia, reportar al 5654-3210",
            "SOCAVON": "🚨 *REPORTE DE SOCAVÓN REGISTRADO*\n\nAcciones: Alejarse, llamar al 911",
            "GRIETA": "⚠️ *REPORTE DE GRIETA REGISTRADO*\n\nRecomendaciones: Monitorear crecimiento",
            "OBSERVACION": "📝 *COMENTARIO REGISTRADO*\n\nGracias por tu contribución"
        }
        
        respuesta = base_respuestas.get(tipo_reporte, base_respuestas["OBSERVACION"])
        respuesta += f"\n\n*Tu comentario:* \"{comentario}\""
        respuesta += f"\n*📸 Foto adjunta:* {'Sí' if foto_url else 'No'}"
        
        return respuesta

    async def notificar_administradores(self, context, user_id, comentario, tipo_reporte, foto_url=None):
        """Notifica a los administradores"""
        try:
            for admin_id in ADMIN_USERS:
                mensaje = f"🚨 *REPORTE URGENTE - {tipo_reporte}*\n\nUsuario: {user_id}\nComentario: {comentario}\nFoto: {'Sí' if foto_url else 'No'}"
                
                if foto_url:
                    await context.bot.send_photo(chat_id=admin_id, photo=foto_url, caption=mensaje, parse_mode='Markdown')
                else:
                    await context.bot.send_message(chat_id=admin_id, text=mensaje, parse_mode='Markdown')
                    
        except Exception as e:
            logging.error(f"Error notificando administradores: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
📋 *GUÍA RÁPIDA DEL BOT*

*COMANDOS:*
/start - Menú principal
/calcular - Analizar riesgo
/reporte - Ver último análisis
/info - Información importante
/comentario - Reportar con fotos
/help - Esta ayuda

*📍 Col. José López Portillo, Iztapalapa*
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def calcular_riesgo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el cálculo de riesgo"""
        instruction_text = """
🔍 *CALCULADOR DE RIESGO*

Envía 4 valores (uno por línea):
1. Fugas de agua (0-1000)
2. Humedad suelo (0-100%)
3. Nivel freático (0-100m)
4. Mantenimiento (0-100)

*Ejemplo:*
180
45
50
13
        """
        await update.message.reply_text(instruction_text, parse_mode='Markdown')
        return RIESGO_INPUT

    async def procesar_datos_riesgo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa los datos de riesgo"""
        try:
            datos = update.message.text.strip().split('\n')
            if len(datos) != 4:
                await update.message.reply_text("❌ Error: Debes enviar exactamente 4 valores")
                return RIESGO_INPUT
            
            fugas_agua = float(datos[0])
            humedad_suelo = float(datos[1])
            nivel_freatico = float(datos[2])
            mantenimiento = float(datos[3])
            
            # Validaciones
            if not all(0 <= x <= 1000 for x in [fugas_agua, humedad_suelo, nivel_freatico, mantenimiento]):
                await update.message.reply_text("❌ Error: Valores fuera de rango")
                return RIESGO_INPUT
            
            riesgo = self.calcular_riesgo_estadistico(fugas_agua, humedad_suelo, nivel_freatico, mantenimiento)
            
            self.guardar_reporte(update.effective_user.id, fugas_agua, humedad_suelo, nivel_freatico, mantenimiento, riesgo)
            await self.enviar_resultado(update, riesgo, {
                'fugas_agua': fugas_agua,
                'humedad_suelo': humedad_suelo,
                'nivel_freatico': nivel_freatico,
                'mantenimiento': mantenimiento
            })
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ Error: Todos los valores deben ser números")
            return RIESGO_INPUT

    def calcular_riesgo_estadistico(self, fugas_agua, humedad_suelo, nivel_freatico, mantenimiento):
        """Calcula el riesgo estadístico"""
        medias = {'fugas_agua': 178.67, 'humedad_suelo': 45.0, 'nivel_freatico': 50.03, 'mantenimiento_hidraulico': 12.67}
        desviaciones = {'fugas_agua': 59.53, 'humedad_suelo': 5.57, 'nivel_freatico': 2.62, 'mantenimiento_hidraulico': 6.66}
        
        factor_fugas = self.calcular_factor_normalizado(fugas_agua, medias['fugas_agua'], desviaciones['fugas_agua']) * 0.35
        factor_humedad = self.calcular_factor_normalizado(humedad_suelo, medias['humedad_suelo'], desviaciones['humedad_suelo']) * 0.30
        factor_nivel_freatico = (1 - self.calcular_factor_normalizado(nivel_freatico, medias['nivel_freatico'], desviaciones['nivel_freatico'])) * 0.25
        factor_mantenimiento = (1 - self.calcular_factor_normalizado(mantenimiento, medias['mantenimiento_hidraulico'], desviaciones['mantenimiento_hidraulico'])) * 0.10
        
        riesgo_total = factor_fugas + factor_humedad + factor_nivel_freatico + factor_mantenimiento
        return min(max(riesgo_total, 0.0), 1.0)

    def calcular_factor_normalizado(self, valor, media, desviacion):
        """Normaliza el valor"""
        if desviacion == 0:
            return 0.5
        z_score = (valor - media) / desviacion
        return 1 / (1 + math.exp(-z_score * 0.5))

    def guardar_reporte(self, user_id, fugas_agua, humedad_suelo, nivel_freatico, mantenimiento, riesgo):
        """Guarda el reporte"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reportes (user_id, fugas_agua, humedad_suelo, nivel_freatico, mantenimiento, riesgo_calculado)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, fugas_agua, humedad_suelo, nivel_freatico, mantenimiento, riesgo))
        self.conn.commit()

    async def enviar_resultado(self, update: Update, riesgo: float, datos: dict):
        """Envía el resultado"""
        if riesgo > 0.7:
            nivel = "🚨 ALERTA ROJA"
            telefono = "📞 *CONTACTO: 911*"
        elif riesgo > 0.4:
            nivel = "🟡 ALERTA AMARILLA"
            telefono = "📞 *Reporte: 5658-1111*"
        else:
            nivel = "🟢 SITUACIÓN ESTABLE"
            telefono = "📞 *Mantenimiento: 5654-3210*"
        
        resultado_text = f"""
{nivel.split()[1]} *RESULTADO DEL ANÁLISIS* {nivel.split()[1]}

*Riesgo:* {riesgo:.3f}/1.000
*Alerta:* {nivel}

*Datos:*
• Fugas: {datos['fugas_agua']} reportes/año
• Humedad: {datos['humedad_suelo']}%
• Nivel freático: {datos['nivel_freatico']} m
• Mantenimiento: {datos['mantenimiento']} acciones

{telefono}

*📍 Col. José López Portillo, Iztapalapa*
        """
        await update.message.reply_text(resultado_text, parse_mode='Markdown')

    async def ver_reporte(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el último reporte"""
        user_id = update.effective_user.id
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM reportes WHERE user_id = ? ORDER BY fecha DESC LIMIT 1', (user_id,))
        reporte = cursor.fetchone()
        
        if reporte:
            riesgo = reporte[6]
            nivel = "🚨 ALERTA ROJA" if riesgo > 0.7 else "🟡 ALERTA AMARILLA" if riesgo > 0.4 else "🟢 ESTABLE"
            reporte_text = f"📋 *ÚLTIMO REPORTE*\n\nRiesgo: {riesgo:.3f}\nNivel: {nivel}\n\nUsa /calcular para nuevo análisis"
        else:
            reporte_text = "📭 No tienes reportes. Usa /calcular"
        
        await update.message.reply_text(reporte_text, parse_mode='Markdown')

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela la conversación"""
        await update.message.reply_text("Operación cancelada.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    def run(self):
        """Inicia el bot - VERSIÓN CORREGIDA"""
        # Configurar logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        # Crear aplicación con la nueva API
        application = Application.builder().token(TOKEN).build()
        
        # Configurar handlers de conversación
        conv_riesgo = ConversationHandler(
            entry_points=[CommandHandler('calcular', self.calcular_riesgo)],
            states={
                RIESGO_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.procesar_datos_riesgo)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        conv_comentarios = ConversationHandler(
            entry_points=[CommandHandler('comentario', self.comentario_command)],
            states={
                COMENTARIO_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.procesar_opcion_comentario)],
                FOTO_INPUT: [MessageHandler(filters.PHOTO | filters.TEXT, self.procesar_foto)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Agregar handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("reporte", self.ver_reporte))
        application.add_handler(CommandHandler("info", self.info_command))
        application.add_handler(conv_riesgo)
        application.add_handler(conv_comentarios)
        
        # Iniciar el bot - MÉTODO CORREGIDO
        print("🤖 Bot iniciado en Render.com - Siempre activo!")
        application.run_polling()

# Ejecutar el bot
if __name__ == "__main__":
    bot = BotSocavones()
    bot.run()