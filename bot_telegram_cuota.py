"""
🏠 Bot Calculadora de Cuota Hipotecaria CLOU v.Final
Plataforma: Telegram
Versión personalizada para Jancarlo Inmobiliario
Desarrollador: Jan
"""

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes
)
import logging
import os
import math

# ==========================================
# CONFIGURACIÓN
# ==========================================
TOKEN_TELEGRAM = os.getenv('TOKEN_TELEGRAM', 'TU_TOKEN_AQUI')

# Estados de la conversación (4 preguntas)
PRECIO, INICIAL, TCEA, PLAZO = range(4)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# FUNCIONES DE CÁLCULO
# ==========================================

def calcular_cuota(precio, inicial, tcea, plazo_anos):
    """
    Calcula la cuota hipotecaria usando la fórmula:
    Cuota = Préstamo × [i(1+i)^n] / [(1+i)^n - 1]
    
    Donde:
    - i = TCEA mensual (TCEA anual / 12 / 100)
    - n = número de meses (plazo_anos × 12)
    """
    
    prestamo = precio - inicial
    
    # Validar que el préstamo sea positivo
    if prestamo <= 0:
        return None
    
    # Conversión de TCEA anual a mensual
    tcea_mensual = (tcea / 12) / 100
    
    # Número de meses
    n_meses = plazo_anos * 12
    
    # Fórmula de cuota
    factor = (tcea_mensual * (1 + tcea_mensual) ** n_meses) / ((1 + tcea_mensual) ** n_meses - 1)
    cuota_mensual = prestamo * factor
    
    # Cálculos adicionales
    total_pagado = cuota_mensual * n_meses
    intereses_comisiones = total_pagado - prestamo
    
    return {
        "prestamo": int(round(prestamo)),
        "cuota_mensual": int(round(cuota_mensual)),
        "total_pagado": int(round(total_pagado)),
        "intereses_comisiones": int(round(intereses_comisiones))
    }

def calcular_comparativa(precio, inicial, tcea):
    """Calcula cuota para 10, 15, 20 y 25 años"""
    plazos = [10, 15, 20, 25]
    resultados = {}
    
    for plazo in plazos:
        resultado = calcular_cuota(precio, inicial, tcea, plazo)
        if resultado:
            resultados[plazo] = resultado
    
    return resultados

def formato_moneda(numero):
    """Convierte número a formato S/. X,XXX con comas como separadores de miles."""
    return f"S/. {numero:,}"

# ==========================================
# MANEJADORES DE CONVERSACIÓN
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la conversación con 3 mensajes iniciales."""
    
    # MENSAJE 1: Bienvenida
    await update.message.reply_text(
        "👋 ¡Hola! Soy el asistente virtual de Jancarlo Inmobiliario.",
        parse_mode='Markdown'
    )
    
    # MENSAJE 2: Imagen sin texto
    url_imagen = "https://postimg.cc/ZBWGPTR8"
    try:
        await update.message.reply_photo(photo=url_imagen)
    except:
        pass
    
    # MENSAJE 3: Propósito
    await update.message.reply_text(
        "Mi meta es ayudarte a calcular la cuota hipotecaria de tu depa de forma precisa. "
        "Con *4 preguntas simples*, sabrás exactamente cuánto pagarías mensualmente en diferentes escenarios.\n\n"
        "Esto te permitirá tomar decisiones financieras informadas y elegir el plazo que mejor se ajuste a tu presupuesto.\n\n"
        "*¿Empezamos?*",
        parse_mode='Markdown'
    )
    
    # MENSAJE 4: Primera pregunta
    await update.message.reply_text(
        "📊 *Pregunta 1:* ¿Cuál es el *precio del depa* que deseas comprar?\n"
        "(En Soles)",
        parse_mode='Markdown'
    )
    
    return PRECIO

async def obtener_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura el precio del depa."""
    try:
        precio = float(update.message.text.replace(",", "."))
        if precio <= 0:
            await update.message.reply_text("❌ Por favor ingresa un monto positivo.")
            return PRECIO
        
        context.user_data['precio'] = precio
        
        # MENSAJE 5
        await update.message.reply_text(
            f"✅ Precio del depa: {formato_moneda(int(precio))}",
            parse_mode='Markdown'
        )
        
        # MENSAJE 6
        porcentaje_minimo = int(precio * 0.20)
        await update.message.reply_text(
            f"💰 *Pregunta 2:* ¿Cuál es tu *inicial* (aporte propio)?\n"
            f"(Mínimo 20% de {formato_moneda(int(precio))} = {formato_moneda(porcentaje_minimo)})",
            parse_mode='Markdown'
        )
        return INICIAL
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return PRECIO

async def obtener_inicial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura la inicial."""
    try:
        inicial = float(update.message.text.replace(",", "."))
        precio = context.user_data['precio']
        minimo = precio * 0.20
        
        if inicial <= 0:
            await update.message.reply_text("❌ Por favor ingresa un monto positivo.")
            return INICIAL
        
        if inicial < minimo:
            await update.message.reply_text(
                f"❌ La inicial debe ser mínimo 20% = {formato_moneda(int(minimo))}"
            )
            return INICIAL
        
        if inicial > precio:
            await update.message.reply_text(
                f"❌ La inicial no puede ser mayor al precio del depa."
            )
            return INICIAL
        
        context.user_data['inicial'] = inicial
        
        # MENSAJE 7
        await update.message.reply_text(
            f"✅ Inicial: {formato_moneda(int(inicial))}",
            parse_mode='Markdown'
        )
        
        # MENSAJE 8
        await update.message.reply_text(
            "📈 *Pregunta 3:* ¿Cuál es la *TCEA (Tasa de Costo Efectivo Anual)* que te ofrece el banco?\n"
            "(En porcentaje. Ej: 9.5, 8.2, 7.8. Incluye comisiones y seguros)",
            parse_mode='Markdown'
        )
        return TCEA
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return INICIAL

async def obtener_tcea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura la TCEA."""
    try:
        tcea = float(update.message.text.replace(",", "."))
        
        if tcea <= 0 or tcea > 50:
            await update.message.reply_text("❌ Por favor ingresa una TCEA válida (entre 0 y 50%).")
            return TCEA
        
        context.user_data['tcea'] = tcea
        
        # MENSAJE 9
        await update.message.reply_text(
            f"✅ TCEA: {tcea}%",
            parse_mode='Markdown'
        )
        
        # MENSAJE 10
        await update.message.reply_text(
            "⏱️ *Pregunta 4 (última):* ¿En cuántos años deseas pagar el depa?\n"
            "(Opciones: 10, 15, 20 o 25 años)",
            parse_mode='Markdown'
        )
        return PLAZO
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return TCEA

async def obtener_plazo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura el plazo y calcula los resultados."""
    try:
        plazo = int(update.message.text.strip())
        plazos_validos = [10, 15, 20, 25]
        
        if plazo not in plazos_validos:
            await update.message.reply_text(
                "❌ Por favor ingresa un plazo válido: 10, 15, 20 o 25 años."
            )
            return PLAZO
        
        context.user_data['plazo'] = plazo
        
        # Obtener datos
        precio = context.user_data['precio']
        inicial = context.user_data['inicial']
        tcea = context.user_data['tcea']
        
        # Calcular cuota principal
        resultado = calcular_cuota(precio, inicial, tcea, plazo)
        
        if not resultado:
            await update.message.reply_text("❌ Error en el cálculo. Por favor intenta de nuevo.")
            return PLAZO
        
        # Calcular comparativa
        comparativa = calcular_comparativa(precio, inicial, tcea)
        
        # MENSAJE 11: Resultado - PARTE 1 (Datos principales)
        respuesta_parte1 = (
            f"📌 *RESULTADO DE TU CUOTA HIPOTECARIA*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Precio del depa: *{formato_moneda(int(precio))}*\n"
            f"• Inicial: *{formato_moneda(int(inicial))}*\n"
            f"• Préstamo: *{formato_moneda(resultado['prestamo'])}*\n"
            f"• TCEA: *{tcea}%*\n"
            f"• Plazo: *{plazo} años*\n"
            f"• Cuota Mensual: *{formato_moneda(resultado['cuota_mensual'])}*"
        )
        
        await update.message.reply_text(respuesta_parte1, parse_mode='Markdown')
        
        # MENSAJE 12: Resultado - PARTE 2 (Análisis completo)
        linea_opcion = f"{plazo} años: {formato_moneda(resultado['cuota_mensual'])}/mes (Total: {formato_moneda(resultado['total_pagado'])}) ← Tu opción"
        
        respuesta_parte2 = (
            f"💡 *ANÁLISIS FINANCIERO:*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total pagado en {plazo} años: *{formato_moneda(resultado['total_pagado'])}*\n"
            f"Intereses + Comisiones: *{formato_moneda(resultado['intereses_comisiones'])}*\n"
            f"Cuota mensual: *{formato_moneda(resultado['cuota_mensual'])}*\n\n"
            f"Comparativa con otros plazos:\n"
        )
        
        for p in [10, 15, 20, 25]:
            if p in comparativa:
                res = comparativa[p]
                if p == plazo:
                    respuesta_parte2 += f"*{p} años: {formato_moneda(res['cuota_mensual'])}/mes (Total: {formato_moneda(res['total_pagado'])}) ← Tu opción*\n"
                else:
                    respuesta_parte2 += f"{p} años: {formato_moneda(res['cuota_mensual'])}/mes (Total: {formato_moneda(res['total_pagado'])})\n"
        
        await update.message.reply_text(respuesta_parte2, parse_mode='Markdown')
        
        # MENSAJE 13: Consideraciones importantes
        await update.message.reply_text(
            "⚠️ *CONSIDERACIONES IMPORTANTES:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 A mayor plazo, menor cuota mensual pero más intereses pagados.\n\n"
            "💡 A menor plazo, mayor cuota mensual pero menos intereses totales.\n\n"
            "💡 La TCEA incluye comisiones, seguros e impuestos (más realista que TEA).\n\n"
            "💡 Este cálculo no incluye gastos notariales, registrales ni prediales.",
            parse_mode='Markdown'
        )
        
        # MENSAJE 14: Información referencial
        await update.message.reply_text(
            "ℹ️ Este cálculo es *referencial*. Si deseas una cotización exacta con tasas actuales del mercado, "
            "entonces necesitas una *asesoría personalizada*. 📞 Puedes agendarla al Whatsapp 📲 920605559 o al siguiente link:",
            parse_mode='Markdown'
        )
        
        # MENSAJE 15: Link de WhatsApp
        await update.message.reply_text(
            "https://wa.link/v7sk8h"
        )
        
        # MENSAJE 16: Opción de nuevo cálculo
        await update.message.reply_text(
            "¿Deseas hacer otro cálculo? Escribe /start"
        )
        
        # Limpiar datos del usuario
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return PLAZO

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación."""
    await update.message.reply_text(
        "❌ Operación cancelada.\n\nEscribe /start para comenzar de nuevo.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda."""
    await update.message.reply_text(
        "🆘 *AYUDA - Bot Calculadora de Cuota*\n\n"
        "*Comandos disponibles:*\n"
        "/start - Iniciar nuevo cálculo\n"
        "/ayuda - Ver esta ayuda\n"
        "/info - Información sobre el bot",
        parse_mode='Markdown'
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información del bot."""
    await update.message.reply_text(
        "ℹ️ *INFORMACIÓN DEL BOT*\n\n"
        "*Bot:* Calculadora de Cuota Hipotecaria v.Final\n"
        "*Desarrollador:* Jancarlo Inmobiliario\n"
        "*Plataforma:* Telegram\n\n"
        "*Parámetros:*\n"
        "• Inicial mínimo: 20% del precio\n"
        "• TCEA: Incluye comisiones y seguros\n"
        "• Plazos: 10, 15, 20, 25 años\n"
        "• Cálculo: Fórmula de cuota hipotecaria francesa",
        parse_mode='Markdown'
    )

# ==========================================
# MAIN - Inicializar Bot
# ==========================================

def main():
    """Inicia el bot."""
    
    if TOKEN_TELEGRAM == 'TU_TOKEN_AQUI':
        logger.error("❌ ERROR: Debes configurar tu TOKEN_TELEGRAM")
        return
    
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    
    # Manejador de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_precio)],
            INICIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_inicial)],
            TCEA: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_tcea)],
            PLAZO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_plazo)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('ayuda', ayuda))
    application.add_handler(CommandHandler('info', info))
    
    logger.info("🚀 Bot Calculadora de Cuota iniciado correctamente")
    application.run_polling()

if __name__ == '__main__':
    main()
