"""
Automação de preenchimento do Google Forms com dados de alunos.
Estratégia: clica no campo RA para garantir foco, depois usa Tab entre campos.

Requisitos:
    pip install pyautogui pyperclip

Como usar:
    1. Abra o formulário no navegador e maximize a janela
    2. Execute: python preencher_forms.py
    3. Não mexa no mouse/teclado durante a execução
"""

import csv
import re
import time
import webbrowser
import threading
import sys
import pyautogui
import pyperclip

# ─────────────────────────────────────────────
# CONFIGURAÇÕES GERAIS
# ─────────────────────────────────────────────
FORM_URL    = "https://forms.gle/SKZ1C4xT895VTMmq7"
CSV_FILE    = "notas_alunos.csv"

WAIT_LOAD   = 10   # segundos aguardando a página carregar
WAIT_CLICK  = 1    # pausa após clique
WAIT_TAB    = 1    # pausa após Tab
WAIT_SUBMIT = 6    # aguarda confirmação de envio
WAIT_NEXT   = 6    # aguarda "Enviar outra resposta" carregar

# ─────────────────────────────────────────────
# COORDENADAS  ← EDITE AQUI SE NECESSÁRIO
# ─────────────────────────────────────────────

# Coordenada do campo RA (primeiro campo do formulário)
CAMPO_RA = (433, 395)

# Coordenada do link "Enviar outra resposta" (página de confirmação)
LINK_OUTRA_RESPOSTA = (466, 246)


# ─────────────────────────────────────────────
# FAILSAFE — 4 CANTOS DA TELA
# ─────────────────────────────────────────────
def monitor_failsafe(margem: int = 10) -> None:
    """
    Roda em background e encerra o programa se o mouse
    chegar a qualquer um dos 4 cantos da tela.
    margem = área em pixels considerada como "canto".
    """
    larg, alt = pyautogui.size()
    cantos = [
        (0,        0      ),  # superior esquerdo
        (larg - 1, 0      ),  # superior direito
        (0,        alt - 1),  # inferior esquerdo
        (larg - 1, alt - 1),  # inferior direito
    ]
    while True:
        x, y = pyautogui.position()
        for cx, cy in cantos:
            if abs(x - cx) <= margem and abs(y - cy) <= margem:
                print("\n⚠ Failsafe ativado! Mouse no canto da tela. Encerrando...")
                sys.exit(1)
        time.sleep(0.1)



import re


def normalizar_nota(valor: str) -> str:
    """
    Normaliza o valor de uma nota:
    - Vazio ou 'n/a'            → 'Não informado'
    - 'faltou' ou 'falta'       → 'Falta'
    - Separador vírgula         → ponto  (ex: 7,2 → 7.2)
    """
    v = valor.strip().lower()

    if v in ("", "n/a", "na", "-"):
        return "Não informado"

    if v in ("faltou", "falta"):
        return "Falta"

    # Normaliza separador decimal
    return valor.strip().replace(",", ".")


def normalizar_nome(valor: str) -> str:
    """
    Primeira letra de cada palavra em maiúsculo, restante minúsculo.
    Ex: 'JOÃO SILVA' → 'João Silva' | 'ana lima' → 'Ana Lima'
    """
    return valor.strip().title()


def normalizar_ra(valor: str) -> str:
    """
    Remove prefixos não numéricos (ex: 'RA12345' → '12345').
    Remove zeros ou caracteres antes do primeiro '1' (ex: '0123456' → '123456').
    Vazio → 'Não informado'.
    """
    v = valor.strip()
    if not v:
        return "Não informado"

    # Remove prefixos de letras (ex: 'ra', 'RA')
    v = re.sub(r"^[a-zA-Z\s]+", "", v).strip()

    # Localiza o primeiro dígito '1' e descarta tudo antes dele
    idx = v.find("1")
    if idx == -1:
        return "Não informado"

    return v[idx:]


def colar(texto: str) -> None:
    """Cola o texto via área de transferência."""
    pyperclip.copy(str(texto))
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(WAIT_TAB)


def preencher_campo(texto: str) -> None:
    """Seleciona tudo no campo atual, apaga e cola o valor."""
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    colar(texto)


def avancar_campo() -> None:
    """Vai para o próximo campo com Tab."""
    pyautogui.press("tab")
    time.sleep(WAIT_TAB)


# ─────────────────────────────────────────────
# LEITURA DO CSV
# ─────────────────────────────────────────────
def ler_alunos(caminho_csv: str) -> list[dict]:
    alunos = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            alunos.append({
                "RA":    normalizar_ra(row["RA"]),
                "Nome":  normalizar_nome(row["Nome"]),
                "Nota1": normalizar_nota(row["Nota01"]),
                "Nota2": normalizar_nota(row["Nota02"]),
                "TF1":   normalizar_nota(row["TF01"]),
                "TF2":   normalizar_nota(row["TF02"]),
            })
    return alunos


# ─────────────────────────────────────────────
# PREENCHIMENTO DE UM ALUNO
# ─────────────────────────────────────────────
def preencher_formulario(aluno: dict) -> None:
    print(f"  → Preenchendo: RA={aluno['RA']} | {aluno['Nome']}")

    # Clica diretamente no campo RA para garantir o foco correto
    pyautogui.click(*CAMPO_RA)
    time.sleep(WAIT_CLICK)

    # RA
    preencher_campo(aluno["RA"])
    avancar_campo()

    # Nome
    preencher_campo(aluno["Nome"])
    avancar_campo()

    # Nota 1
    preencher_campo(aluno["Nota1"])
    avancar_campo()

    # Nota 2
    preencher_campo(aluno["Nota2"])
    avancar_campo()

    # TF1
    preencher_campo(aluno["TF1"])
    avancar_campo()

    # TF2
    preencher_campo(aluno["TF2"])
    avancar_campo()

    # Tab até o botão Enviar e pressiona Enter
    pyautogui.press("enter")
    print("  → Formulário enviado. Aguardando confirmação...")
    time.sleep(WAIT_SUBMIT)


# ─────────────────────────────────────────────
# CLICAR EM "ENVIAR OUTRA RESPOSTA"
# ─────────────────────────────────────────────
def clicar_enviar_outra_resposta() -> None:
    pyautogui.click(*LINK_OUTRA_RESPOSTA)
    print("  → Clicou em 'Enviar outra resposta'. Aguardando carregamento...")
    time.sleep(WAIT_NEXT)


# ─────────────────────────────────────────────
# FLUXO PRINCIPAL
# ─────────────────────────────────────────────
def main() -> None:
    alunos = ler_alunos(CSV_FILE)
    total  = len(alunos)
    print(f"Alunos encontrados no CSV: {total}")

    if total == 0:
        print("Nenhum aluno encontrado. Verifique o arquivo CSV.")
        return

    print(f"\nAbrindo formulário: {FORM_URL}")
    webbrowser.open(FORM_URL)
    print(f"Aguardando {WAIT_LOAD}s para a página carregar...")
    time.sleep(WAIT_LOAD)

    for indice, aluno in enumerate(alunos):
        print(f"\n[{indice + 1}/{total}] Iniciando preenchimento...")
        preencher_formulario(aluno)

        if indice < total - 1:
            clicar_enviar_outra_resposta()

    print("\n✓ Todos os alunos foram registrados com sucesso!")

    # Após registrar todos, abre o menu de consulta
    menu_consulta(alunos)


# ─────────────────────────────────────────────
# CÁLCULO DE NOTAS
# ─────────────────────────────────────────────
def calcular_notas(aluno: dict) -> dict:
    """
    Parte 1: (Nota1 * 8 + TF1 * 2) / 10
    Parte 2: (Nota2 * 8 + TF2 * 2) / 10
    Nota Final: média entre Parte 1 e Parte 2
    Valores 'Não informado' ou 'Falta' são tratados como 0.
    """
    def para_numero(v: str) -> float:
        if v in ("Não informado", "Falta"):
            return 0.0
        return float(v)

    nota1 = para_numero(aluno["Nota1"])
    nota2 = para_numero(aluno["Nota2"])
    tf1   = para_numero(aluno["TF1"])
    tf2   = para_numero(aluno["TF2"])

    parte1     = (nota1 * 8) / 10 + tf1
    parte2     = (nota2 * 8) / 10 + tf2
    nota_final = (parte1 + parte2) / 2
    situacao   = "APROVADO" if nota_final >= 6 else "REPROVADO"

    return {
        "parte1":     parte1,
        "parte2":     parte2,
        "nota_final": nota_final,
        "situacao":   situacao,
    }


# ─────────────────────────────────────────────
# EXIBIÇÃO DO BOLETIM
# ─────────────────────────────────────────────
def exibir_boletim(aluno: dict) -> None:
    calc = calcular_notas(aluno)

    print()
    print("=" * 45)
    print(f"  RA   : {aluno['RA']}")
    print(f"  Nome : {aluno['Nome']}")
    print("-" * 45)
    print(f"  Nota 1  : {aluno['Nota1']:<6}  TF1 : {aluno['TF1']}")
    print(f"  Nota 2  : {aluno['Nota2']:<6}  TF2 : {aluno['TF2']}")
    print("-" * 45)
    print(f"  Parte 1 : {calc['parte1']:.2f}  (Nota1×8/10 + TF1)")
    print(f"  Parte 2 : {calc['parte2']:.2f}  (Nota2×8/10 + TF2)")
    print(f"  Nota Final: {calc['nota_final']:.2f}")
    print(f"  Situação  : {calc['situacao']}")
    print("=" * 45)


# ─────────────────────────────────────────────
# MENU DE CONSULTA
# ─────────────────────────────────────────────
def menu_consulta(alunos: list[dict]) -> None:
    # Índices para busca rápida
    por_ra   = {a["RA"].lower(): a for a in alunos}
    por_nome = {a["Nome"].lower(): a for a in alunos}

    print()
    print("=" * 45)
    print("  CONSULTA DE ALUNOS")
    print("  Digite o RA ou Nome do aluno para consultar.")
    print("  Digite 'sair' para encerrar.")
    print("=" * 45)

    while True:
        print()
        busca = input("  Buscar: ").strip()

        if busca.lower() == "sair":
            print("  Encerrando. Até mais!")
            break

        if not busca:
            continue

        chave = busca.lower()

        # Busca exata por RA
        if chave in por_ra:
            exibir_boletim(por_ra[chave])
            continue

        # Busca exata por Nome
        if chave in por_nome:
            exibir_boletim(por_nome[chave])
            continue

        # Busca parcial por Nome (ex: digitar só o primeiro nome)
        encontrados = [a for a in alunos if chave in a["Nome"].lower()]
        if len(encontrados) == 1:
            exibir_boletim(encontrados[0])
        elif len(encontrados) > 1:
            print(f"  {len(encontrados)} alunos encontrados:")
            for a in encontrados:
                print(f"    RA: {a['RA']}  |  {a['Nome']}")
            print("  Refine a busca para ver o boletim completo.")
        else:
            print("  Aluno não encontrado. Verifique o RA ou Nome digitado.")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.05

    # Inicia o monitor de cantos em background
    t = threading.Thread(target=monitor_failsafe, daemon=True)
    t.start()

    print("=" * 55)
    print(" Automação Google Forms — Lançamento de Notas")
    print("=" * 55)
    print("ATENÇÃO: Não mexa no mouse/teclado durante a execução.")
    print("Para cancelar: mova o mouse para QUALQUER CANTO da tela.")
    print()

    for i in range(5, 0, -1):
        print(f"  Iniciando em {i}s...", end="\r")
        time.sleep(1)
    print()

    main()
