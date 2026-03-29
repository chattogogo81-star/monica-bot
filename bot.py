from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import pandas as pd
from datetime import datetime, timedelta, timezone

# =======================================================
# 🤖 WELLBOT CORPORATIVO - MÓNICA
# =======================================================

TOKEN = "TU_TOKEN_AQUI"

ARCHIVO_CSV = "respuestas_bienestar_v2.csv"
ARCHIVO_EXCEL = "respuestas_bienestar_v2.xlsx"

AREA, CIUDAD, LIDER, PREGUNTA, COMENTARIO = range(5)

AREAS_EMPRESA = [
    "Recursos Humanos 👥",
    "Finanzas / Contabilidad 💰",
    "Operaciones ⚙️",
    "Marketing / Ventas 📢",
    "Tecnología / IT 💻",
    "Administración / Gerencia General 🏢"
]

# -------------------------------------------------------
# SALUDO SEGÚN HORA
# -------------------------------------------------------

def obtener_saludo():
    hora_colombia = datetime.now(timezone.utc) - timedelta(hours=5)
    hora = hora_colombia.hour

    if 1 <= hora < 12:
        return "☀️ Buenos días"
    elif 12 <= hora < 19:
        return "🌇 Buenas tardes"
    else:
        return "🌙 Buenas noches"


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

# -------------------------------------------------------
# START
# -------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()
    saludo = obtener_saludo()

    keyboard = [[a] for a in AREAS_EMPRESA] + [[KeyboardButton("🚪 Salir")]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )

    bienvenida = (
        f"{saludo}, *{update.message.from_user.first_name}* 👋\n\n"
        "Soy *Mónica*, tu asistente virtual de bienestar laboral 🌸\n\n"
        "Selecciona el área en la que trabajas:"
    )

    await update.message.reply_text(
        bienvenida,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return AREA


# -------------------------------------------------------
# AREA
# -------------------------------------------------------

async def seleccionar_area(update: Update, context: ContextTypes.DEFAULT_TYPE):

    area = update.message.text.strip()

    if area == "🚪 Salir":
        return await salir(update, context)

    if area not in AREAS_EMPRESA:
        await update.message.reply_text("⚠️ Selecciona un área válida.")
        return AREA

    context.user_data["area"] = area

    await update.message.reply_text(
        "🏙️ Escribe la *ciudad o sede* donde trabajas:",
        parse_mode="Markdown"
    )

    return CIUDAD


# -------------------------------------------------------
# CIUDAD
# -------------------------------------------------------

async def obtener_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["ciudad"] = update.message.text.strip()

    await update.message.reply_text(
        "👩‍💼 Escribe el *nombre de tu líder o jefe directo*:",
        parse_mode="Markdown"
    )

    return LIDER


# -------------------------------------------------------
# LIDER
# -------------------------------------------------------

async def obtener_lider(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["lider"] = update.message.text.strip()
    context.user_data["respuestas"] = []
    context.user_data["indice"] = 0

    await update.message.reply_text(
        "Responde las siguientes preguntas con números del *1 al 5*.\n\n"
        f"{PREGUNTAS[0]}",
        parse_mode="Markdown"
    )

    return PREGUNTA


# -------------------------------------------------------
# PREGUNTAS
# -------------------------------------------------------

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.strip()

    if not texto.isdigit() or not (1 <= int(texto) <= 5):

        await update.message.reply_text(
            "⚠️ Responde con un número del 1 al 5."
        )

        return PREGUNTA

    context.user_data["respuestas"].append(int(texto))
    context.user_data["indice"] += 1

    if context.user_data["indice"] < len(PREGUNTAS):

        await update.message.reply_text(
            PREGUNTAS[context.user_data["indice"]]
        )

        return PREGUNTA

    await update.message.reply_text(
        "💬 Escribe un comentario final o escribe *ninguno*:",
        parse_mode="Markdown"
    )

    return COMENTARIO


# -------------------------------------------------------
# COMENTARIO FINAL
# -------------------------------------------------------

async def obtener_comentario(update: Update, context: ContextTypes.DEFAULT_TYPE):

    comentario = update.message.text.strip()

    user = update.message.from_user

    respuestas = context.user_data["respuestas"]

    promedio = round(sum(respuestas) / len(respuestas), 2)

    fecha = datetime.now().strftime("%Y-%m-%d")

    if promedio < 3:
        estado = "🔴 Bienestar bajo"
    elif promedio < 4:
        estado = "🟠 Bienestar medio"
    else:
        estado = "🟢 Bienestar alto"

    df = pd.DataFrame([{
        "Area": context.user_data["area"],
        "Ciudad": context.user_data["ciudad"],
        "Lider": context.user_data["lider"],
        "Empleado": user.first_name,
        "Fecha": fecha,
        **{f"P{i+1}": respuestas[i] for i in range(len(respuestas))},
        "Promedio": promedio,
        "Estado": estado,
        "Comentario": comentario
    }])

    try:
        df_existente = pd.read_csv(ARCHIVO_CSV)
        df_final = pd.concat([df_existente, df], ignore_index=True)
    except:
        df_final = df

    df_final.to_csv(ARCHIVO_CSV, index=False)
    df_final.to_excel(ARCHIVO_EXCEL, index=False)

    await update.message.reply_text(
        f"✅ Encuesta completada\n\n"
        f"Promedio: *{promedio}*\n"
        f"Resultado: *{estado}*\n\n"
        f"Gracias por participar 💙",
        parse_mode="Markdown"
    )

    context.user_data.clear()

    return ConversationHandler.END


# -------------------------------------------------------
# SALIR
# -------------------------------------------------------

async def salir(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🚪 Has salido de la encuesta. ¡Gracias!"
    )

    context.user_data.clear()

    return ConversationHandler.END


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={

            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_area)],

            CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_ciudad)],

            LIDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_lider)],

            PREGUNTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preguntar)],

            COMENTARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_comentario)]

        },

        fallbacks=[CommandHandler("salir", salir)]

    )

    app.add_handler(conv_handler)

    print("🤖 Mónica está ejecutándose...")

    app.run_polling()


if __name__ == "__main__":
    main()