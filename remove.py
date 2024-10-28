import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rembg import remove
from PIL import Image
import io

# Configuración básica del bot
API_TOKEN = '7745194232:AAEoWoMh4aypLDN-qMwX1wKtrls10AkN0Go'

# Configura el logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Función para iniciar el bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame una imagen (JPG, PNG, etc.) y eliminaré el fondo por ti.")

# Función para procesar la imagen recibida
async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Enviar mensaje de progreso inicial
    progress_message = await update.message.reply_text("⏳ Procesando la imagen, por favor espera...")

    try:
        # Verificar si la imagen se envió como foto o documento
        if update.message.photo:
            # Imagen enviada como foto (obtiene la de mayor resolución)
            await progress_message.edit_text("⏳ Paso 1/3: Descargando la imagen...")
            photo_file = await update.message.photo[-1].get_file()
        elif update.message.document and update.message.document.mime_type.startswith("image/"):
            # Imagen enviada como documento con tipo MIME de imagen
            await progress_message.edit_text("⏳ Paso 1/3: Descargando el archivo de imagen...")
            photo_file = await update.message.document.get_file()
        else:
            await progress_message.edit_text("❌ El archivo no es una imagen compatible.")
            return

        # Descargar la imagen y procesarla
        input_image = await photo_file.download_as_bytearray()
        
        # Paso 2: Eliminar el fondo de la imagen
        await progress_message.edit_text("⏳ Paso 2/3: Eliminando el fondo de la imagen...")
        output_data = remove(bytes(input_image), force_return_bytes=True)
        img_no_bg = Image.open(io.BytesIO(output_data))

        # Crear una versión JPG con fondo blanco
        img_with_white_bg = Image.new("RGB", img_no_bg.size, (255, 255, 255))
        img_with_white_bg.paste(img_no_bg, mask=img_no_bg.split()[3])  # Usar el canal alfa como máscara

        # Paso 3: Enviar imagen JPG con fondo blanco
        await progress_message.edit_text("⏳ Paso 3/3: Preparando la imagen para enviar...")

        # Enviar la imagen con fondo blanco como foto
        jpg_buffer = io.BytesIO()
        img_with_white_bg.save(jpg_buffer, format="JPEG")
        jpg_buffer.seek(0)
        await update.message.reply_photo(photo=jpg_buffer, filename="output_with_white_bg.jpg")

        # Enviar la imagen sin fondo como archivo PNG
        png_buffer = io.BytesIO()
        img_no_bg.save(png_buffer, format="PNG")
        png_buffer.seek(0)
        await update.message.reply_text("⬇️ Descargar PNG sin fondo:")
        await update.message.chat.send_document(document=png_buffer, filename="output_no_bg.png")

        # Borrar el mensaje de progreso
        await progress_message.delete()
        logger.info("Imagen procesada y enviada en ambos formatos (JPG con fondo blanco y PNG sin fondo).")

    except Exception as e:
        await progress_message.edit_text("❌ Ocurrió un error al procesar la imagen.")
        logger.error(f"Error al procesar la imagen: {e}")

# Configura los manejadores de comandos e imágenes
def main():
    app = Application.builder().token(API_TOKEN).build()

    # Manejadores de comandos y mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_image))

    # Inicia el bot
    logger.info("Bot en funcionamiento...")
    app.run_polling()

if __name__ == "__main__":
    main()
