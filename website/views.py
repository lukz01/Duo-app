from flask import Blueprint, render_template, request, flash, jsonify, url_for, redirect, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Note, Financeiro, Documento
from . import db
import json
from datetime import datetime
import requests
import os


views = Blueprint('views', __name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}


# Notas, Tarefas.

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    marker_options = {
        "0": "0 - Todas",
        "1": "1 - Organização Financeira",
        "2": "2 - Passaporte/Visto",
        "3": "3 - Pesquisa Inicial",
        "4": "4 - Definir Datas",
        "5": "5 - Compra de Passagens",
        "6": "6 - Escolha de Hospedagem",
        "7": "7 - Compra dos Ingressos",
        "8": "8 - Definir Transportes",
        "9": "9 - Atividades nos Parques",
        "10": "10 - Planejar Compras e Restaurantes",
        "11": "11 - Comprar Dólares",
        "12": "12 - Preparativos Pré-Viagem",
        "13": "13 - Chegada em Orlando",
        "14": "14 - Dias de Parques",
        "15": "15 - Dias Alternativos"
    }
    
    if request.method == 'POST':
        note = request.form.get('note')
        due_date_str = request.form.get('due_date')
        marker = request.form.get('marker') 

        if len(note) < 1:
            flash('Nota muito curta!', category='error')
        else:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
            new_note = Note(data=note, user_id=current_user.id, due_date=due_date, marker=marker)
            db.session.add(new_note)
            db.session.commit()
            flash('Nota adicionada!', category='success')


    selected_marker = request.args.get('marker')
    
    if selected_marker and selected_marker != "0":  
        notes = Note.query.filter_by(user_id=current_user.id, marker=selected_marker).all()
    else:
        notes = Note.query.filter_by(user_id=current_user.id).all()  

    return render_template("home.html", user=current_user, marker_options=marker_options, notes=notes)



@views.route('/complete-note/<int:note_id>', methods=['POST'])
def complete_note(note_id):
    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        note.completed = not note.completed
        db.session.commit()
    return jsonify({})

@views.route('/update-note', methods=['POST'])
def update_note():
    note_data = json.loads(request.data)
    note_id = note_data['noteId']
    completed = note_data['completed']
    note = Note.query.get(note_id)

    if note:
        note.completed = completed
        db.session.commit()

    return jsonify({})

@views .route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)

    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    
    return jsonify({})



# Financeiro, Carteira 

def obter_cotacao_dolar():
    url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            return data["USDBRL"]["bid"] 
        else:
            return None  
    except requests.RequestException:
        return None
    
@views.route('/finance', methods=['GET', 'POST'])
@login_required
def finance():
    cotacao_dolar = obter_cotacao_dolar()
    
    filtro_gastos = request.args.get('filtro_gastos', default='0', type=str)
    
    if filtro_gastos == '0':
        gastos = Financeiro.query.filter_by(user_id=current_user.id).all()
    else:
        categorias = {
            "Passagens Aéreas": "Passagens Aéreas",
            "Seguro de Viagem": "Seguro de Viagem",
            "Passaporte": "Passaporte",
            "Visto": "Visto",
            "Hospedagem": "Hospedagem",
            "Transporte": "Transporte",
            "Ingressos para Parques": "Ingressos para Parques",
            "Alimentação": "Alimentação",
            "Compras": "Compras",
            "Estacionamento": "Estacionamento",
            "Celular": "Celular",
            "Taxas de Serviço e Resort": "Taxas de Serviço e Resort",
            "Entretenimento Adicional": "Entretenimento Adicional",
            "Aluguel de Equipamentos": "Aluguel de Equipamentos",
            "Outros Gastos": "Outros Gastos",
        }

        categoria_selecionada = next((k for k, v in categorias.items() if v == filtro_gastos), None)

        if categoria_selecionada:
            gastos = Financeiro.query.filter_by(user_id=current_user.id, categoria=categoria_selecionada).all()
        else:
            gastos = Financeiro.query.filter_by(user_id=current_user.id).all()

    # Calcular a soma de todos os gastos do usuário para o saldo restante
    todos_gastos = Financeiro.query.filter_by(user_id=current_user.id).all() 
    soma_gastos = sum(float(gasto.valor) for gasto in todos_gastos)  

    # Obter o objetivo de gastos do usuário
    if current_user.financeiros:
        objetivo_gastos = current_user.financeiros[0].objetivo_gastos  # Obtendo o objetivo da primeira instância
    else:
        objetivo_gastos = 100.00  

    # Calcular o saldo restante
    saldo_restante = objetivo_gastos - soma_gastos

    # Formatação do saldo restante para o estilo brasileiro
    saldo_restante_formatado = f'R$ {saldo_restante:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    # Processamento da requisição POST para atualizar ou adicionar gastos
    if request.method == 'POST':
        if 'objetivo_gastos' in request.form:  
            novo_objetivo = request.form.get('objetivo_gastos')
            if not current_user.financeiros:  
                financeiro = Financeiro(user_id=current_user.id, objetivo_gastos=novo_objetivo)
                db.session.add(financeiro)
            else:
                current_user.financeiros[0].objetivo_gastos = novo_objetivo
            
            db.session.commit()
            flash('Objetivo de gastos atualizado!', category='success')
            return redirect(url_for('views.finance', filtro_gastos=filtro_gastos))
        
        elif 'adicionar_gasto' in request.form:  # Adiciona um novo gasto
            categoria = request.form.get('categoria')
            descricao = request.form.get('descricao')
            valor = request.form.get('valor')
            moeda = request.form.get('moeda')  

            # Criação do novo gasto
            novo_gasto = Financeiro(
                user_id=current_user.id,
                categoria=categoria,
                descricao=descricao,
                valor=float(valor.replace(',', '.')),
                moeda=moeda  # Armazena a moeda
            )
            
            db.session.add(novo_gasto)
            db.session.commit()
            flash('Gasto adicionado com sucesso!', category='success')
            return redirect(url_for('views.finance', filtro_gastos=filtro_gastos))
    
    # Renderiza o template com os gastos filtrados e a cotação do dólar
    return render_template('finance.html', 
                           user=current_user, 
                           cotacao_dolar=cotacao_dolar, 
                           gastos=gastos, 
                           filtro_gastos=filtro_gastos,
                           saldo_restante=saldo_restante_formatado)  


@views.route('/excluir_gasto/<int:gasto_id>', methods=['POST'])
@login_required
def excluir_gasto(gasto_id):
    gasto = Financeiro.query.get(gasto_id)
    if gasto and gasto.user_id == current_user.id:
        db.session.delete(gasto)
        db.session.commit()
        flash('Gasto excluído com sucesso!', category='success')
    else:
        flash('Gasto não encontrado ou não autorizado!', category='error')
    return redirect(url_for('views.finance'))


# Documentos 


@views.route('/documents')
@login_required
def documents():
    categorias = ['Documentos', 'Ingressos', 'Comprovantes', 'Passagens', 'Prints', 'Reservas', 'Outros']
    documentos = Documento.query.filter_by(user_id=current_user.id).all()
    return render_template('documents.html', categorias=categorias, documentos=documentos, user=current_user)

@views.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    categoria = request.form.get('categoria')
    arquivo = request.files.get('arquivo')

    if arquivo:
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
        if '.' in arquivo.filename and arquivo.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            caminho = os.path.join(UPLOAD_FOLDER, arquivo.filename)
            os.makedirs('uploads', exist_ok=True)
            arquivo.save(caminho)

            novo_documento = Documento(
                user_id=current_user.id,
                categoria=categoria,
                nome_arquivo=arquivo.filename,
                caminho_arquivo=caminho
            )

            db.session.add(novo_documento)
            db.session.commit()

            flash("Documento adicionado com sucesso!", "success")
        else:
            flash("Tipo de arquivo não permitido. Por favor, envie um arquivo PDF, JPG ou PNG.", "danger")
    else:
        flash('Por favor, selecione um arquivo!', 'danger')

    return redirect(url_for('views.documents'))

@views.route('/uploads/<path:filename>')
def upload_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@views.route('/view_document/<int:documento_id>')
@login_required
def view_document(documento_id):
    documento = Documento.query.get_or_404(documento_id)
    return send_from_directory(UPLOAD_FOLDER, documento.nome_arquivo, as_attachment=False)


@views.route('/delete_document/<int:documento_id>', methods=['GET', 'POST'])
@login_required
def delete_document(documento_id):
    documento = Documento.query.get_or_404(documento_id)

    # Remove o documento do sistema de arquivos
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, documento.nome_arquivo))
    except Exception as e:
        print(f"Erro ao remover o arquivo: {e}")

    # Remove o documento do banco de dados
    db.session.delete(documento)
    db.session.commit()

    flash("Documento excluído com sucesso!", "success")
    return redirect(url_for('views.documents'))



# Calendario

@views.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html', user=current_user)
