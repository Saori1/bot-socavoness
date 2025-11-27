import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
import os

# Configuración
TOKEN = os.getenv('TOKEN')
ADMIN_USER = os.getenv('ADMIN_USER', '123456789')

class BotSocavonesSimple:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Configura la base de datos simple"""
        self.conn = sqlite3.connect('socavones.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ubicacion TEXT,
                problema TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def start(self, update: Update, context: CallbackContext):
        """Comando /start"""
        user = update.effective_user
        welcome_text = f"""
🤖 BOT DE SOCAVONES - IZTAPALAPA

¡Hola {user.first_name}! Reporta socavones y fugas.

📍 Col. José López Portillo, Iztapalapa

📋 COMANDOS:
/start - Menú principal
/reportar - Reportar un problema
/info - Información importante
/emergencia - Teléfonos de emergencia
        """
        
        keyboard = [
            ['/reportar', '/info'],
            ['/emergencia']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(welcome_text, reply_markup=reply_markup)

    def info(self, update: Update, context: CallbackContext):
        """Información sobre socavones"""
        info_text = """
🔍 INFORMACIÓN SOBRE SOCAVONES

🚰 PRINCIPALES CAUSAS:
• Fugras de agua subterráneas
• Suelo arcilloso inestable  
• Erosión del subsuelo
• Falta de mantenimiento

⚠️ SEÑALES DE PELIGRO:
• Hundimientos en el pavimento
• Grietas en paredes y suelo
• Charcos persistentes sin lluvia
• Sonidos huecos al caminar

📍 Zona de monitoreo: Col. José López Portillo
        """
        update.message.reply_text(info_text)

    def emergencia(self, update: Update, context: CallbackContext):
        """Teléfonos de emergencia"""
        emergencia_text = """
🚨 TELÉFONOS DE EMERGENCIA

📞 Protección Civil: 911
📞 Sistema de Aguas: 5654-3210  
📞 Locatel: 5658-1111
📞 Bomberos: 911

⚠️ EN CASO DE SOCAVÓN:
1. Aléjese inmediatamente
2. Alertar a vecinos
3. Llamar a Protección Civil
4. No tomar selfies cerca
        """
        update.message.reply_text(emergencia_text)

    def reportar(self, update: Update, context: CallbackContext):
        """Inicia el reporte"""
        instrucciones = """
📝 REPORTAR PROBLEMA

Por favor envía tu reporte en este formato:

*Ubicación exacta:*
*Problema observado:*

📌 EJEMPLO:
Calle Principal #123, entre Calle A y B
Fuga de agua visible y hundimiento en pavimento

⚠️ Incluye detalles específicos de la ubicación
        """
        update.message.reply_text(instrucciones)
        # Guardar que el usuario está en modo reporte
        context.user_data['esperando_reporte'] = True

    def procesar_mensaje(self, update: Update, context: CallbackContext):
        """Procesa todos los mensajes"""
        try:
            user_id = update.effective_user.id
            mensaje = update.message.text
            
            # Si está esperando un reporte
            if context.user_data.get('esperando_reporte'):
                self.guardar_reporte(user_id, mensaje)
                
                respuesta = """
✅ REPORTE GUARDADO EXITOSAMENTE

Hemos registrado tu observación. 
Si es una emergencia, contacta:
🚨 911 - Protección Civil

Gracias por tu colaboración comunitaria.
                """
                update.message.reply_text(respuesta)
                context.user_data['esperando_reporte'] = False
                
                # Notificar al administrador
                self.notificar_admin(context, user_id, mensaje)
                
            else:
                # Mensaje normal
                update.message.reply_text(
                    "Usa /start para ver los comandos disponibles o /reportar para hacer un reporte."
                )
                
        except Exception as e:
            logging.error(f"Error: {e}")
            update.message.reply_text("❌ Error al procesar tu mensaje. Intenta nuevamente.")

    def guardar_reporte(self, user_id, mensaje):
        """Guarda el reporte en la base de datos"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO reportes (user_id, problema) VALUES (?, ?)',
            (user_id, mensaje)
        )
        self.conn.commit()

    def notificar_admin(self, context, user_id, mensaje):
        """Notifica al administrador"""
        try:
            admin_text = f"""
🚨 NUEVO REPORTE RECIBIDO

👤 Usuario: {user_id}
📝 Reporte: {mensaje}

Revisar urgencia del caso.
            """
            context.bot.send_message(
                chat_id=ADMIN_USER,
                text=admin_text
            )
        except Exception as e:
            logging.error(f"Error notificando admin: {e}")

    def run(self):
        """Inicia el bot"""
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        # Crear updater
        updater = Updater(TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Comandos
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("info", self.info))
        dispatcher.add_handler(CommandHandler("emergencia", self.emergencia))
        dispatcher.add_handler(CommandHandler("reportar", self.reportar))
        
        # Mensajes normales
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.procesar_mensaje))
        
        # Iniciar bot
        print("🤖 Bot Simple de Socavones iniciado!")
        print("📍 Iztapalapa - Col. José López Portillo")
        print("🚀 Funcionando en Render.com")
        
        updater.start_polling()
        updater.idle()

if __name__ == "__main__":
    bot = BotSocavonesSimple()
    bot.run()
