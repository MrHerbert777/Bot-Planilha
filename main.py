import os
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, \
    MessageHandler, filters
from PIL import Image
import pytesseract
#import easyocr
import asyncio
import nest_asyncio
import logging
from datetime import datetime
import locale
from datetime import datetime
import re

ESPERANDO_TIPSTER, ESPERANDO_COMPETICAO = range(2)

# Definir a localidade para português (Brasil)
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Ativar nest_asyncio
nest_asyncio.apply()

# Caminho do executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Inicializa o leitor do EasyOCR (somente uma vez para reutilizar)
#reader = easyocr.Reader(['pt', 'en'], gpu=True)

# Insira seu token aqui
TOKEN = '8182151154:AAHHLoVizyeCCN5ddnoRtrKOQzGvAoSpmA0'
SHEET_ID = '1UsnTGhuFb2L7YdcI0DOSpKVUVmFxjFwlcTGrjCTuLsA'  # Substitua pelo ID da sua planilha
CREDS_FILE = 'credentials.json'  # Caminho para o seu arquivo de credenciais

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Configure o logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s',
    level=logging.INFO
)

# Definição dos estados da conversa
MENU, OPTION1, OPTION2, SELECT_TIPSTER, SELECT_COMPETITION, VALORES = range(6)


# Autenticação com Google Sheets
def authenticate_google_sheets():
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        logging.info("Autenticação com Google Sheets bem-sucedida.")
        return client.open_by_key(SHEET_ID)
    except Exception as e:
        logging.error("Erro ao autenticar com Google Sheets: %s", e)


# Função para adicionar um tipster
def add_tipster(tipster_name):
    try:
        sheet = authenticate_google_sheets()
        try:
            worksheet = sheet.worksheet("Tipsters")
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Tipsters", rows="100", cols="1")
            logging.info("Aba criada: Tipsters")

        all_values = worksheet.get_all_values()
        next_row = len(all_values) + 1
        worksheet.update(f'A{next_row}', [[tipster_name]])
        logging.info(f"Tipster adicionado: {tipster_name}")
        return True
    except Exception as e:
        logging.error("Erro ao adicionar tipster: %s", e)
        return False


# Função para adicionar uma competição
def add_competition(competition_name):
    try:
        sheet = authenticate_google_sheets()
        try:
            worksheet = sheet.worksheet("Competições")
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Competições", rows="100", cols="1")
            logging.info("Aba criada: Competições")

        all_values = worksheet.get_all_values()
        next_row = len(all_values) + 1
        worksheet.update(f'A{next_row}', [[competition_name]])
        logging.info(f"Competição adicionada: {competition_name}")
        return True
    except Exception as e:
        logging.error("Erro ao adicionar competição: %s", e)
        return False


# Função de resposta ao comando /start
async def start(update: Update, context: CallbackContext) -> int:
    # Verifica se é um callback ou uma mensagem
    if update.message:
        chat_id = update.message.chat_id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat_id
    else:
        return MENU  # Se não for mensagem nem callback, sai da função

    keyboard = [
        [InlineKeyboardButton("Cadastrar Tipster", callback_data="cadastrar_tipster")],
        [InlineKeyboardButton("Cadastrar Competição", callback_data="cadastrar_competicao")],
        [InlineKeyboardButton("Planilhar", callback_data="planilhar")],
        [InlineKeyboardButton("Ver Tipsters Cadastrados", callback_data="ver_tipsters")],
        [InlineKeyboardButton("Ver Competições Cadastradas", callback_data="ver_competicoes")],
        [InlineKeyboardButton("Encerrar o Bot", callback_data="encerrar_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Responde de forma diferente dependendo do tipo de update
    if update.message:
        await update.message.reply_text("Olá! Bem-vindo ao bot. Escolha uma opção:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Olá! Bem-vindo ao bot. Escolha uma opção:", reply_markup=reply_markup)

    return MENU  # Retorna o estado do menu principal

# Função para gerenciar o cadastro de tipsters
async def cadastrar_tipster(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Por favor, envie o nome do tipster a ser cadastrado.")
    return OPTION1


# Função para gerenciar o cadastro de competições
async def cadastrar_competicao(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Por favor, envie o nome da competição a ser cadastrada.")
    return OPTION2


# Função para adicionar o tipster após receber o nome
async def receive_tipster_name(update: Update, context: CallbackContext) -> int:
    tipster_name = update.message.text
    if add_tipster(tipster_name):
        await update.message.reply_text("Tipster cadastrado com sucesso! Escolha uma opção:",
                                        reply_markup=return_menu())
    else:
        await update.message.reply_text("Erro ao cadastrar tipster. Tente novamente.")
    return MENU


# Função para adicionar a competição após receber o nome
async def receive_competition_name(update: Update, context: CallbackContext) -> int:
    competition_name = update.message.text
    if add_competition(competition_name):
        await update.message.reply_text("Competição cadastrada com sucesso! Escolha uma opção:",
                                        reply_markup=return_menu())
    else:
        await update.message.reply_text("Erro ao cadastrar competição. Tente novamente.")
    return MENU


# Função para retornar o menu principal
def return_menu():
    keyboard = [
        [InlineKeyboardButton("Encerrar", callback_data="encerrar")],
        [InlineKeyboardButton("Voltar ao Menu Principal", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Função para retornar o menu com opções para troca ou encerramento
def options_menu():
    keyboard = [
        [InlineKeyboardButton("Trocar Tipster", callback_data="trocar_tipster")],
        [InlineKeyboardButton("Trocar Competição", callback_data="trocar_competicao")],
        [InlineKeyboardButton("Voltar ao Menu Principal", callback_data="menu_principal")],
        [InlineKeyboardButton("Encerrar o Bot", callback_data="encerrar")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Função para mostrar os tipsters cadastrados em forma de lista
async def ver_tipsters(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Tipsters")
        tipsters = worksheet.get_all_values()
        tipster_names = [row[0] for row in tipsters]

        if tipster_names:
            response = "Tipsters Cadastrados:\n" + "\n".join(tipster_names)
        else:
            response = "Nenhum tipster cadastrado."

        await update.callback_query.edit_message_text(
            text=response + "\n\nEscolha uma opção:",
            reply_markup=return_menu()
        )
    except Exception as e:
        logging.error("Erro ao listar tipsters: %s", e)
        await update.callback_query.edit_message_text(
            text="Erro ao listar tipsters.\n\nEscolha uma opção:",
            reply_markup=return_menu()
        )
    return MENU


# Função para mostrar as competições cadastradas em forma de lista
async def ver_competicoes(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Competições")
        competicoes = worksheet.get_all_values()
        competicao_names = [row[0] for row in competicoes]

        if competicao_names:
            response = "Competições Cadastradas:\n" + "\n".join(competicao_names)
        else:
            response = "Nenhuma competição cadastrada."

        await update.callback_query.edit_message_text(
            text=response + "\n\nEscolha uma opção:",
            reply_markup=return_menu()
        )
    except Exception as e:
        logging.error("Erro ao listar competições: %s", e)
        await update.callback_query.edit_message_text(
            text="Erro ao listar competições.\n\nEscolha uma opção:",
            reply_markup=return_menu()
        )
    return MENU


# Função para encerrar o bot
async def encerrar_bot(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Bot encerrado. Até a próxima!")
    return ConversationHandler.END


# Função para voltar ao menu principal
async def voltar_menu_principal(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await start(update, context)
    return MENU


# Função para iniciar o processo de planilhar
async def planilhar(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Por favor, selecione o tipster.")

    # Exibir os tipsters como botões
    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Tipsters")
        tipsters = worksheet.get_all_values()
        keyboard = [[InlineKeyboardButton(row[0], callback_data=f"tipster_{row[0]}")] for row in tipsters]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Selecione um tipster:", reply_markup=reply_markup)
    except Exception as e:
        logging.error("Erro ao iniciar o planilhamento: %s", e)
        await update.callback_query.edit_message_text(text="Erro ao iniciar o planilhamento.")
    return SELECT_TIPSTER


# Função para processar a seleção do tipster
async def select_tipster(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    context.user_data['tipster'] = update.callback_query.data.split("_")[1]  # Guardar tipster selecionado
    await update.callback_query.edit_message_text(text="Por favor, selecione a competição.")

    # Exibir as competições como botões
    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Competições")
        competicoes = worksheet.get_all_values()
        keyboard = [[InlineKeyboardButton(row[0], callback_data=f"competicao_{row[0]}")] for row in competicoes]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Selecione uma competição:", reply_markup=reply_markup)
    except Exception as e:
        logging.error("Erro ao selecionar tipster: %s", e)
        await update.callback_query.edit_message_text(text="Erro ao selecionar tipster.")
    return SELECT_COMPETITION


# Função para processar a seleção da competição
async def select_competition(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    context.user_data['competicao'] = update.callback_query.data.split("_")[1]  # Guardar competição selecionada
    await update.callback_query.edit_message_text(text="Por favor, envie as imagens com os dados.")

    # Esperar pelo envio de imagens
    return VALORES


# Função para processar o envio das imagens e registrar na planilha
async def process_images(update: Update, context: CallbackContext) -> int:
    # Verificar se o update.message existe e se o usuário enviou uma imagem
    if update.message and update.message.photo:
        try:
            file_id = update.message.photo[-1].file_id  # Obter a imagem de maior resolução
            new_file = await context.bot.get_file(file_id)
            file_path = f"{update.message.chat_id}_image.jpg"
            await new_file.download_to_drive(file_path)

            # Processar a imagem para extração de texto
            extracted_text = extract_text_from_image(file_path)

            # Obter a primeira linha do texto extraído
            first_line = extracted_text.splitlines()[0] if extracted_text else ""

            # Obter a data da legenda, se presente, ou a data atual
            image_caption = update.message.caption
            date = get_date_from_caption(image_caption) if image_caption else datetime.now().strftime("%d/%m")

            # Extrair o mês da data obtida para definir a aba de destino
            date_obj = datetime.strptime(date, "%d/%m")
            month = date_obj.strftime("%B")  # Mês da data obtida em português

            # Extrair os valores monetários no formato "R$ x,yy" ou "RS x,yy"
            values = parse_values_from_extracted_text(extracted_text)

            # Verificar se os valores são válidos
            if len(values) >= 2:  # Precisamos de pelo menos 2 valores monetários
                try:
                    sheet = authenticate_google_sheets()
                    
                    # Tentar acessar a aba do mês correspondente
                    try:
                        worksheet = sheet.worksheet(month)
                    except gspread.WorksheetNotFound:
                        worksheet = sheet.add_worksheet(title=month, rows="100", cols="6")
                        logging.info(f"Aba criada: {month}")

                    # Encontrar a primeira linha vazia nas cinco colunas específicas
                    all_values = worksheet.get_all_values()
                    next_row = None

                    for i, row in enumerate(all_values, start=1):
                        # Checar se as cinco colunas específicas estão vazias
                        if all([cell == '' for cell in row[:5]]):  # Checar se as primeiras 5 colunas estão vazias
                            next_row = i
                            break

                    # Se não encontrar uma linha vazia, insere após a última linha
                    if next_row is None:
                        next_row = len(all_values) + 1

                    # Inserir os dados na planilha na ordem correta
                    worksheet.update(
                        f'A{next_row}',
                        [[date, context.user_data['tipster'], context.user_data['competicao'], first_line, values[0],
                          values[1], values[1] / values[0] if values[0] != 0 else 0]]
                    )

                    # Confirmar o registro e mostrar todos os dados extraídos
                    await update.message.reply_text(
                        f"Dados registrados com sucesso!\n"
                        f"Primeira linha: {first_line}\nValores monetários: {values}\nmês: {month}",
                        reply_markup=options_menu()
                    )
                except Exception as e:
                    logging.error("Erro ao registrar dados na planilha: %s", e)
                    await update.message.reply_text(
                        f"Erro ao registrar dados na planilha. Tente novamente.\n\n"
                        f"Primeira linha: {first_line}\n"
                        f"Valores monetários extraídos: {values}"
                    )
            else:
                await update.message.reply_text(
                    f"Não foi possível extrair valores suficientes\n"
                    f"\nPrimeira linha: {first_line}\n"
                    f"Valores monetários extraídos: {values}"
                )
        except Exception as e:
            logging.error("Erro ao processar a imagem: %s", e)
            await update.message.reply_text(
                f"Erro ao processar a imagem. Tente novamente."
                f"Primeira linha: {first_line}\nValores monetários extraídos: {values}"
            )
    else:
        await update.message.reply_text("Por favor, envie apenas imagens com os dados.")
    
    return VALORES  # Retorna ao estado VALORES para processar a próxima imagem ou aguardar nova ação


# Função para extrair texto da imagem
def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='eng').strip()  # Remover espaços em branco no início e no fim
        return text  # Retorna o texto completo extraído
    except Exception as e:
        logging.error("Erro ao extrair texto da imagem: %s", e)
        return ""
    

# Função para extrair texto da imagem
#def extract_text_from_image(file_path):
#    try:
#        result = reader.readtext(file_path, detail=0)  # Extrai apenas o texto, sem detalhes das coordenadas
#        text = " ".join(result).strip()  # Junta as partes do texto e remove espaços desnecessários
#        return text  # Retorna o texto completo extraído
#    except Exception as e:
#        logging.error("Erro ao extrair texto da imagem com EasyOCR: %s", e)
#        return ""


# Função para analisar os valores extraídos
def parse_values_from_extracted_text(text):
    # Procurar valores precedidos de "R$" ou "RS" e no formato "x,yy" ou com "I" ou "O" após os números
    pattern = r"(?:R\$|RS)\s*(\d+[,\d{2}]+)"  # Aceitar apenas números com vírgula para as casas decimais
    values = []

    # Encontrar todos os valores precedidos de "R$" ou "RS" no texto
    matches = re.findall(pattern, text)

    for match in matches:
        # Substituir letras "I" e "O" por números (tanto maiúsculas quanto minúsculas)
        cleaned_match = match.replace("l", "1").replace("O", "0").replace("I", "1").replace("o", "0").replace("i", "1")
        
        try:
            # Verificar se o valor tem o formato adequado (número com vírgula e 2 casas decimais)
            if cleaned_match.count(",") == 1 and len(cleaned_match.split(",")[1]) == 2:
                # Converter o valor encontrado para float (substituindo vírgula por ponto)
                value = float(cleaned_match.replace(",", "."))
                values.append(value)
            else:
                continue  # Ignorar se o formato não for válido
        except ValueError:
            # Ignorar caso o valor não seja convertível para float
            continue

        if len(values) >= 2:  # Se já temos 2 valores, podemos parar
            break

    return values

# Função de troca para escolher um novo tipster
async def trocar_tipster(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Selecione o novo tipster:")

    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Tipsters")
        tipsters = worksheet.get_all_values()
        keyboard = [[InlineKeyboardButton(row[0], callback_data=f"tipster_{row[0]}")] for row in tipsters]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Escolha o tipster:", reply_markup=reply_markup)
    except Exception as e:
        logging.error("Erro ao listar tipsters: %s", e)
        await update.callback_query.edit_message_text(text="Erro ao listar tipsters.")

    return SELECT_TIPSTER


# Função de troca para escolher uma nova competição
async def trocar_competicao(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Selecione a nova competição:")

    try:
        sheet = authenticate_google_sheets()
        worksheet = sheet.worksheet("Competições")
        competicoes = worksheet.get_all_values()
        keyboard = [[InlineKeyboardButton(row[0], callback_data=f"competicao_{row[0]}")] for row in competicoes]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Escolha a competição:", reply_markup=reply_markup)
    except Exception as e:
        logging.error("Erro ao listar competições: %s", e)
        await update.callback_query.edit_message_text(text="Erro ao listar competições.")

    return SELECT_COMPETITION

# Função para voltar ao envio de imagens após trocar tipster ou competição
async def voltar_para_envio_de_imagens(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Agora, por favor, continue enviando as imagens.")
    return VALORES



# Função para extrair a data da legenda
def get_date_from_caption(caption):
    try:
        date_str = caption.strip()  # Remover espaços em branco
        datetime_obj = datetime.strptime(date_str, "%d/%m")  # Converte para objeto datetime
        return datetime_obj.strftime("%d/%m")  # Retorna no formato desejado
    except ValueError:
        logging.warning("Data na legenda inválida. Usando data atual.")
        return datetime.now().strftime("%d/%m")

# Função principal para iniciar o bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [
                CallbackQueryHandler(cadastrar_tipster, pattern='cadastrar_tipster'),
                CallbackQueryHandler(cadastrar_competicao, pattern='cadastrar_competicao'),
                CallbackQueryHandler(planilhar, pattern='planilhar'),
                CallbackQueryHandler(ver_tipsters, pattern='ver_tipsters'),
                CallbackQueryHandler(ver_competicoes, pattern='ver_competicoes'),
                CallbackQueryHandler(encerrar_bot, pattern='encerrar_bot')
            ],
            OPTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tipster_name)],
            OPTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_competition_name)],
            SELECT_TIPSTER: [
                CallbackQueryHandler(select_tipster),
                CallbackQueryHandler(voltar_para_envio_de_imagens, pattern='^menu_imagens$')
            ],
            SELECT_COMPETITION: [
                CallbackQueryHandler(select_competition),
                CallbackQueryHandler(voltar_para_envio_de_imagens, pattern='^menu_imagens$')
            ],
            VALORES: [
                MessageHandler(filters.PHOTO, process_images),
                CallbackQueryHandler(trocar_tipster, pattern='^trocar_tipster$'),  # Botão para trocar tipster
                CallbackQueryHandler(trocar_competicao, pattern='^trocar_competicao$')  # Botão para trocar competição
            ],
        },
        fallbacks=[
            CallbackQueryHandler(voltar_menu_principal, pattern='menu_principal'),
            CallbackQueryHandler(encerrar_bot, pattern='encerrar')
        ],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()