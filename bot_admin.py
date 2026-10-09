# ============================================================
# BOT TELEGRAM - COMANDOS DE ADMINISTRADOR
# Instale: pip install python-telegram-bot requests
# ============================================================

import json
import os
import random
import re
import requests
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ============================================================
# TOKEN DO BOT
# ============================================================
TOKEN = "8843258561:AAE5KjeWx5syJJ3DvPyOX_O0nUrttIytzZU"

# ============================================================
# ID DO DONO (ADMINISTRADOR PRINCIPAL)
# ============================================================
DONO_ID = 7848571699

os.environ['TZ'] = 'America/Fortaleza'


# ---------------- UTILITÁRIOS ----------------
def getstr(url, start, fim, n):
    try:
        return url.split(start)[n].split(fim)[0]
    except Exception:
        return ""


def l(size):
    basic = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    return ''.join(random.choice(basic) for _ in range(size))


def bot(method, params):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        r = requests.post(url, data=params, timeout=30)
        return r.text
    except Exception as e:
        print("Erro API:", e)
        return ""


def read_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, data):
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print("Erro ao salvar:", e)
        return False


def buscaprox(text, cmd, ignore_list):
    out = text
    for ig in ignore_list:
        out = out.replace(ig, '', 1)
    return out.strip()


def is_dono(user_id):
    return int(user_id) == int(DONO_ID)


def is_admin(user_id):
    if is_dono(user_id):
        return True
    users = read_json("./usuarios.json")
    u = users.get(str(user_id))
    return bool(u and str(u.get('adm', '')).lower() == 'true')


# ============================================================
# FUNÇÃO PRINCIPAL DE COMANDOS ADMIN
# ============================================================
async def adm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    chat_id = message.chat.id
    from_id = message.from_user.id

    if not is_admin(from_id):
        return

    text = message.text
    args = re.findall(r'[A-Za-z0-9@\.\-\_]+', text.lower())
    if not args:
        return
    cmd = args[0].lstrip('/')

    # --------------------------------------------------------
    # /admin  |  /menu
    # --------------------------------------------------------
    if cmd in ("admin", "menu"):
        menu = "===================================\n"
        menu += "          [MENU DO BOT ADMIN]\n"
        menu += "===================================\n"
        menu += "/addcc - adiciona novas ccs\n"
        menu += "/addmix - adiciona novos mixs\n"
        menu += "/alteraritem - altera os preços\n"
        menu += "/alterarmix - altera os preços dos mix\n"
        menu += "/veruser - info de um usuário pelo user\n"
        menu += "/addsaldo - add saldo a um usuário\n"
        menu += "/resaldo - remove saldo de um usuário\n"
        menu += "/getsaldo - obter o saldo de um usuario\n"
        menu += "/addgift - gera um gift para resgatar saldo\n"
        menu += "/users - LISTA OS USUARIOS DO BOT\n"
        menu += "/setwelcome - adiciona msg de boas vindas\n"
        menu += "/addadmin - adiciona um admin\n"
        menu += "/showadms - mostra admins\n"
        menu += "/delladm - deleta um admin\n"
        menu += "/send - envia msg para os usuarios\n"
        bot("sendMessage", {"chat_id": chat_id, "text": menu})
        return

    # --------------------------------------------------------
    # /addcc  ->  NUMERO|MES|ANO|CVV|NIVEL|VALOR
    # --------------------------------------------------------
    if cmd == "addcc":
        txt = ("ℹ️ O comando /addcc funciona assim:\n\n"
               "➕ Formato: /addcc NUMERO|MES|ANO|CVV|NIVEL|VALOR\n\n"
               "📌 Exemplo:\n"
               "/addcc 5276600064049219|12|2024|721|gold|50\n"
               "/addcc 5276600064049219|12|2024|721|standard|10\n\n"
               "ℹ️ Aceita também vírgula, ponto, barra ou espaço como separador.\n"
               "Um cartão por linha.")
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id, "text": txt})
            return

        ccs = text.split("\n")
        ccs[0] = ccs[0].replace("/addcc", "").strip()
        logs = []

        bot("sendMessage", {"chat_id": chat_id,
                            "text": "✅ Adicionando cartões... Aguarde."})

        openprice = read_json('./resource/conf.json')
        openprice.setdefault('price', {})

        for value in ccs:
            value = value.strip()
            if not value:
                continue

            normal = re.sub(r'[:;,\s/]+', '|', value)
            parts = [p for p in normal.split("|") if p != ""]

            if len(parts) < 6:
                logs.append(f"❌ {value} — formato inválido (precisa 6 campos).")
                continue

            numero = parts[0].strip()
            mes = parts[1].strip()
            ano = parts[2].strip()
            cvv = parts[3].strip()
            nivel = parts[4].strip().lower()
            try:
                valor = int(parts[5].strip())
            except Exception:
                logs.append(f"❌ {value} — valor inválido.")
                continue

            if len(mes) == 1:
                mes = "0" + mes
            if len(ano) == 2:
                ano = "20" + ano

            bin_num = numero[:6]

            # Gera dados fake
            try:
                r = requests.post(
                    "https://www.4devs.com.br/ferramentas_online.php",
                    data='acao=gerar_pessoa&sexo=I&pontuacao=S&idade=0&cep_estado=&txt_qtde=1&cep_cidade=',
                    timeout=15
                )
                d = r.json()
                nome, cpf = d.get("nome", ""), d.get("cpf", "")
            except Exception:
                nome, cpf = "", ""

            # Consulta BIN (só pra pegar bandeira/banco/pais/tipo)
            try:
                binchk = requests.get(
                    f'https://storebot.store/binsearch.php?bin={bin_num}', timeout=15
                ).text
                ban = getstr(binchk, '"bandeira": "', '"', 1).upper()
                type_ = getstr(binchk, '"tipo": "', '"', 1).upper()
                banco = getstr(binchk, '"banco": "', '"', 1).upper()
                pais = getstr(binchk, '"pais": "', '"', 1).upper()
            except Exception:
                ban = type_ = banco = pais = ""

            diretorio = "brasil" if pais.strip() == "BRASIL" else "gringa"
            path_dir = f"./ccs/{diretorio}"
            os.makedirs(path_dir, exist_ok=True)

            file_path = f"./ccs/{diretorio}/{nivel}.json"
            file_data = read_json(file_path, {})

            idx = len(file_data) + 1
            file_data[str(idx)] = {
                "cc": numero, "mes": mes, "ano": ano, "cvv": cvv,
                "nome": nome, "cpf": cpf,
                "bandeira": ban.strip(), "nivel": nivel,
                "tipo": type_.strip(), "banco": banco,
                "pais": pais, "valor": valor
            }

            openprice['price'][nivel] = valor

            if write_json(file_path, file_data):
                msg = (f"✔️ Cartão adicionado!\n\n"
                       f"💳 {numero} {mes}/{ano} {cvv}\n"
                       f"🎖 Nível: {nivel.upper()}\n"
                       f"💰 Valor: R$ {valor}\n"
                       f"🌎 {ban or '?'} | {type_ or '?'} | {banco or '?'} | {pais or '?'}")
                bot("sendMessage", {"chat_id": chat_id, "text": msg})

        write_json('./resource/conf.json', openprice)

        bot("sendMessage", {"chat_id": chat_id,
                            "text": "⚙️ Logs:\n" + "\n".join(logs) + "\n✅ Processo concluído!"})
        return

    # --------------------------------------------------------
    # /send
    # --------------------------------------------------------
    if cmd == "send":
        msg_send = buscaprox(text, "/send", ["/send"])
        if not msg_send:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "⚙️ Exemplo: /send Olá pessoal, bem-vindos!"})
            return

        reply_markup = {"inline_keyboard": [[
            {"text": "🔹", "callback_data": "envia_nao_0"},
            {"text": "🔸", "callback_data": "envia_sim_0"}
        ]]}

        with open("./msgs.txt", "w", encoding="utf-8") as f:
            f.write(msg_send.strip())

        txt = (f"<b>✨ Envio de mensagem em massa</b>\n\n"
               f"<b>📩 Mensagem:</b> {msg_send}\n\n"
               f"<b>⚠️ Escolha o modo:</b>\n"
               f"<b>🔹 Enviar para todos!</b>\n"
               f"<b>🔸 Enviar e deletar os que não receberem!</b>")

        bot("sendMessage", {"chat_id": chat_id, "text": txt, "parse_mode": "html",
                            "reply_markup": json.dumps(reply_markup),
                            "reply_to_message_id": message.message_id})
        return

    # --------------------------------------------------------
    # /veruser
    # --------------------------------------------------------
    if cmd == "veruser":
        r = bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>⚙️ Obtendo informações...</b>",
                                "reply_to_message_id": message.message_id,
                                "parse_mode": "html"})
        try:
            message_id = json.loads(r)['result']['message_id']
        except Exception:
            message_id = None

        users = read_json("./usuarios.json")
        ccscom = read_json("./ccsompradas.json")
        saldocom = read_json("./salcocomprado.json")

        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "ops, /veruser [username]\nExemplo: /veruser @terrordelas"})
            return

        user = text.split(" ")[1].replace("@", "")
        iduser = None
        for key, v in users.items():
            if str(v.get('username', '')).strip() == user.strip():
                iduser = key
                break

        if not iduser:
            bot("editMessageText", {"message_id": message_id, "chat_id": chat_id,
                                    "text": "<b>Usuário não encontrado!</b>",
                                    "parse_mode": "html"})
            return

        dados = users[iduser]
        totalcc = len(ccscom.get(iduser, {}).get('ccs', []))
        totalmix = len(ccscom.get(iduser, {}).get('mixs', []))
        totalsaldo = len(saldocom.get(iduser, []))

        txt = "<b>Informações do usuário!</b>\n\n"
        txt += f"🧰 <b>Id da carteira:</b> {iduser}\n"
        txt += f"💎 <b>Nome:</b> {dados.get('nome', '')}\n"
        txt += f"💰 <b>Saldo:</b> {dados.get('saldo', '')}\n"
        txt += f"📅 <b>Cadastro:</b> {datetime.datetime.fromtimestamp(dados.get('cadastro', 0)).strftime('%d/%m/%Y %H:%M:%S')}\n"
        txt += f"💳 <b>CCs compradas:</b> {totalcc}\n"
        txt += f"💳 <b>Mixs comprados:</b> {totalmix}\n"
        txt += f"🏛 <b>Recargas:</b> {totalsaldo}\n"

        bot("editMessageText", {"message_id": message_id, "chat_id": chat_id,
                                "text": txt, "reply_to_message_id": message.message_id,
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /getsemlevel
    # --------------------------------------------------------
    if cmd == "getsemlevel":
        open_data = read_json("./ccs.json")
        out = ""
        for v in open_data.get('semnivel', []):
            out += f"ID DA CC: <code>{v.get('id','')}</code>\n"
            out += f"CC: {v.get('cc','')}\n"
            out += f"Bandeira: {v.get('bandeira','')}\n"
            out += f"Tipo: {v.get('tipo','')}\n"
            out += f"Banco: {v.get('banco','')}\n"
            out += f"Pais: {v.get('pais','')}\n\n"
        bot("sendMessage", {"chat_id": chat_id, "text": out, "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /users
    # --------------------------------------------------------
    if cmd == "users":
        users = read_json("./usuarios.json")
        chunks = [list(users.items())[i:i+10] for i in range(0, len(users), 10)] or [[]]
        tt = len(chunks)

        txt = f"<b>✨ LISTA DE USUÁRIOS\n🍃 mostrando: 1 de {tt}</b>\n"
        for iduser, v in chunks[0]:
            txt += f"\n🧰 <b>Id:</b> {iduser}\n"
            txt += f"💎 <b>Nome:</b> {v.get('nome','')}\n"
            txt += f"💰 <b>Saldo:</b> {v.get('saldo','')}\n"
            txt += f"📅 <b>Cadastro:</b> {datetime.datetime.fromtimestamp(v.get('cadastro',0)).strftime('%d/%m/%Y %H:%M:%S')}\n"

        reply_markup = {"inline_keyboard": [
            [{"text": "<<", "callback_data": "users_ant_0"},
             {"text": ">>", "callback_data": "users_prox_0"}],
            [{"text": "🔙 Voltar", "callback_data": "menu"}]
        ]}

        bot("sendMessage", {"chat_id": chat_id, "text": txt, "parse_mode": "html",
                            "reply_to_message_id": message.message_id,
                            "reply_markup": json.dumps(reply_markup)})
        return

    # --------------------------------------------------------
    # /addadmin
    # --------------------------------------------------------
    if cmd == "addadmin":
        parts = text.split(" ")
        id_user = parts[1] if len(parts) > 1 else ""

        if not id_user:
            bot("sendMessage", {"chat_id": chat_id, "text": "user: /addadmin [id_user]",
                                "reply_to_message_id": message.message_id})
            return

        users = read_json("./usuarios.json")
        if id_user not in users:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Usuário não encontrado!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        if not is_dono(from_id):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Erro: Apenas o dono pode add admins!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        nome = users[id_user].get('nome', '')
        username = users[id_user].get('username', '')
        users[id_user]['adm'] = True

        if write_json('./usuarios.json', users):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"<b>Novo admin adicionado\nId: {id_user}\nNome: {nome}\nUser: {username}!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
        else:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Erro ao adicionar admin!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
        return

    # --------------------------------------------------------
    # /delladm
    # --------------------------------------------------------
    if cmd == "delladm":
        parts = text.split(" ")
        id_user = parts[1] if len(parts) > 1 else ""

        if not id_user:
            bot("sendMessage", {"chat_id": chat_id, "text": "user: /delladm [id_user]",
                                "reply_to_message_id": message.message_id})
            return

        users = read_json("./usuarios.json")
        if id_user not in users:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Usuário não encontrado!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        if not is_dono(from_id):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Erro: Apenas o dono pode remover admins!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        nome = users[id_user].get('nome', '')
        username = users[id_user].get('username', '')
        users[id_user]['adm'] = False

        if write_json('./usuarios.json', users):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"<b>Id: {id_user}\nNome: {nome}\nUser: {username}\nNão é mais admin!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "<b>Erro!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
        return

    # --------------------------------------------------------
    # /showadms
    # --------------------------------------------------------
    if cmd == "showadms":
        if not is_dono(from_id):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Erro: Apenas o dono pode ver os admins!</b>",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        users = read_json("./usuarios.json")
        adms = []
        for key, v in users.items():
            if str(v.get("adm", "")).lower() == "true":
                adms.append(f"🔐 ID: {key}\n✨ Nome: {v.get('nome','')}\n🍃 User: {v.get('username','')}\n")

        bot("sendMessage", {"chat_id": chat_id,
                            "text": "\n".join(adms) or "Nenhum admin cadastrado.",
                            "parse_mode": "html",
                            "reply_to_message_id": message.message_id})
        return

    # --------------------------------------------------------
    # /editnivel
    # --------------------------------------------------------
    if cmd == "editnivel":
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /editnivel [id_cc] [nivel]",
                                "parse_mode": "html"})
            return

        values = text.split(" ")
        id_cc = values[1] if len(values) > 1 else ""
        nivel = " ".join(values[2:]).strip()

        open_data = read_json("./ccs.json")
        cc_found = None
        for v in open_data.get('semnivel', []):
            if str(v.get('id', '')) == str(id_cc):
                cc_found = v
                break

        if not cc_found:
            bot("sendMessage", {"chat_id": chat_id, "text": "CC não encontrada!",
                                "parse_mode": "html"})
            return

        open_data.setdefault(nivel, []).append({
            "id": len(open_data.get(nivel, [])),
            "cc": cc_found.get('cc',''),
            "bandeira": cc_found.get('bandeira',''),
            "tipo": cc_found.get('tipo',''),
            "nivel": nivel.upper(),
            "banco": cc_found.get('banco',''),
            "pais": cc_found.get('pais','')
        })
        open_data['semnivel'] = [s for s in open_data.get('semnivel', [])
                                 if str(s.get('id','')) != str(id_cc)]

        if write_json('./ccs.json', open_data):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"Nivel alterado!\nCC: {cc_found.get('cc','')}\nNivel: {nivel}"})
        return

    # --------------------------------------------------------
    # /getnivel
    # --------------------------------------------------------
    if cmd == "getnivel":
        open_data = read_json("./ccs.json")
        bot("sendMessage", {"chat_id": chat_id,
                            "text": "Níveis encontrados:\n<code>" + "\n".join(open_data.keys()) + "</code>",
                            "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /alteraritem
    # --------------------------------------------------------
    if cmd == "alteraritem":
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /alteraritem [nivel] [valor]\nExemplo: /alteraritem gold 10"})
            return

        openprice = read_json('./resource/conf.json')
        nivel = args[1].lower()
        price = args[2] if len(args) > 2 else None

        if not price:
            bot("sendMessage", {"chat_id": chat_id, "text": "user: /alteraritem [nivel] [valor]"})
            return

        openprice.setdefault('price', {})[nivel] = int(price)

        if write_json('./resource/conf.json', openprice):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"✅ Preço alterado!\n🎖 {nivel} → R$ {price}",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "Erro ao alterar preço!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /addsaldo
    # --------------------------------------------------------
    if cmd == "addsaldo":
        if len(args) < 3:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /addsaldo [id_carteira] [valor]",
                                "parse_mode": "html"})
            return

        openusers = read_json('./usuarios.json')
        cliente_id = args[1]

        if cliente_id not in openusers:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Cliente não encontrado!</b>",
                                "parse_mode": "html"})
            return

        saldo_an = int(openusers[cliente_id].get('saldo', 0))
        openusers[cliente_id]['saldo'] = saldo_an + int(args[2])
        openusers[cliente_id]['dataLimite'] = int(
            (datetime.datetime.now() + datetime.timedelta(weeks=1)).timestamp())

        if write_json('./usuarios.json', openusers):
            s = openusers[cliente_id].get('nome', '')
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"<b>💰 Saldo adicionado!\nCliente: {s}\nValor: {args[2]}\n\n⚠️ Válido por 1 semana.</b>",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao add saldo!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /resaldo
    # --------------------------------------------------------
    if cmd == "resaldo":
        if len(args) < 3:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /resaldo [id_usuario] [valor]",
                                "parse_mode": "html"})
            return

        openusers = read_json('./usuarios.json')
        cliente_id = args[1]

        if cliente_id not in openusers:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Cliente não encontrado!</b>",
                                "parse_mode": "html"})
            return

        saldo_an = int(openusers[cliente_id].get('saldo', 0))
        openusers[cliente_id]['saldo'] = saldo_an - int(args[2])

        if write_json('./usuarios.json', openusers):
            s = openusers[cliente_id].get('nome', '')
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"Saldo removido do cliente: {s}",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao remover saldo!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /getsaldo
    # --------------------------------------------------------
    if cmd == "getsaldo":
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id, "text": "user: /getsaldo [id_usuario]",
                                "parse_mode": "html"})
            return

        openusers = read_json('./usuarios.json')
        cliente_id = args[1]

        if cliente_id not in openusers:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>Cliente não encontrado!</b>",
                                "parse_mode": "html"})
            return

        s = openusers[cliente_id].get('nome', '')
        saldo = openusers[cliente_id].get('saldo', '')
        bot("sendMessage", {"chat_id": chat_id,
                            "text": f"Saldo do cliente: <b>{s}</b> = <b>{saldo}</b>",
                            "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /addgift
    # --------------------------------------------------------
    if cmd == "addgift":
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /addgift [valor]\nExemplo: /addgift 10"})
            return

        valor = int(args[1])
        gif = l(10)

        openprice = read_json('./gifts.json', {})
        openprice.setdefault('gifts', {})

        while gif in openprice:
            gif = l(10)

        data = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        openprice[gif] = {"valor": valor, "date": data}

        if write_json('./gifts.json', openprice):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"<b>✅ Gift criado!\nCódigo:</b> <code>{gif}</code>\n<b>Valor:</b> {valor} (saldo)\n\n⚠️ Uso único!",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao gerar Gift!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /addmix
    # --------------------------------------------------------
    if cmd == "addmix":
        if len(args) < 2:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /addmix [ccs]\nExemplo:\n/addmix 4066695543634018|12|2025|176\n5447317485524324|05|2027|822"})
            return

        ccs_text = text[len('addmix')+1:].strip()
        ccs_list = [c.strip() for c in ccs_text.split("\n") if c.strip()]
        mix = len(ccs_list)

        openmix = read_json("./mix.json")
        openmix.setdefault(str(mix), []).append("\n".join(ccs_list))

        if write_json("./mix.json", openmix):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"mix - {mix}\n" + "\n".join(ccs_list) + "\nSalvo!",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao salvar mix!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /alterarmix
    # --------------------------------------------------------
    if cmd == "alterarmix":
        if len(args) < 3:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "user: /alterarmix [mix] [valor]\nExemplo: /alterarmix 5 50"})
            return

        openprice = read_json('./resource/conf.json')
        mix = args[1]
        valor = args[2]

        openprice.setdefault('pricemix', {})[mix] = int(valor)

        if write_json('./resource/conf.json', openprice):
            bot("sendMessage", {"chat_id": chat_id,
                                "text": f"✅ Preço do mix alterado!\n🎖 mix {mix} → R$ {valor}",
                                "parse_mode": "html"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao alterar preço!",
                                "parse_mode": "html"})
        return

    # --------------------------------------------------------
    # /setwelcome
    # --------------------------------------------------------
    if cmd == "setwelcome":
        msg = buscaprox(text, "/setwelcome", ["/setwelcome"])
        if not msg:
            bot("sendMessage", {"chat_id": chat_id,
                                "text": "<b>setwelcome</b>\n\nuse: /setwelcome [mensagem]\n\n"
                                        "Parâmetros: {nome} e {id}\n\n"
                                        "Exemplo:\n/setwelcome *{nome}*, seja bem vindo!",
                                "parse_mode": "html",
                                "reply_to_message_id": message.message_id})
            return

        teste = msg.replace("{nome}", "testenome").replace("{id}", "1934634734")
        bot("sendMessage", {"chat_id": chat_id, "text": teste, 'parse_mode': "Markdown"})

        conf = read_json("./resource/conf.json")
        conf['welcome'] = msg.strip()

        if write_json("./resource/conf.json", conf):
            bot("sendMessage", {"chat_id": chat_id, "text": "Boas vindas salva!"})
        else:
            bot("sendMessage", {"chat_id": chat_id, "text": "Erro ao salvar!"})
        return


# ============================================================
# HANDLERS
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await adm(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "envia_sim_0":
        users = read_json("./usuarios.json")
        try:
            with open("./msgs.txt", "r", encoding="utf-8") as f:
                msg = f.read()
        except Exception:
            msg = ""
        enviados = 0
        for uid in users.keys():
            r = bot("sendMessage", {"chat_id": uid, "text": msg, "parse_mode": "Markdown"})
            if r:
                enviados += 1
        await query.edit_message_text(f"✅ Mensagem enviada para {enviados} usuários!")

    elif data == "envia_nao_0":
        await query.edit_message_text("❌ Envio cancelado!")

    elif data == "menu":
        await query.edit_message_text("Use /menu para abrir o menu.")


# ============================================================
# MAIN
# ============================================================
def main():
    users = read_json("./usuarios.json") if os.path.exists("./usuarios.json") else {}
    uid = str(DONO_ID)
    if uid not in users:
        users[uid] = {
            "nome": "Dono",
            "username": "dono",
            "saldo": 0,
            "cadastro": int(datetime.datetime.now().timestamp()),
            "adm": True
        }
    else:
        users[uid]['adm'] = True
    write_json("./usuarios.json", users)

    os.makedirs("./resource", exist_ok=True)
    os.makedirs("./ccs/brasil", exist_ok=True)
    os.makedirs("./ccs/gringa", exist_ok=True)

    if not os.path.exists("./resource/conf.json"):
        write_json("./resource/conf.json",
                   {"dono": DONO_ID, "price": {}, "pricemix": {}, "welcome": ""})
    else:
        conf = read_json("./resource/conf.json")
        conf['dono'] = DONO_ID
        write_json("./resource/conf.json", conf)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print(f"🤖 Bot de ADMIN rodando... Dono: {DONO_ID}")
    app.run_polling()


if __name__ == "__main__":
    main()