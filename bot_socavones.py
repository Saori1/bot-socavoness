import logging
import os
import sqlite3

# Configuración
TOKEN = os.getenv('TOKEN')

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Función principal ultra simple"""
    print("🤖 Iniciando Bot de Socavones...")
    
    try:
        # Configurar base de datos simple
        conn = sqlite3.connect('socavones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mensaje TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Base de datos configurada")
        
        # Importar telegram después de configurar todo
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
        
        # Crear updater
        updater = Updater(TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        def start(update, context):
            """Comando /start"""
            user = update.effective_user
            update.message.reply_text(
                f"🤖 BOT SOCAVONES IZTAPALAPA\n\n"
                f"Hola {user.first_name}! Reporta socavones y fugas.\n\n"
                f"📍 Col. José López Portillo\n\n"
                f"📋 COMANDOS:\n"
                f"/start - Menú\n"
                f"/reportar [mensaje] - Reportar problema\n"
                f"/info - Información\n"
                f"/emergencia - Teléfonos"
            )
        
        def info(update, context):
            """Comando /info"""
            update.message.reply_text(
                "🔍 INFORMACIÓN SOCAVONES\n\n"
                "🚰 Causas principales:\n"
                "• Fugas de agua\n"
                "• Suelo arcilloso\n"
                "• Erosión\n\n"
                "📍 Zona: Col. José López Portillo"
            )
        
        def emergencia(update, context):
            """Comando /emergencia"""
            update.message.reply_text(
                "🚨 EMERGENCIA\n\n"
                "📞 Protección Civil: 911\n"
                "📞 Sistema de Aguas: 5654-3210\n"
                "📞 Locatel: 5658-1111\n\n"
                "⚠️ En caso de socavón:\n"
                "1. Aléjese\n"
                "2. Alertar vecinos\n"
                "3. Llamar al 911"
            )
        
        def reportar(update, context):
            """Comando /reportar"""
            if context.args:
                mensaje = ' '.join(context.args)
                user_id = update.effective_user.id
                
                # Guardar en base de datos
                cursor.execute(
                    'INSERT INTO reportes (user_id, mensaje) VALUES (?, ?)',
                    (user_id, mensaje)
                )
                conn.commit()
                
                update.message.reply_text(
                    "✅ REPORTE GUARDADO\n\n"
                    f"Tu reporte: {mensaje}\n\n"
                    "Gracias por tu colaboración."
                )
                
                print(f"📝 Nuevo reporte: {mensaje}")
            else:
                update.message.reply_text(
                    "📝 USO: /reportar [tu mensaje]\n\n"
                    "Ejemplo:\n"
                    "/reportar Fuga en calle Principal #123"
                )
        
        def mensaje_normal(update, context):
            """Manejar mensajes normales"""
            update.message.reply_text(
                "Escribe /start para ver los comandos disponibles\n"
                "O usa /reportar [mensaje] para hacer un reporte"
            )
        
        # Agregar handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("info", info))
        dispatcher.add_handler(CommandHandler("emergencia", emergencia))
        dispatcher.add_handler(CommandHandler("reportar", reportar))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, mensaje_normal))
        
        # Iniciar bot
        print("🚀 Bot iniciado correctamente!")
        print("📍 Iztapalapa - Col. José López Portillo")
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Intentar reiniciar después de 10 segundos
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
