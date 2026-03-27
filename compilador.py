"""
Compilador PascalLite - Fase 1: Análise Léxica e Sintática

Implementa as fases de análise léxica e sintática para a linguagem PascalLite,
uma versão simplificada do Pascal com tipos integer e boolean, comandos if e while.

Integrantes do grupo:
    - (preencher com os nomes dos integrantes)

Uso: python compilador.py <arquivo_fonte>
"""

import sys


# ============================================================
# Definição dos tipos de átomos (tokens)
# ============================================================

# Palavras reservadas
PROGRAM     = "PROGRAM"
BEGIN       = "BEGIN"
END         = "END"
VAR         = "VAR"
INTEGER     = "INTEGER"
BOOLEAN     = "BOOLEAN"
IF          = "IF"
THEN        = "THEN"
ELSE        = "ELSE"
WHILE       = "WHILE"
DO          = "DO"
READ        = "READ"
WRITE       = "WRITE"
TRUE        = "TRUE"
FALSE       = "FALSE"
NOT         = "NOT"
AND         = "AND"
OR          = "OR"
DIV         = "DIV"
MOD         = "MOD"

# Identificadores e números
IDENTIF     = "IDENTIF"
NUM         = "NUM"

# Delimitadores
PONTO_VIRG  = "PONTO_VIRG"     # ;
VIRGULA     = "VIRGULA"        # ,
DOIS_PONTOS = "DOIS_PONTOS"    # :
PONTO       = "PONTO"          # .
ABRE_PAR    = "ABRE_PAR"       # (
FECHA_PAR   = "FECHA_PAR"      # )

# Operador de atribuição
ATRIB       = "ATRIB"          # :=

# Operadores aritméticos
MAIS        = "MAIS"           # +
MENOS       = "MENOS"          # -
VEZES       = "VEZES"          # *
BARRA       = "BARRA"          # /

# Operadores relacionais
MENOR       = "MENOR"          # <
MENOR_IGUAL = "MENOR_IGUAL"    # <=
IGUAL       = "IGUAL"          # =
DIFERENTE   = "DIFERENTE"      # <>
MAIOR       = "MAIOR"          # >
MAIOR_IGUAL = "MAIOR_IGUAL"    # >=

# Tipos especiais
COMENTARIO  = "COMENTARIO"
EOF_ATOM    = "EOF"
ERRO        = "ERRO"

# Mapeamento de palavras reservadas (comparação em minúsculo)
PALAVRAS_RESERVADAS = {
    'program': PROGRAM, 'begin': BEGIN,   'end': END,
    'var': VAR,         'integer': INTEGER,'boolean': BOOLEAN,
    'if': IF,           'then': THEN,     'else': ELSE,
    'while': WHILE,     'do': DO,         'read': READ,
    'write': WRITE,     'true': TRUE,     'false': FALSE,
    'not': NOT,         'and': AND,       'or': OR,
    'div': DIV,         'mod': MOD,
}


# ============================================================
# Classe Atomo — representa um token reconhecido
# ============================================================

class Atomo:
    """Estrutura que armazena as informações de um átomo reconhecido."""

    def __init__(self, tipo, lexema, linha, valor=None):
        self.tipo = tipo        # tipo do átomo (ex: PROGRAM, IDENTIF, NUM)
        self.lexema = lexema    # sequência de caracteres reconhecida
        self.linha = linha      # linha onde o átomo foi encontrado
        self.valor = valor      # valor numérico (apenas para NUM)

    def __repr__(self):
        if self.valor is not None:
            return f"Atomo({self.tipo}, '{self.lexema}', linha={self.linha}, valor={self.valor})"
        return f"Atomo({self.tipo}, '{self.lexema}', linha={self.linha})"


# ============================================================
# Analisador Léxico
# ============================================================

class AnalisadorLexico:
    """
    Realiza a análise léxica do código-fonte PascalLite.

    Responsável por:
    - Ignorar espaços em branco mantendo contagem de linhas
    - Reconhecer comentários (//, (* *), { })
    - Reconhecer palavras reservadas e identificadores
    - Reconhecer números inteiros
    - Reconhecer operadores e delimitadores
    """

    # Limite máximo de caracteres para identificadores
    MAX_IDENTIF = 20

    def __init__(self, codigo):
        """
        Inicializa o analisador léxico.

        Args:
            codigo: string com o código-fonte completo
        """
        self.codigo = codigo
        self.pos = 0                    # posição atual no código-fonte
        self.linha = 1                  # linha atual (contagem inicia em 1)
        self.tamanho = len(codigo)      # tamanho total do código

    def _char_atual(self):
        """Retorna o caractere na posição atual, ou None se fim do arquivo."""
        if self.pos < self.tamanho:
            return self.codigo[self.pos]
        return None

    def _avancar(self):
        """Avança para o próximo caractere, atualizando contagem de linha."""
        if self.pos < self.tamanho:
            if self.codigo[self.pos] == '\n':
                self.linha += 1
            self.pos += 1

    def _pular_espacos(self):
        """Ignora espaços em branco, tabulações e quebras de linha."""
        while self.pos < self.tamanho and self.codigo[self.pos] in (' ', '\t', '\n', '\r'):
            if self.codigo[self.pos] == '\n':
                self.linha += 1
            self.pos += 1

    def _reconhecer_comentario_linha(self):
        """
        Reconhece comentário de linha única: // ... \\n
        Retorna átomo COMENTARIO.
        """
        linha_inicio = self.linha
        self.pos += 2  # pula '//'
        inicio = self.pos
        while self.pos < self.tamanho and self.codigo[self.pos] != '\n':
            self.pos += 1
        lexema = '//' + self.codigo[inicio:self.pos]
        # não avança sobre o '\n' aqui; _pular_espacos cuidará dele
        return Atomo(COMENTARIO, lexema, linha_inicio)

    def _reconhecer_comentario_parenteses(self):
        """
        Reconhece comentário de bloco: (* ... *)
        Mantém contagem de linhas dentro do comentário.
        Retorna átomo COMENTARIO ou gera erro léxico se não fechado.
        """
        linha_inicio = self.linha
        inicio = self.pos
        self.pos += 2  # pula '(*'
        while self.pos < self.tamanho - 1:
            if self.codigo[self.pos] == '\n':
                self.linha += 1
            if self.codigo[self.pos] == '*' and self.codigo[self.pos + 1] == ')':
                self.pos += 2  # pula '*)'
                lexema = self.codigo[inicio:self.pos]
                return Atomo(COMENTARIO, lexema, linha_inicio)
            self.pos += 1
        # Verificação do último caractere
        if self.pos < self.tamanho:
            if self.codigo[self.pos] == '\n':
                self.linha += 1
            self.pos += 1
        # Comentário não fechado
        print(f"Erro léxico: comentário '(* *)' não fechado, iniciado na linha {linha_inicio}")
        sys.exit(1)

    def _reconhecer_comentario_chaves(self):
        """
        Reconhece comentário de bloco: { ... }
        Mantém contagem de linhas dentro do comentário.
        Retorna átomo COMENTARIO ou gera erro léxico se não fechado.
        """
        linha_inicio = self.linha
        inicio = self.pos
        self.pos += 1  # pula '{'
        while self.pos < self.tamanho:
            if self.codigo[self.pos] == '\n':
                self.linha += 1
            if self.codigo[self.pos] == '}':
                self.pos += 1  # pula '}'
                lexema = self.codigo[inicio:self.pos]
                return Atomo(COMENTARIO, lexema, linha_inicio)
            self.pos += 1
        # Comentário não fechado
        print(f"Erro léxico: comentário '{{ }}' não fechado, iniciado na linha {linha_inicio}")
        sys.exit(1)

    def _reconhecer_identificador_ou_reservada(self):
        """
        Reconhece identificador ou palavra reservada.

        Identificadores: começam com letra ou '_', seguidos de letras, dígitos ou '_'.
        Limitados a 20 caracteres. Se exceder, gera erro léxico.
        Palavras reservadas são reconhecidas pela mesma função.

        Returns:
            Atomo com tipo da palavra reservada ou IDENTIF.
        """
        linha_inicio = self.linha
        inicio = self.pos
        # Consome caracteres válidos para identificador
        while self.pos < self.tamanho and (
            self.codigo[self.pos].isalpha() or
            self.codigo[self.pos].isdigit() or
            self.codigo[self.pos] == '_'
        ):
            self.pos += 1
        lexema = self.codigo[inicio:self.pos]
        # Verifica limite de 20 caracteres
        if len(lexema) > self.MAX_IDENTIF:
            print(f"Erro léxico: identificador '{lexema}' excede {self.MAX_IDENTIF} "
                  f"caracteres na linha {linha_inicio}")
            sys.exit(1)
        # Verifica se é palavra reservada (comparação case-insensitive)
        tipo = PALAVRAS_RESERVADAS.get(lexema.lower(), IDENTIF)
        return Atomo(tipo, lexema, linha_inicio)

    def _reconhecer_numero(self):
        """
        Reconhece número inteiro (sequência de dígitos).

        Returns:
            Atomo do tipo NUM com o valor numérico.
        """
        linha_inicio = self.linha
        inicio = self.pos
        while self.pos < self.tamanho and self.codigo[self.pos].isdigit():
            self.pos += 1
        lexema = self.codigo[inicio:self.pos]
        return Atomo(NUM, lexema, linha_inicio, valor=int(lexema))

    def obter_atomo(self):
        """
        Função principal do analisador léxico.

        Reconhece e retorna o próximo átomo do código-fonte.
        Ignora espaços em branco e mantém a contagem de linhas.
        Comentários são retornados como átomos COMENTARIO para o
        analisador sintático reportar e descartar.

        Returns:
            Atomo reconhecido.
        """
        # Ignora espaços em branco
        self._pular_espacos()

        # Verifica fim do arquivo
        if self.pos >= self.tamanho:
            return Atomo(EOF_ATOM, "EOF", self.linha)

        char = self.codigo[self.pos]
        linha_atual = self.linha

        # --- Comentários ---
        # Comentário de linha: //
        if char == '/' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '/':
            return self._reconhecer_comentario_linha()
        # Comentário de bloco: (* *)
        if char == '(' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '*':
            return self._reconhecer_comentario_parenteses()
        # Comentário de bloco: { }
        if char == '{':
            return self._reconhecer_comentario_chaves()

        # --- Identificadores e palavras reservadas ---
        if char.isalpha() or char == '_':
            return self._reconhecer_identificador_ou_reservada()

        # --- Números inteiros ---
        if char.isdigit():
            return self._reconhecer_numero()

        # --- Operadores e delimitadores (dois caracteres) ---
        if char == ':' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '=':
            self.pos += 2
            return Atomo(ATRIB, ":=", linha_atual)
        if char == '<' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '=':
            self.pos += 2
            return Atomo(MENOR_IGUAL, "<=", linha_atual)
        if char == '<' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '>':
            self.pos += 2
            return Atomo(DIFERENTE, "<>", linha_atual)
        if char == '>' and self.pos + 1 < self.tamanho and self.codigo[self.pos + 1] == '=':
            self.pos += 2
            return Atomo(MAIOR_IGUAL, ">=", linha_atual)

        # --- Operadores e delimitadores (um caractere) ---
        tabela_simples = {
            ';': PONTO_VIRG,
            ',': VIRGULA,
            ':': DOIS_PONTOS,
            '.': PONTO,
            '(': ABRE_PAR,
            ')': FECHA_PAR,
            '+': MAIS,
            '-': MENOS,
            '*': VEZES,
            '/': BARRA,
            '<': MENOR,
            '>': MAIOR,
            '=': IGUAL,
        }
        if char in tabela_simples:
            self.pos += 1
            return Atomo(tabela_simples[char], char, linha_atual)

        # --- Caractere não reconhecido ---
        print(f"Erro léxico: caractere inválido '{char}' na linha {linha_atual}")
        sys.exit(1)


# ============================================================
# Analisador Sintático (Parser Descendente Recursivo)
# ============================================================

class AnalisadorSintatico:
    """
    Realiza a análise sintática do código PascalLite usando
    o método de análise descendente recursiva (recursive descent).

    Cada não-terminal da gramática EBNF corresponde a um método.
    A interação com o analisador léxico se dá pela função consome(),
    que chama obter_atomo() do léxico.
    """

    def __init__(self, lexico):
        """
        Inicializa o analisador sintático.

        Args:
            lexico: instância de AnalisadorLexico já inicializada.
        """
        self.lexico = lexico
        self.ultima_linha = 1  # linha do último átomo consumido
        # Obtém o primeiro átomo (lookahead), pulando comentários
        self.lookahead = self._proximo_atomo()

    def _proximo_atomo(self):
        """
        Obtém o próximo átomo do léxico, descartando comentários.

        Comentários são repassados pelo léxico e descartados aqui
        no analisador sintático, conforme especificação.

        Returns:
            Próximo átomo que não seja COMENTARIO.
        """
        atomo = self.lexico.obter_atomo()
        while atomo.tipo == COMENTARIO:
            atomo = self.lexico.obter_atomo()
        return atomo

    def _imprimir_atomo(self, atomo):
        """
        Imprime as informações do átomo consumido no formato especificado.

        Para átomos NUM, inclui também o valor numérico.
        """
        msg = f"Linha: {atomo.linha} - atomo: {atomo.tipo} lexema: {atomo.lexema}"
        if atomo.tipo == NUM:
            msg += f" valor: {atomo.valor}"
        print(msg)

    def consome(self, esperado):
        """
        Consome o átomo atual se ele corresponde ao tipo esperado.

        Se o lookahead tem o tipo esperado, imprime o átomo e avança
        para o próximo. Caso contrário, reporta erro sintático e encerra.

        Args:
            esperado: tipo de átomo esperado (ex: PROGRAM, IDENTIF)
        """
        if self.lookahead.tipo == esperado:
            self._imprimir_atomo(self.lookahead)
            self.ultima_linha = self.lookahead.linha
            self.lookahead = self._proximo_atomo()
        else:
            self._erro_sintatico(esperado)

    def _erro_sintatico(self, esperado):
        """
        Reporta erro sintático e encerra a execução do compilador.

        Args:
            esperado: tipo de átomo que era esperado.
        """
        print(f"Erro sintático: Esperado [{esperado}] "
              f"encontrado [{self.lookahead.tipo}] "
              f"na linha {self.lookahead.linha}")
        sys.exit(1)

    # --------------------------------------------------------
    # Regras gramaticais (cada método = um não-terminal)
    # --------------------------------------------------------

    def programa(self):
        """
        <programa> ::= program identificador [( <lista_identificadores> )] ; <bloco> .
        """
        self.consome(PROGRAM)
        self.consome(IDENTIF)
        # Parte opcional: ( <lista_identificadores> )
        if self.lookahead.tipo == ABRE_PAR:
            self.consome(ABRE_PAR)
            self.lista_identificadores()
            self.consome(FECHA_PAR)
        self.consome(PONTO_VIRG)
        self.bloco()
        self.consome(PONTO)
        # Análise concluída com sucesso
        print(f"{self.ultima_linha} linhas analisadas, programa sintaticamente correto.")

    def bloco(self):
        """
        <bloco> ::= [<declarações de variáveis>] <comando composto>
        """
        if self.lookahead.tipo == VAR:
            self.declaracoes_variaveis()
        self.comando_composto()

    def declaracoes_variaveis(self):
        """
        <declarações de variáveis> ::= var <declaração> { ; <declaração> } ;

        Após cada declaração, consome ';'. Se o próximo token é um
        identificador, há outra declaração; senão, o ';' era o terminador.
        """
        self.consome(VAR)
        self.declaracao()
        self.consome(PONTO_VIRG)
        # Enquanto houver mais declarações (próximo token é identificador)
        while self.lookahead.tipo == IDENTIF:
            self.declaracao()
            self.consome(PONTO_VIRG)

    def declaracao(self):
        """
        <declaração> ::= <lista de identificadores> : <tipo>
        """
        self.lista_identificadores()
        self.consome(DOIS_PONTOS)
        self.tipo()

    def lista_identificadores(self):
        """
        <lista de identificadores> ::= identificador { , identificador }
        """
        self.consome(IDENTIF)
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            self.consome(IDENTIF)

    def tipo(self):
        """
        <tipo> ::= integer | boolean
        """
        if self.lookahead.tipo == INTEGER:
            self.consome(INTEGER)
        elif self.lookahead.tipo == BOOLEAN:
            self.consome(BOOLEAN)
        else:
            self._erro_sintatico("INTEGER ou BOOLEAN")

    def comando_composto(self):
        """
        <comando composto> ::= begin <comando> { ; <comando> } end
        """
        self.consome(BEGIN)
        self.comando()
        while self.lookahead.tipo == PONTO_VIRG:
            self.consome(PONTO_VIRG)
            self.comando()
        self.consome(END)

    def comando(self):
        """
        <comando> ::= <atribuição> | <comando de entrada> | <comando de saída>
                     | <comando if> | <comando while> | <comando composto>

        A decisão é tomada pelo lookahead (análise LL(1)).
        """
        if self.lookahead.tipo == IDENTIF:
            self.atribuicao()
        elif self.lookahead.tipo == READ:
            self.comando_entrada()
        elif self.lookahead.tipo == WRITE:
            self.comando_saida()
        elif self.lookahead.tipo == IF:
            self.comando_if()
        elif self.lookahead.tipo == WHILE:
            self.comando_while()
        elif self.lookahead.tipo == BEGIN:
            self.comando_composto()
        else:
            self._erro_sintatico("IDENTIF, READ, WRITE, IF, WHILE ou BEGIN")

    def atribuicao(self):
        """
        <atribuição> ::= identificador := <expressão>
        """
        self.consome(IDENTIF)
        self.consome(ATRIB)
        self.expressao()

    def comando_entrada(self):
        """
        <comando de entrada> ::= read ( <lista de identificadores> )
        """
        self.consome(READ)
        self.consome(ABRE_PAR)
        self.lista_identificadores()
        self.consome(FECHA_PAR)

    def comando_saida(self):
        """
        <comando de saída> ::= write ( <expressão> { , <expressão> } )
        """
        self.consome(WRITE)
        self.consome(ABRE_PAR)
        self.expressao()
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            self.expressao()
        self.consome(FECHA_PAR)

    def comando_if(self):
        """
        <comando if> ::= if <expressão> then <comando> [else <comando>]
        """
        self.consome(IF)
        self.expressao()
        self.consome(THEN)
        self.comando()
        # Parte opcional: else <comando>
        if self.lookahead.tipo == ELSE:
            self.consome(ELSE)
            self.comando()

    def comando_while(self):
        """
        <comando while> ::= while <expressão> do <comando>
        """
        self.consome(WHILE)
        self.expressao()
        self.consome(DO)
        self.comando()

    def expressao(self):
        """
        <expressão> ::= <expressão simples> [<operador relacional> <expressão simples>]
        """
        self.expressao_simples()
        # Operadores relacionais: < <= = <> > >=
        if self.lookahead.tipo in (MENOR, MENOR_IGUAL, IGUAL, DIFERENTE, MAIOR, MAIOR_IGUAL):
            self.consome(self.lookahead.tipo)
            self.expressao_simples()

    def expressao_simples(self):
        """
        <expressão simples> ::= [+ | -] <termo> { <operador de adição> <termo> }
        """
        # Sinal unário opcional
        if self.lookahead.tipo in (MAIS, MENOS):
            self.consome(self.lookahead.tipo)
        self.termo()
        # Operadores de adição: + - or
        while self.lookahead.tipo in (MAIS, MENOS, OR):
            self.consome(self.lookahead.tipo)
            self.termo()

    def termo(self):
        """
        <termo> ::= <fator> { <operador de multiplicação> <fator> }
        """
        self.fator()
        # Operadores de multiplicação: * / div mod and
        while self.lookahead.tipo in (VEZES, BARRA, DIV, MOD, AND):
            self.consome(self.lookahead.tipo)
            self.fator()

    def fator(self):
        """
        <fator> ::= identificador | numero | ( <expressão> ) | true | false | not <fator>
        """
        if self.lookahead.tipo == IDENTIF:
            self.consome(IDENTIF)
        elif self.lookahead.tipo == NUM:
            self.consome(NUM)
        elif self.lookahead.tipo == ABRE_PAR:
            self.consome(ABRE_PAR)
            self.expressao()
            self.consome(FECHA_PAR)
        elif self.lookahead.tipo == TRUE:
            self.consome(TRUE)
        elif self.lookahead.tipo == FALSE:
            self.consome(FALSE)
        elif self.lookahead.tipo == NOT:
            self.consome(NOT)
            self.fator()
        else:
            self._erro_sintatico("IDENTIF, NUM, ABRE_PAR, TRUE, FALSE ou NOT")


# ============================================================
# Programa Principal
# ============================================================

def main():
    """Ponto de entrada do compilador PascalLite."""
    # Verifica argumentos de linha de comando
    if len(sys.argv) < 2:
        print("Uso: python compilador.py <arquivo_fonte>")
        print("Exemplo: python compilador.py programa.pas")
        sys.exit(1)

    nome_arquivo = sys.argv[1]

    # Lê o arquivo-fonte
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            codigo = arquivo.read()
    except FileNotFoundError:
        print(f"Erro: arquivo '{nome_arquivo}' não encontrado.")
        sys.exit(1)
    except IOError as e:
        print(f"Erro ao ler arquivo '{nome_arquivo}': {e}")
        sys.exit(1)

    # Inicializa o analisador léxico
    lexico = AnalisadorLexico(codigo)

    # Inicializa e executa o analisador sintático
    sintatico = AnalisadorSintatico(lexico)
    sintatico.programa()


if __name__ == '__main__':
    main()
