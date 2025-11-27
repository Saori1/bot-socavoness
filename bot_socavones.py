import os
import logging
import sqlite3
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración
TOKEN = os.getenv('TOKEN')
PORT = int(os.environ.get('PORT', 5000))

# Crear aplicación Flask (necesaria para Web Service)
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot de Socavones Iztapalapa - ACTIVO ✅"

class BotSocavones:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Configurar base de datos"""
        self.conn = sqlite3.connect('socavones.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mensaje TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        print("✅ Base de datos lista")

    def start(self, update, context):
        """Comando /start"""
        user = update.effective_user
        update.message.reply_text(
            f"🤖 BOT SOCAVONES IZTAPALAPA\n\n"
            f"Hola {user.first_name}!\n\n"
            f"📍 Col. José López Portillo\n\n"
            f"📋 COMANDOS:\n"
            f"/start - Menú\n"
            f"/reportar [mensaje] - Reportar problema\n"
            f"/info - Información\n"
            f"/emergencia - Teléfonos"
        )

    def info(self, update, context):
        """Comando /info"""
        update.message.reply_text(
            "🔍 INFORMACIÓN SOBRE SOCAVONES\n\n"
            "🚰 Causas principales:\n"
            "• Fugas de agua subterráneas\n"
            "• Suelo arcilloso inestable\n"
            "• Erosión del subsuelo\n\n"
            "📍 Zona: Col. José López Portillo, Iztapalapa"
        )

    def emergencia(self, update, context):
        """Comando /emergencia"""
        update.message.reply_text(
            "🚨 TELÉFONOS DE EMERGENCIA\n\n"
            "📞 Protección Civil: 911\n"
            "📞 Sistema de Aguas: 5654-3210\n"
            "📞 Locatel: 5658-1111\n\n"
            "⚠️ EN CASO DE SOCAVÓN:\n"
            "1. Aléjese inmediatamente\n"
            "2. Alertar a vecinos\n"
            "3. Llamar a Protección Civil\n"
            "4. No acercarse para tomar fotos"
        )

    def reportar(self, update, context):
        """Comando /reportar"""
        if context.args:
            mensaje = ' '.join(context.args)
            user_id = update.effective_user.id
            
            # Guardar en base de datos
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO reportes (user_id, mensaje) VALUES (?, ?)',
                (user_id, mensaje)
            )
            self.conn.commit()
            
            update.message.reply_text(
                f"✅ REPORTE GUARDADO EXITOSAMENTE\n\n"
                f"📝 Tu reporte: {mensaje}\n\n"
                "Gracias por tu colaboración comunitaria.\n"
                "Si es urgente, contacta: 🚨 911"
            )
            
            logger.info(f"📝 Nuevo reporte de {user_id}: {mensaje}")
        else:
            update.message.reply_text(
                "📝 USO: /reportar [tu mensaje]\n\n"
                "Ejemplos:\n"
                "/reportar Fuga en calle Principal #123\n"
                "/reportar Socavón en avenida Central\n"
                "/reportar Grieta grande en pavimento"
            )

    def mensaje_normal(self, update, context):
        """Manejar mensajes normales"""
        update.message.reply_text(
            "🤖 Escribe /start para ver los comandos disponibles\n\n"
            "O usa:\n"
            "/reportar [mensaje] - Para reportar un problema\n"
            "/info - Información sobre socavones\n"
            "/emergencia - Teléfonos de emergencia"
        )

    def run_bot(self):
        """Iniciar el bot de Telegram"""
        try:
            print("🚀 Iniciando Bot de Socavones...")
            print("📍 Iztapalapa - Col. José López Portillo")
            print("🌐 Modo: Web Service con Flask")
            
            # Crear updater del bot
            updater = Updater(TOKEN, use_context=True)
            dispatcher = updater.dispatcher
            
            # Agregar handlers
            dispatcher.add_handler(CommandHandler("start", self.start))
            dispatcher.add_handler(CommandHandler("info", self.info))
            dispatcher.add_handler(CommandHandler("emergencia", self.emergencia))
            dispatcher.add_handler(CommandHandler("reportar", self.reportar))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.mensaje_normal))
            
            # Iniciar polling del bot
            updater.start_polling()
            print("✅ Bot de Telegram iniciado correctamente!")
            
            return updater
            
        except Exception as e:
            logger.error(f"❌ Error iniciando bot: {e}")
            raise e

def main():
    """Función principal"""
    # Iniciar el bot
    bot = BotSocavones()
    bot_updater = bot.run_bot()
    
    # Iniciar servidor Flask en el puerto correcto
    print(f"🌐 Iniciando servidor web en puerto {PORT}...")
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
