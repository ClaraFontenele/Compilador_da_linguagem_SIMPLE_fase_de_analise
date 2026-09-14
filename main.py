
"""
Alunas: 
        Ana Maria Ferreira de Souza  - 2312130055
        Maria Clara Fontenele Silva  - 2312130230
--------------------------------------------------------------------------------
GRAMATICA UTILIZADA (LL(1): sem recursao a esquerda, ja fatorada a esquerda:

    programa        -> linha { linha }
    linha           -> NUM comando (NEWLINE | ETX)
    comando         -> 'rem'
                      | 'input' ID
                      | 'let' ID '=' expr
                      | 'print' ID
                      | 'goto' NUM
                      | 'if' expr_rel 'goto' NUM
                      | 'end'
    expr_rel        -> expr oprel expr
    oprel           -> '==' | '!=' | '>' | '<' | '>=' | '<='
    expr            -> termo expr_l
    expr_l          -> '+' termo expr_l | '-' termo expr_l | EPSILON
    termo           -> fator termo_l
    termo_l         -> '*' fator termo_l | '/' fator termo_l | '%' fator termo_l | EPSILON
    fator           -> ID | NUM

--------------------------------------------------------------------------------
CLASSES DE TOKEN (mesma numeracao usada em sala e no material):

    10 newline (fim de instrucao)      31 ==                61 rem
    03 fim de arquivo (ETX)            32 !=                62 input
    11 = (atribuicao)                  33 >                 63 let
    21 + (adicao)                      34 <                 64 print
    22 - (subtracao)                   35 >=                65 goto
    23 * (multiplicacao)               36 <=                66 if
    24 / (divisao inteira)             41 identificador     67 end
    25 % (resto da divisao)            51 constante numerica
--------------------------------------------------------------------------------
"""

import sys


# ==============================================================================
# 1) TABELA DE CLASSES DE TOKEN E PALAVRAS RESERVADAS
# ==============================================================================

NEWLINE, ETX = 10, 3                                                                           #fim de instrucao ; fim de arquivo
OP_ATRIB = 11                                                                                  #atribuicao
OP_MAIS, OP_MENOS, OP_MULT, OP_DIV, OP_MOD = 21, 22, 23, 24, 25                                #operacoes
OP_IGUAL, OP_DIF, OP_MAIOR, OP_MENOR, OP_MAIOR_IGUAL, OP_MENOR_IGUAL = 31, 32, 33, 34, 35, 36  #relacoes
ID = 41                                                                                        #identificador
CTE = 51                                                                                       #constante
REM, INPUT, LET, PRINT, GOTO, IF, END = 61, 62, 63, 64, 65, 66, 67                             #palavras reservadas

PALAVRAS_RESERVADAS = {
    'rem': REM, 'input': INPUT, 'let': LET, 'print': PRINT,
    'goto': GOTO, 'if': IF, 'end': END,
}

NOME_CLASSE = {
    NEWLINE: 'fim de instrucao', ETX: 'fim de arquivo', OP_ATRIB: "'='",
    OP_MAIS: "'+'", OP_MENOS: "'-'", OP_MULT: "'*'", OP_DIV: "'/'", OP_MOD: "'%'",
    OP_IGUAL: "'=='", OP_DIF: "'!='", OP_MAIOR: "'>'", OP_MENOR: "'<'",
    OP_MAIOR_IGUAL: "'>='", OP_MENOR_IGUAL: "'<='",
    ID: 'identificador', CTE: 'constante numerica',
    REM: "'rem'", INPUT: "'input'", LET: "'let'", PRINT: "'print'",
    GOTO: "'goto'", IF: "'if'", END: "'end'",
}

OPERADORES_RELACIONAIS = {OP_IGUAL, OP_DIF, OP_MAIOR, OP_MENOR, OP_MAIOR_IGUAL, OP_MENOR_IGUAL}


def descreve(classe):
    return NOME_CLASSE.get(classe, str(classe))


class Token:
    # Cada token carrega: classe, valor (lexema) e posicao (linha, coluna).

    __slots__ = ('classe', 'valor', 'linha', 'coluna')

    def __init__(self, classe, valor, linha, coluna):
        self.classe = classe
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return "[{}, {}, ({}, {})]".format(self.classe, self.valor, self.linha, self.coluna)


# ==============================================================================
# 2) ERROS DE COMPILACAO
# ==============================================================================

class ErroCompilacao:
    def __init__(self, fase, linha, coluna, mensagem):
        self.fase = fase              # 'lexico' | 'sintatico' | 'semantico'
        self.linha = linha
        self.coluna = coluna
        self.mensagem = mensagem

    def __str__(self):
        rotulo = {'lexico': 'Erro lexico', 'sintatico': 'Erro sintatico',
                   'semantico': 'Erro semantico'}[self.fase]
        if self.coluna is not None:
            return "{} (linha {}, coluna {}): {}".format(
                rotulo, self.linha, self.coluna, self.mensagem)
        return "{} (linha {}): {}".format(rotulo, self.linha, self.mensagem)


# ==============================================================================
# 3) ANALISADOR LEXICO
# ==============================================================================

class AnalisadorLexico:
    # Le o programa-fonte ja detectando e reportando erros lexicos
    

    def __init__(self, codigo_fonte, erros):
        self.codigo = codigo_fonte
        self.erros = erros
        self.pos = 0
        self.tam = len(codigo_fonte)
        self.linha = 1
        self.coluna = 1

    # -- utilitarios de leitura -------------------------------------------------
    def _char_atual(self):
        return self.codigo[self.pos] if self.pos < self.tam else ''

    def _proximo_char(self):
        return self.codigo[self.pos + 1] if self.pos + 1 < self.tam else ''

    def _avancar(self):
        c = self._char_atual()
        self.pos += 1
        if c == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _erro(self, mensagem, linha=None, coluna=None):
        self.erros.append(ErroCompilacao(
            'lexico', linha or self.linha, coluna or self.coluna, mensagem))

    # -- laco principal -----------------------------------------------------
    def tokenizar(self):
        tokens = []
        while self.pos < self.tam:
            c = self._char_atual()

            if c == '\n':
                l, col = self.linha, self.coluna
                self._avancar()
                tokens.append(Token(NEWLINE, '\\n', l, col))
                continue

            if c in ' \t\r':
                self._avancar()
                continue

            if c.isdigit():
                tokens.append(self._ler_numero())
                continue

            if c.islower():
                tok = self._ler_palavra()
                if tok is not None:
                    tokens.append(tok)
                continue

            if c.isupper():
                self._erro(
                    "letra maiuscula '{}' nao permitida (a linguagem SIMPLE so "
                    "aceita letras minusculas fora de comentarios 'rem')".format(c))
                self._avancar()
                continue

            # operadores e delimitadores ------------------------------------
            l, col = self.linha, self.coluna
            if c == '=' :
                if self._proximo_char() == '=':
                    self._avancar(); self._avancar()
                    tokens.append(Token(OP_IGUAL, '==', l, col))
                else:
                    self._avancar()
                    tokens.append(Token(OP_ATRIB, '=', l, col))
                continue
            if c == '!':
                if self._proximo_char() == '=':
                    self._avancar(); self._avancar()
                    tokens.append(Token(OP_DIF, '!=', l, col))
                else:
                    self._avancar()
                    self._erro("caractere '!' invalido (esperava-se '!=')", l, col)
                continue
            if c == '>':
                if self._proximo_char() == '=':
                    self._avancar(); self._avancar()
                    tokens.append(Token(OP_MAIOR_IGUAL, '>=', l, col))
                else:
                    self._avancar()
                    tokens.append(Token(OP_MAIOR, '>', l, col))
                continue
            if c == '<':
                if self._proximo_char() == '=':
                    self._avancar(); self._avancar()
                    tokens.append(Token(OP_MENOR_IGUAL, '<=', l, col))
                else:
                    self._avancar()
                    tokens.append(Token(OP_MENOR, '<', l, col))
                continue
            if c == '+':
                self._avancar(); tokens.append(Token(OP_MAIS, '+', l, col)); continue
            if c == '-':
                self._avancar(); tokens.append(Token(OP_MENOS, '-', l, col)); continue
            if c == '*':
                self._avancar(); tokens.append(Token(OP_MULT, '*', l, col)); continue
            if c == '/':
                self._avancar(); tokens.append(Token(OP_DIV, '/', l, col)); continue
            if c == '%':
                self._avancar(); tokens.append(Token(OP_MOD, '%', l, col)); continue

            # qualquer outro caractere e invalido na linguagem SIMPLE
            self._erro("caractere nao reconhecido '{}'".format(c), l, col)
            self._avancar()

        tokens.append(Token(ETX, 'ETX', self.linha, self.coluna))
        return tokens

    def _ler_numero(self):
        l, col = self.linha, self.coluna
        inicio = self.pos
        while self._char_atual().isdigit():
            self._avancar()
        lexema = self.codigo[inicio:self.pos]
        return Token(CTE, int(lexema), l, col)

    def _ler_palavra(self):
        l, col = self.linha, self.coluna
        inicio = self.pos
        while self._char_atual().islower():
            self._avancar()
        lexema = self.codigo[inicio:self.pos]

        if lexema in PALAVRAS_RESERVADAS:
            classe = PALAVRAS_RESERVADAS[lexema]
            if classe == REM:
                # Tudo ate o fim da linha e comentario e e ignorado, inclusive
                # maiusculas, digitos e simbolos (regra explicita da linguagem).
                while self._char_atual() not in ('\n', '') :
                    self._avancar()
            return Token(classe, lexema, l, col)

        if len(lexema) == 1:
            return Token(ID, lexema, l, col)

        self._erro(
            "identificador invalido '{}' (identificadores da linguagem SIMPLE "
            "possuem exatamente uma letra)".format(lexema), l, col)
        return None


# ==============================================================================
# 4) TABELA DE SIMBOLOS / TABELA DE LINHAS
# ==============================================================================

class TabelaSimbolos:
    """Guarda as variaveis reconhecidas durante a analise, cada entrada e a declaracao de um nome,
    com atributos (aqui: tipo fixo 'integer', linha da 1a ocorrencia e numero de usos)."""

    def __init__(self):
        self._entradas = {}

    def declarar_ou_usar(self, nome, linha):
        if nome not in self._entradas:
            self._entradas[nome] = {'tipo': 'integer', 'primeira_linha': linha, 'usos': 0}
        self._entradas[nome]['usos'] += 1

    def itens(self):
        return sorted(self._entradas.items())


class TabelaLinhas:
    """Controla os numeros de linha definidos no programa (para validar a
    ordem crescente) e os alvos de goto/if...goto pendentes de checagem
    semantica (podem ser referencias 'para frente')."""

    def __init__(self, erros):
        self.erros = erros
        self.definidas = {}          # numero_linha -> linha_fisica do token
        self.ultima_definida = None
        self.referencias_pendentes = []   # (numero_alvo, token_origem)

    def registrar_definicao(self, token_num):
        n = token_num.valor
        if n in self.definidas:
            self.erros.append(ErroCompilacao(
                'semantico', token_num.linha, token_num.coluna,
                "numero de linha {} duplicado (ja utilizado anteriormente no "
                "programa)".format(n)))
        elif self.ultima_definida is not None and n <= self.ultima_definida:
            self.erros.append(ErroCompilacao(
                'semantico', token_num.linha, token_num.coluna,
                "numero de linha {} fora de ordem crescente (a linha anterior "
                "era {})".format(n, self.ultima_definida)))
        else:
            self.definidas[n] = token_num.linha
            self.ultima_definida = n

        if n not in self.definidas:
            # ainda registra para permitir goto ateh esta linha em outros
            # pontos do programa, mesmo apos erro de ordenacao/duplicidade.
            self.definidas.setdefault(n, token_num.linha)

    def registrar_referencia(self, token_num):
        self.referencias_pendentes.append(token_num)

    def validar_referencias(self):
        for token_num in self.referencias_pendentes:
            if token_num.valor not in self.definidas:
                self.erros.append(ErroCompilacao(
                    'semantico', token_num.linha, token_num.coluna,
                    "'goto {}' referencia uma linha que nao existe no "
                    "programa".format(token_num.valor)))


# ==============================================================================
# 5) ANALISADOR SINTATICO (recursivo preditivo) + ACOES SEMANTICAS
# ==============================================================================

class AnalisadorSintatico:
    """Parser recursivo preditivo (top-down) para a gramatica da linguagem
    SIMPLE. As acoes semanticas (tabela de simbolos, tabela de linhas,
    divisao por zero) sao executadas durante o proprio reconhecimento."""

    SINCRONIZADORES = {NEWLINE, ETX}

    def __init__(self, tokens, erros):
        self.tokens = tokens
        self.erros = erros
        self.i = 0
        self.simbolos = TabelaSimbolos()
        self.tabela_linhas = TabelaLinhas(erros)
        self.viu_end = False

    # -- utilitarios de navegacao --------------------------------------------
    def _atual(self):
        return self.tokens[self.i]

    def _avancar(self):
        tok = self.tokens[self.i]
        if self.i < len(self.tokens) - 1:
            self.i += 1
        return tok

    def _erro_sintatico(self, mensagem, token=None):
        token = token or self._atual()
        self.erros.append(ErroCompilacao('sintatico', token.linha, token.coluna, mensagem))

    def _esperar(self, classe, descricao=None):
        tok = self._atual()
        if tok.classe == classe:
            return self._avancar()
        self._erro_sintatico(
            "esperava-se {}, mas foi encontrado {} ('{}')".format(
                descricao or descreve(classe), descreve(tok.classe), tok.valor))
        return None

    def _sincronizar(self):
        """MODO PANICO: descarta tokens ate encontrar um NEWLINE ou o fim do
        arquivo (ETX), exatamente a estrategia 'Modo Panico' vista em sala,
        usando o fim de instrucao como token de sincronizacao."""
        while self._atual().classe not in self.SINCRONIZADORES:
            self._avancar()
        if self._atual().classe == NEWLINE:
            self._avancar()

    # -- programa -------------------------------------------------------------
    def parse_programa(self):
        while self._atual().classe != ETX:
            if self._atual().classe == NEWLINE:
                self._avancar()   # linha em branco
                continue
            self._parse_linha()
        self.tabela_linhas.validar_referencias()
        if not self.viu_end:
            ultimo = self.tokens[-1]
            self.erros.append(ErroCompilacao(
                'semantico', ultimo.linha, None,
                "o programa nao possui nenhum comando 'end'"))

    def _parse_linha(self):
        tok_num = self._esperar(CTE, 'um numero de linha')
        if tok_num is None:
            self._sincronizar()
            return
        self.tabela_linhas.registrar_definicao(tok_num)

        ok = self._parse_comando()
        if not ok:
            self._sincronizar()
            return

        if self._atual().classe not in (NEWLINE, ETX):
            self._erro_sintatico(
                "conteudo inesperado apos o comando ('{}'); cada linha deve "
                "conter apenas um comando".format(self._atual().valor))
            self._sincronizar()
            return

        if self._atual().classe == NEWLINE:
            self._avancar()

    # -- comando ----------------------------------------------------------------
    def _parse_comando(self):
        tok = self._atual()

        if tok.classe == REM:
            self._avancar()
            return True

        if tok.classe == INPUT:
            self._avancar()
            tok_id = self._esperar(ID, 'um identificador (variavel)')
            if tok_id is None:
                return False
            self.simbolos.declarar_ou_usar(tok_id.valor, tok_id.linha)
            return True

        if tok.classe == LET:
            self._avancar()
            tok_id = self._esperar(ID, 'um identificador (variavel)')
            if tok_id is None:
                return False
            self.simbolos.declarar_ou_usar(tok_id.valor, tok_id.linha)
            if self._esperar(OP_ATRIB, "'='") is None:
                return False
            return self._parse_expr() is not None

        if tok.classe == PRINT:
            self._avancar()
            tok_id = self._esperar(ID, 'um identificador (variavel)')
            if tok_id is None:
                return False
            self.simbolos.declarar_ou_usar(tok_id.valor, tok_id.linha)
            return True

        if tok.classe == GOTO:
            self._avancar()
            tok_num = self._esperar(CTE, 'um numero de linha')
            if tok_num is None:
                return False
            self.tabela_linhas.registrar_referencia(tok_num)
            return True

        if tok.classe == IF:
            self._avancar()
            if self._parse_expr_rel() is None:
                return False
            if self._esperar(GOTO, "'goto'") is None:
                return False
            tok_num = self._esperar(CTE, 'um numero de linha')
            if tok_num is None:
                return False
            self.tabela_linhas.registrar_referencia(tok_num)
            return True

        if tok.classe == END:
            self._avancar()
            self.viu_end = True
            return True

        self._erro_sintatico(
            "esperava-se um comando (rem, input, let, print, goto, if ou "
            "end), mas foi encontrado {} ('{}')".format(descreve(tok.classe), tok.valor))
        return False

    # -- expressoes (E -> T E' ; E' -> + T E' | - T E' | eps) -------------------
    def _parse_expr_rel(self):
        if self._parse_expr() is None:
            return None
        tok = self._atual()
        if tok.classe not in OPERADORES_RELACIONAIS:
            self._erro_sintatico(
                "esperava-se um operador relacional (==, !=, >, <, >= ou <=), "
                "mas foi encontrado {} ('{}')".format(descreve(tok.classe), tok.valor))
            return None
        self._avancar()
        if self._parse_expr() is None:
            return None
        return True

    def _parse_expr(self):
        if self._parse_termo() is None:
            return None
        while self._atual().classe in (OP_MAIS, OP_MENOS):
            self._avancar()
            if self._parse_termo() is None:
                return None
        return True

    def _parse_termo(self):
        primeiro = self._parse_fator()
        if primeiro is None:
            return None
        while self._atual().classe in (OP_MULT, OP_DIV, OP_MOD):
            tok_op = self._avancar()
            tok_divisor = self._atual()
            resultado = self._parse_fator()
            if resultado is None:
                return None
            if tok_op.classe in (OP_DIV, OP_MOD) and \
               tok_divisor.classe == CTE and tok_divisor.valor == 0:
                self.erros.append(ErroCompilacao(
                    'semantico', tok_divisor.linha, tok_divisor.coluna,
                    "divisao por zero (o divisor da operacao '{}' e a "
                    "constante 0)".format(tok_op.valor)))
        return True

    def _parse_fator(self):
        tok = self._atual()
        if tok.classe == ID:
            self._avancar()
            self.simbolos.declarar_ou_usar(tok.valor, tok.linha)
            return True
        if tok.classe == CTE:
            self._avancar()
            return True
        self._erro_sintatico(
            "esperava-se um operando (identificador ou constante numerica), "
            "mas foi encontrado {} ('{}')".format(descreve(tok.classe), tok.valor))
        return None


# ==============================================================================
# 6) FUNCAO PRINCIPAL DA FASE DE ANALISE
# ==============================================================================

def compilar(codigo_fonte):
    erros = []

    lexico = AnalisadorLexico(codigo_fonte, erros)
    tokens = lexico.tokenizar()

    sintatico = AnalisadorSintatico(tokens, erros)
    sintatico.parse_programa()

    erros.sort(key=lambda e: (e.linha, e.coluna if e.coluna is not None else -1))
    return erros, sintatico


import sys

def selecionar_arquivo():
    # Mapeamento de opções para os arquivos correspondentes
    arquivos = {
        "1": ("1_entrada_taylor_swift.txt", "Programa Taylor Swift (Válido)"),
        "2": ("2_valido_soma.txt", "Validação: Soma"),
        "3": ("3_valido_maior.txt", "Validação: Maior valor"),
        "4": ("4_erro_lex_id_grande.txt", "Erro Léxico: Identificador grande"),
        "5": ("5_erro_sint_1_maiuscula.txt", "Erro Sintático 1: Maiúscula"),
        "6": ("6_erro_sint_2_operando.txt", "Erro Sintático 2: Operando"),
        "7": ("7_erro_sint_3_if_sem_goto.txt", "Erro Sintático 3: IF sem GOTO"),
        "8": ("8_erro_sem_1_goto_invalido.txt", "Erro Semântico 1: GOTO inválido"),
        "9": ("9_erro_sem_2_ordem.txt", "Erro Semântico 2: Ordem incorreta"),
        "10": ("10_erro_sem_3_div_zero.txt", "Erro Semântico 3: Divisão por zero"),
        "11": ("11_arquivo_para_editar.txt", "Erro Personalizável, arquivo em branco")
    }

    while True:
        print("\n" + "=" * 60)
        print(" DIGITE O NÚMERO DO ARQUIVO DE TESTE PARA O COMPILADOR")
        print("=" * 60)
        for chave, (_, descricao) in arquivos.items():
            print(f" [{chave:>2}] - {descricao}")
        print(" [99] - Sair do programa")
        print("=" * 60)

        opcao = input("Digite o número da opção desejada: ").strip()

        if opcao == "99":
            return None  # Retorna None para indicar que o usuário escolheu sair
        elif opcao in arquivos:
            return arquivos[opcao][0]
        else:
            print(f"\n\033[31m[!] Opção '{opcao}' inválida. Por favor, escolha um número da lista.\033[0m")
            input("\nPressione ENTER para voltar ao menu...")


def main():
    while True:
        # Se passar via argumento de linha de comando usa ele; senão abre o menu
        if len(sys.argv) > 1:
            caminho_arquivo = sys.argv[1]
        else:
            caminho_arquivo = selecionar_arquivo()

        # Se a escolha foi encerrar o programa (opção 99)
        if caminho_arquivo is None:
            print("\nPrograma encerrado pelo usuário. Até logo!")
            return

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                codigo_fonte = f.read()
        except FileNotFoundError:
            print(f"\nErro: O arquivo '{caminho_arquivo}' não foi encontrado.")
            input("\nPressione ENTER para voltar ao menu...")
            continue

        print("\n" + "° 。" * 20)
        print("° 。° 。 COMPILADOR SIMPLE - FASE DE ANALISE (LEXICA/SINTATICA/SEMANTICA) ° 。° 。")
        print("° 。" * 20)
        print(f"\n\033[32mArquivo analisado:\033[0m {caminho_arquivo}\n")

        erros, sintatico = compilar(codigo_fonte)

        if not erros:
            print("★ Compilacao concluida com sucesso: nenhum erro lexico,sintatico ou semantico encontrado. ★\n")
            print("Tabela de simbolos (variaveis):")
            if sintatico.simbolos.itens():
                for nome, info in sintatico.simbolos.itens():
                    print("  {:<3} tipo={:<8} 1a linha={:<6} usos={}".format(
                        nome, info['tipo'], info['primeira_linha'], info['usos']))
            else:
                print("  (nenhuma variavel utilizada)")

            print("\nTabela de linhas definidas:")
            print("  " + ", ".join(str(n) for n in sorted(sintatico.tabela_linhas.definidas)))
        else:
            print("Compilacao encontrou {} erro(s):\n".format(len(erros)))
            for e in erros:
                print("  - " + str(e))
            print("\nCompilacao falhou.")

        print("=" * 70)

        # Se veio por linha de comando, não faz sentido voltar ao menu — encerra
        if len(sys.argv) > 1:
            return

        input("\nPressione ENTER para voltar ao menu...")



if __name__ == '__main__':
    main()
