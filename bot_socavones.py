import os
import logging
import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Token desde variables de entorno
TOKEN = os.getenv('TOKEN')

class BotSocavones:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Configurar base de datos simple"""
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
            f"/reportar [mensaje] - Reportar\n"
            f"/info - Información\n"
            f"/emergencia - Teléfonos"
        )

    def info(self, update, context):
        """Comando /info"""
        update.message.reply_text(
            "🔍 INFORMACIÓN\n\n"
            "🚰 Causas de socavones:\n"
            "• Fugas de agua\n"
            "• Suelo arcilloso\n"
            "• Erosión\n\n"
            "📍 Col. José López Portillo"
        )

    def emergencia(self, update, context):
        """Comando /emergencia"""
        update.message.reply_text(
            "🚨 TELÉFONOS EMERGENCIA\n\n"
            "📞 Protección Civil: 911\n"
            "📞 Sistema de Aguas: 5654-3210\n"
            "📞 Locatel: 5658-1111\n\n"
            "⚠️ En emergencia:\n"
            "1. Aléjese\n"
            "2. Alertar vecinos\n"
            "3. Llamar al 911"
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
                f"✅ REPORTE GUARDADO\n\n"
                f"📝: {mensaje}\n\n"
                "Gracias por tu colaboración."
            )
            
            logger.info(f"Nuevo reporte de {user_id}: {mensaje}")
        else:
            update.message.reply_text(
                "📝 USO: /reportar [mensaje]\n\n"
                "Ejemplo:\n"
                "/reportar Fuga en calle Principal #123"
            )

    def mensaje_normal(self, update, context):
        """Mensajes normales"""
        update.message.reply_text(
            "Usa /start para ver comandos\n"
            "O /reportar [mensaje] para reportar"
        )

    def run(self):
        """Iniciar bot"""
        try:
            print("🚀 Iniciando Bot de Socavones...")
            print("📍 Iztapalapa - Col. José López Portillo")
            print("🤖 Modo: Background Worker")
            
            # Crear updater
            updater = Updater(TOKEN, use_context=True)
            dispatcher = updater.dispatcher
            
            # Agregar handlers
            dispatcher.add_handler(CommandHandler("start", self.start))
            dispatcher.add_handler(CommandHandler("info", self.info))
            dispatcher.add_handler(CommandHandler("emergencia", self.emergencia))
            dispatcher.add_handler(CommandHandler("reportar", self.reportar))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.mensaje_normal))
            
            # Iniciar polling
            updater.start_polling()
            print("✅ Bot iniciado correctamente!")
            
            # Mantener el bot corriendo
            updater.idle()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")
            # Reintentar después de 30 segundos
            import time
            time.sleep(30)
            self.run()

if __name__ == "__main__":
    bot = BotSocavones()
    bot.run()
