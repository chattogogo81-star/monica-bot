# @title
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import pandas as pd
# =======================================================
# 🤖 WELLBOT CORPORATIVO - Asistente de Bienestar Laboral "M O N I C A"
# (Versión con Ciudad, Líder, Comentario y estructura nueva)
# =======================================================

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import pandas as pd
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
TOKEN = "8660577207:AAGByxl0XHWwR2mWT4QmGscGnoNVpRR2l6M"
ARCHIVO_CSV = "/content/drive/MyDrive/respuestas_bienestar_v2.csv"
ARCHIVO_EXCEL = "/content/drive/MyDrive/respuestas_bienestar_v2.xlsx"

# Estados de conversación
AREA, CIUDAD, LIDER, PREGUNTA, COMENTARIO = range(5)

# ÁREAS EMPRESARIALES GENÉRICAS
AREAS_EMPRESA = [
    "Recursos Humanos 👥",
    "Finanzas / Contabilidad 💰",
    "Operaciones ⚙️",
    "Marketing / Ventas 📢",
    "Tecnología / IT 💻",
    "Administración / Gerencia General 🏢"
]

# --- SALUDO SEGÚN HORA (COLOMBIA UTC-5) ---
def obtener_saludo():
    hora_colombia = datetime.now(timezone.utc) - timedelta(hours=5)
    hora = hora_colombia.hour
    if 1 <= hora < 12:
        return "☀️ Buenos días"
    elif 12 <= hora < 19:
        return "🌇 Buenas tardes"
    else:
        return "🌙 Buenas noches"

# PREGUNTAS DE BIENESTAR
PREGUNTAS = [
    "1️⃣ Del 1 al 5, ¿qué tan motivado te sientes para realizar tus tareas diarias? 💪",
    "2️⃣ Del 1 al 5, ¿sientes que tus habilidades están siendo aprovechadas en tu trabajo? 🎯",
    "3️⃣ Del 1 al 5, ¿te sientes valorado y reconocido por tu esfuerzo? 🌟",
    "4️⃣ Del 1 al 5, ¿cómo calificarías tu equilibrio entre trabajo y descanso? ⚖️",
    "5️⃣ Del 1 al 5, ¿sientes que tu entorno de trabajo te permite concentrarte bien? 🧘",
    "6️⃣ Del 1 al 5, ¿cómo describirías tu bienestar emocional en la empresa? 💬",
    "7️⃣ Del 1 al 5, ¿consideras que hay oportunidades de desarrollo profesional? 📈",
    "8️⃣ Del 1 al 5, ¿qué tan satisfecho estás con tu experiencia general en la empresa? 🏆"
]

# =======================================================
# FUNCIONES PRINCIPALES
# =======================================================

# --- INICIO ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    saludo = obtener_saludo()

    keyboard = [[a] for a in AREAS_EMPRESA] + [[KeyboardButton("🚪 Salir")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    bienvenida = (
        f"{saludo}, *{update.message.from_user.first_name}* 👋\n\n"
        "Soy *Mónica*, tu asistente virtual de bienestar laboral 🌸\n"
        "Estoy aquí para acompañarte en una breve encuesta sobre tu experiencia en la empresa.\n\n"
        "Por favor, selecciona el área en la que trabajas:"
    )

    await update.message.reply_text(bienvenida, parse_mode="Markdown", reply_markup=reply_markup)
    return AREA


# --- SELECCIÓN DE ÁREA ---
async def seleccionar_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    area = update.message.text.strip()
    if area == "🚪 Salir":
        await salir(update, context)
        return ConversationHandler.END

    if area not in AREAS_EMPRESA:
        await update.message.reply_text("⚠️ Por favor selecciona un área válida de la lista.")
        return AREA

    context.user_data["area"] = area
    await update.message.reply_text("🏙️ Ingresa la *ciudad o sede* en la que trabajas:", parse_mode="Markdown")
    return CIUDAD


# --- CIUDAD ---
async def obtener_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ciudad"] = update.message.text.strip()
    await update.message.reply_text("👩‍💼 Ingresa el *nombre de tu líder o jefe directo*:", parse_mode="Markdown")
    return LIDER


# --- LÍDER ---
async def obtener_lider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lider"] = update.message.text.strip()
    context.user_data["respuestas"] = []
    context.user_data["indice"] = 0

    instrucciones = (
        "Perfecto ✅\n\nResponderás 8 preguntas con valores del **1 al 5**, donde:\n"
        "1️⃣ = Muy bajo\n2️⃣ = Bajo\n3️⃣ = Medio\n4️⃣ = Alto\n5️⃣ = Muy alto\n\n"
        "👉 Escribe el número que mejor represente tu percepción.\n"
        "Puedes escribir *salir* en cualquier momento para terminar.\n\n"
        f"{PREGUNTAS[0]}"
    )
    await update.message.reply_text(instrucciones, parse_mode="Markdown")
    return PREGUNTA


# --- RESPUESTAS ---
async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().lower()

    if texto in ["salir", "/salir", "🚪 salir", "cancelar", "/cancelar"]:
        await salir(update, context)
        return ConversationHandler.END

    if not texto.isdigit() or not (1 <= int(texto) <= 5):
        await update.message.reply_text("⚠️ Por favor responde solo con un número del 1 al 5.")
        return PREGUNTA

    context.user_data["respuestas"].append(int(texto))
    context.user_data["indice"] += 1

    if context.user_data["indice"] < len(PREGUNTAS):
        await update.message.reply_text(PREGUNTAS[context.user_data["indice"]])
        return PREGUNTA

    # Última pregunta: comentario
    await update.message.reply_text("💬 Para finalizar, deja un *comentario o percepción general* sobre tu bienestar.\n"
                                    "👉 Si no tienes ninguno, escribe *ninguno*.", parse_mode="Markdown")
    return COMENTARIO


# --- COMENTARIO ---
async def obtener_comentario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comentario = update.message.text.strip()
    if not comentario:
        await update.message.reply_text("⚠️ El comentario no puede estar vacío. Escribe 'ninguno' si no deseas dejar uno.")
        return COMENTARIO

    # Datos base
    user = update.message.from_user
    fecha = datetime.now().strftime("%Y-%m-%d")
    respuestas = context.user_data["respuestas"]
    promedio = round(sum(respuestas) / len(respuestas), 2)

    # Clasificación
    if promedio < 3:
        estado = "🔴 Bienestar bajo"
    elif promedio < 4:
        estado = "🟠 Bienestar medio"
    else:
        estado = "🟢 Bienestar alto"

    # Crear fila de datos
    df = pd.DataFrame([{
        "Área": context.user_data["area"],
        "Ciudad": context.user_data["ciudad"],
        "Líder de área": context.user_data["lider"],
        "Empleado": user.first_name,
        "Fecha": fecha,
        "Participación Encuesta": "Sí",
        **{f"P{i+1}": respuestas[i] for i in range(len(respuestas))},
        "Promedio": promedio,
        "Clasificación": estado,
        "Comentario": comentario
    }])

    # Guardar archivos
    try:
        df_existente = pd.read_csv(ARCHIVO_CSV)
        df_final = pd.concat([df_existente, df], ignore_index=True)
    except FileNotFoundError:
        df_final = df

    df_final.to_csv(ARCHIVO_CSV, index=False)
    df_final.to_excel(ARCHIVO_EXCEL, index=False)

    # Confirmación final
    mensaje = (
        f"🎯 *Encuesta completada exitosamente*\n"
        f"───────────────────────────────\n"
        f"👤 *Empleado:* {user.first_name}\n"
        f"🏢 *Área:* {context.user_data['area']}\n"
        f"🏙️ *Ciudad:* {context.user_data['ciudad']}\n"
        f"👩‍💼 *Líder:* {context.user_data['lider']}\n"
        f"📅 *Fecha:* {fecha}\n"
        f"📊 *Promedio:* {promedio}\n"
        f"💬 *Resultado:* {estado}\n"
        f"───────────────────────────────\n"
        f"Gracias por tu participación 💙 — *Mónica*"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")

    print(f"✅ Guardado: {user.first_name} | {context.user_data['area']} | {promedio}")
    context.user_data.clear()
    return ConversationHandler.END


# --- SALIR ---
async def salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚪 Has salido de la encuesta. ¡Gracias por tu tiempo! 💙 — *Mónica*", parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END


# =======================================================
# EJECUCIÓN DEL BOT
# =======================================================
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.Regex("(?i)^(hola|holaa|buenas|buenos días|buenas tardes|buenas noches)$"), start)
    ],
    states={
        AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_area)],
        CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_ciudad)],
        LIDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_lider)],
        PREGUNTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preguntar)],
        COMENTARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_comentario)]
    },
    fallbacks=[CommandHandler("salir", salir)],
)

app.add_handler(conv_handler)

import asyncio
await app.initialize()
await app.start()
print("🤖 Mónica ejecutándose... puedes saludarla o usar /start para comenzar.")
await app.updater.start_polling()