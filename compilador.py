"""
Compilador PascalLite - Fase 2: Análise Semântica e Geração de Código Intermediário (MEPA)

Implementa as fases de análise léxica, sintática, semântica e geração de código
intermediário para a linguagem PascalLite, uma versão simplificada do Pascal
com tipo integer, comandos if e while.

A análise semântica verifica:
  - Declaração duplicada de identificadores (erro semântico)
  - Uso de identificadores não declarados (erro semântico)

A geração de código intermediário produz instruções da MEPA (Máquina de Execução
para PascalLite com Armazenamento), conforme descrito no livro de Tomasz Kowaltowski.

Integrante:
    - Matheus Fernandes Martins Batista - RA: 2202435

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
# Tabela de Símbolos (mini-tabela para variáveis)
# ============================================================

class TabelaSimbolos:
    """
    Tabela de símbolos simplificada para o compilador PascalLite.

    Armazena os identificadores declarados na seção 'var' com seus
    respectivos endereços (ordem de declaração) e tipos. Utilizada
    durante a análise semântica para:
      - Verificar declarações duplicadas
      - Verificar se variáveis usadas foram declaradas
      - Obter o endereço de memória de uma variável para geração de código
    """

    def __init__(self):
        """Inicializa a tabela de símbolos vazia."""
        self.simbolos = {}      # dicionário: identificador -> {endereco, tipo}
        self.proximo_endereco = 0  # próximo endereço disponível

    def inserir(self, identificador, tipo, linha):
        """
        Insere um identificador na tabela de símbolos.

        Verifica se o identificador já foi declarado; se sim, gera
        erro semântico e encerra o compilador.

        Args:
            identificador: nome da variável (lexema)
            tipo: tipo da variável (ex: 'integer')
            linha: linha da declaração (para mensagem de erro)
        """
        if identificador in self.simbolos:
            print(f"Erro semântico: identificador '{identificador}' já declarado "
                  f"(linha {linha})")
            sys.exit(1)
        self.simbolos[identificador] = {
            'endereco': self.proximo_endereco,
            'tipo': tipo
        }
        self.proximo_endereco += 1

    def buscar(self, identificador, linha):
        """
        Busca um identificador na tabela de símbolos e retorna seu endereço.

        Se o identificador não for encontrado, gera erro semântico e encerra.

        Args:
            identificador: nome da variável a buscar
            linha: linha onde a variável é referenciada (para mensagem de erro)

        Returns:
            Endereço (int) da variável na memória.
        """
        if identificador not in self.simbolos:
            print(f"Erro semântico: identificador '{identificador}' não declarado "
                  f"(linha {linha})")
            sys.exit(1)
        return self.simbolos[identificador]['endereco']

    def total_variaveis(self):
        """Retorna o número total de variáveis declaradas."""
        return self.proximo_endereco


# ============================================================
# Gerador de Rótulos (para instruções de desvio da MEPA)
# ============================================================

class GeradorRotulos:
    """
    Gera rótulos consecutivos (L1, L2, L3, ...) para as instruções
    de desvio condicional e incondicional da MEPA.
    """

    def __init__(self):
        """Inicializa o contador de rótulos."""
        self.contador = 0

    def proximo_rotulo(self):
        """
        Retorna o próximo rótulo consecutivo.

        Returns:
            String no formato 'L1', 'L2', etc.
        """
        self.contador += 1
        return f"L{self.contador}"


# ============================================================
# Analisador Sintático com Análise Semântica e Geração de Código
# ============================================================

class AnalisadorSintatico:
    """
    Realiza a análise sintática, semântica e geração de código MEPA
    para o compilador PascalLite, usando o método de análise
    descendente recursiva (recursive descent).

    Cada não-terminal da gramática EBNF corresponde a um método.
    A interação com o analisador léxico se dá pela função consome(),
    que chama obter_atomo() do léxico.

    Fase 2:
    - Mantém uma tabela de símbolos para verificação semântica
    - Gera instruções intermediárias da MEPA embutidas nas
      funções de análise sintática (ações semânticas)
    """

    def __init__(self, lexico):
        """
        Inicializa o analisador sintático.

        Args:
            lexico: instância de AnalisadorLexico já inicializada.
        """
        self.lexico = lexico
        self.ultima_linha = 1           # linha do último átomo consumido
        self.tabela = TabelaSimbolos()  # tabela de símbolos para análise semântica
        self.rotulos = GeradorRotulos() # gerador de rótulos para desvios MEPA
        self.codigo_mepa = []           # lista de instruções MEPA geradas
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

    def _emitir(self, instrucao):
        """
        Emite uma instrução MEPA, adicionando-a à lista de código gerado.

        Args:
            instrucao: string com a instrução MEPA (ex: 'INPP', 'CRCT 1')
        """
        self.codigo_mepa.append(instrucao)

    def consome(self, esperado):
        """
        Consome o átomo atual se ele corresponde ao tipo esperado.

        Se o lookahead tem o tipo esperado, avança para o próximo.
        Caso contrário, reporta erro sintático e encerra.

        Args:
            esperado: tipo de átomo esperado (ex: PROGRAM, IDENTIF)
        """
        if self.lookahead.tipo == esperado:
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
    # Regras gramaticais com ações semânticas para geração MEPA
    # --------------------------------------------------------

    def programa(self):
        """
        <programa> ::= program identificador ; <bloco> .

        Ações semânticas:
          - Emite INPP (inicializa programa) no início
          - Emite PARA (parada) no final
        """
        self.consome(PROGRAM)
        self.consome(IDENTIF)
        # Parte opcional: ( <lista_identificadores> ) — ignorada na fase 2
        if self.lookahead.tipo == ABRE_PAR:
            self.consome(ABRE_PAR)
            self._lista_identificadores_programa()
            self.consome(FECHA_PAR)
        self.consome(PONTO_VIRG)
        # Emite instrução de início de programa MEPA
        self._emitir("INPP")
        self.bloco()
        # Emite instrução de parada MEPA
        self._emitir("PARA")
        self.consome(PONTO)

    def _lista_identificadores_programa(self):
        """
        Lista de identificadores do cabeçalho do programa (apenas sintática,
        sem inserção na tabela de símbolos, pois são parâmetros do programa).
        """
        self.consome(IDENTIF)
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            self.consome(IDENTIF)

    def bloco(self):
        """
        <bloco> ::= [<declarações de variáveis>] <comando composto>

        Ações semânticas:
          - Após declarações, emite AMEM n (aloca memória para n variáveis)
        """
        if self.lookahead.tipo == VAR:
            self.declaracoes_variaveis()
        # Emite alocação de memória para as variáveis declaradas
        num_vars = self.tabela.total_variaveis()
        if num_vars > 0:
            self._emitir(f"AMEM {num_vars}")
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

        Ações semânticas:
          - Coleta os identificadores da lista
          - Após reconhecer o tipo, insere cada identificador na tabela
            de símbolos com o tipo correspondente
        """
        # Coleta os identificadores antes de consumir (para associar ao tipo)
        ids_declarados = []
        ids_declarados.append((self.lookahead.lexema, self.lookahead.linha))
        self.consome(IDENTIF)
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            ids_declarados.append((self.lookahead.lexema, self.lookahead.linha))
            self.consome(IDENTIF)
        self.consome(DOIS_PONTOS)
        # Reconhece o tipo
        tipo_var = self.lookahead.lexema.lower()
        self.tipo()
        # Insere cada identificador na tabela de símbolos
        for nome, linha in ids_declarados:
            self.tabela.inserir(nome, tipo_var, linha)

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

        Nota: permite comando vazio antes de 'end' (';' antes de 'end'
        é válido em Pascal e representa um comando vazio).
        """
        self.consome(BEGIN)
        self.comando()
        while self.lookahead.tipo == PONTO_VIRG:
            self.consome(PONTO_VIRG)
            # Se o próximo token é END, temos um comando vazio (válido em Pascal)
            if self.lookahead.tipo == END:
                break
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

        Ações semânticas:
          - Verifica se o identificador está na tabela de símbolos
          - Após avaliar a expressão, emite ARMZ endereco
        """
        # Guarda o lexema e linha antes de consumir
        nome = self.lookahead.lexema
        linha = self.lookahead.linha
        # Verifica se a variável foi declarada e obtém endereço
        endereco = self.tabela.buscar(nome, linha)
        self.consome(IDENTIF)
        self.consome(ATRIB)
        self.expressao()
        # Emite instrução de armazenamento na posição da variável
        self._emitir(f"ARMZ {endereco}")

    def comando_entrada(self):
        """
        <comando de entrada> ::= read ( <lista de identificadores> )

        Ações semânticas:
          - Para cada identificador lido, emite LEIT seguido de ARMZ endereco
        """
        self.consome(READ)
        self.consome(ABRE_PAR)
        # Primeiro identificador
        nome = self.lookahead.lexema
        linha = self.lookahead.linha
        endereco = self.tabela.buscar(nome, linha)
        self.consome(IDENTIF)
        self._emitir("LEIT")
        self._emitir(f"ARMZ {endereco}")
        # Identificadores adicionais separados por vírgula
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            nome = self.lookahead.lexema
            linha = self.lookahead.linha
            endereco = self.tabela.buscar(nome, linha)
            self.consome(IDENTIF)
            self._emitir("LEIT")
            self._emitir(f"ARMZ {endereco}")
        self.consome(FECHA_PAR)

    def comando_saida(self):
        """
        <comando de saída> ::= write ( <expressão> { , <expressão> } )

        Ações semânticas:
          - Após cada expressão, emite IMPR
        """
        self.consome(WRITE)
        self.consome(ABRE_PAR)
        self.expressao()
        self._emitir("IMPR")
        while self.lookahead.tipo == VIRGULA:
            self.consome(VIRGULA)
            self.expressao()
            self._emitir("IMPR")
        self.consome(FECHA_PAR)

    def comando_if(self):
        """
        <comando if> ::= if <expressão> then <comando> [else <comando>]

        Ações semânticas:
          - Após a expressão, emite DSVF L1 (desvia se falso)
          - Se há else: antes do else emite DSVS L2, coloca L1: NADA,
            executa o else, depois coloca L2: NADA
          - Se não há else: após o then-comando coloca L1: NADA
        """
        self.consome(IF)
        self.expressao()
        rotulo_falso = self.rotulos.proximo_rotulo()  # L1: pula se falso
        self._emitir(f"DSVF {rotulo_falso}")
        self.consome(THEN)
        self.comando()
        # Parte opcional: else <comando>
        if self.lookahead.tipo == ELSE:
            rotulo_fim = self.rotulos.proximo_rotulo()  # L2: pula o else
            self._emitir(f"DSVS {rotulo_fim}")
            self._emitir(f"{rotulo_falso}: NADA")
            self.consome(ELSE)
            self.comando()
            self._emitir(f"{rotulo_fim}: NADA")
        else:
            self._emitir(f"{rotulo_falso}: NADA")

    def comando_while(self):
        """
        <comando while> ::= while <expressão> do <comando>

        Ações semânticas:
          - Emite L1: NADA antes da expressão
          - Após a expressão, emite DSVF L2
          - Após o comando, emite DSVS L1 (volta ao início do loop)
          - Emite L2: NADA (saída do loop)
        """
        rotulo_inicio = self.rotulos.proximo_rotulo()  # L1: início do loop
        rotulo_fim = self.rotulos.proximo_rotulo()     # L2: saída do loop
        self.consome(WHILE)
        self._emitir(f"{rotulo_inicio}: NADA")
        self.expressao()
        self._emitir(f"DSVF {rotulo_fim}")
        self.consome(DO)
        self.comando()
        self._emitir(f"DSVS {rotulo_inicio}")
        self._emitir(f"{rotulo_fim}: NADA")

    def expressao(self):
        """
        <expressão> ::= <expressão simples> [<operador relacional> <expressão simples>]

        Ações semânticas:
          - Após o operador relacional e a segunda expressão simples,
            emite a instrução de comparação correspondente
        """
        self.expressao_simples()
        # Operadores relacionais: < <= = <> > >=
        if self.lookahead.tipo in (MENOR, MENOR_IGUAL, IGUAL, DIFERENTE, MAIOR, MAIOR_IGUAL):
            operador = self.lookahead.tipo
            self.consome(operador)
            self.expressao_simples()
            # Mapeamento de operadores relacionais para instruções MEPA
            mapa_relacional = {
                MENOR:       "CMME",    # compara menor
                MENOR_IGUAL: "CMEG",    # compara menor ou igual
                IGUAL:       "CMIG",    # compara igual
                DIFERENTE:   "CMDG",    # compara diferente
                MAIOR:       "CMMA",    # compara maior
                MAIOR_IGUAL: "CMAG",    # compara maior ou igual
            }
            self._emitir(mapa_relacional[operador])

    def expressao_simples(self):
        """
        <expressão simples> ::= [+ | -] <termo> { <operador de adição> <termo> }

        Ações semânticas:
          - Se há sinal '-' unário, emite INVR após o termo
          - Para cada operador de adição, emite a instrução correspondente
        """
        # Sinal unário opcional
        sinal_negativo = False
        if self.lookahead.tipo in (MAIS, MENOS):
            if self.lookahead.tipo == MENOS:
                sinal_negativo = True
            self.consome(self.lookahead.tipo)
        self.termo()
        # Se havia sinal unário negativo, inverte o valor no topo da pilha
        if sinal_negativo:
            self._emitir("INVR")
        # Operadores de adição: + - or
        while self.lookahead.tipo in (MAIS, MENOS, OR):
            operador = self.lookahead.tipo
            self.consome(operador)
            self.termo()
            # Mapeamento de operadores de adição para instruções MEPA
            if operador == MAIS:
                self._emitir("SOMA")
            elif operador == MENOS:
                self._emitir("SUBT")
            elif operador == OR:
                self._emitir("DISJ")    # disjunção lógica

    def termo(self):
        """
        <termo> ::= <fator> { <operador de multiplicação> <fator> }

        Ações semânticas:
          - Para cada operador de multiplicação, emite a instrução MEPA
        """
        self.fator()
        # Operadores de multiplicação: * / div mod and
        while self.lookahead.tipo in (VEZES, BARRA, DIV, MOD, AND):
            operador = self.lookahead.tipo
            self.consome(operador)
            self.fator()
            # Mapeamento de operadores de multiplicação para instruções MEPA
            if operador == VEZES:
                self._emitir("MULT")
            elif operador == BARRA or operador == DIV:
                self._emitir("DIVI")
            elif operador == MOD:
                self._emitir("MODI")
            elif operador == AND:
                self._emitir("CONJ")    # conjunção lógica

    def fator(self):
        """
        <fator> ::= identificador | numero | ( <expressão> )

        Produção simplificada para a Fase 2 (somente expressões inteiras):
        - Remove true, false e not da gramática original.

        Ações semânticas:
          - identificador: emite CRVL endereco (carrega valor da variável)
          - numero: emite CRCT valor (carrega constante)
          - ( <expressão> ): avalia a expressão entre parênteses
        """
        if self.lookahead.tipo == IDENTIF:
            # Verifica se a variável foi declarada e obtém endereço
            endereco = self.tabela.buscar(self.lookahead.lexema, self.lookahead.linha)
            self._emitir(f"CRVL {endereco}")
            self.consome(IDENTIF)
        elif self.lookahead.tipo == NUM:
            # Carrega constante numérica
            self._emitir(f"CRCT {self.lookahead.lexema}")
            self.consome(NUM)
        elif self.lookahead.tipo == ABRE_PAR:
            self.consome(ABRE_PAR)
            self.expressao()
            self.consome(FECHA_PAR)
        else:
            self._erro_sintatico("IDENTIF, NUM ou ABRE_PAR")


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

    # Inicializa e executa o analisador sintático (com semântico e geração de código)
    sintatico = AnalisadorSintatico(lexico)
    sintatico.programa()

    # Imprime o código MEPA gerado (uma instrução por linha, separadas por vírgula)
    print(", ".join(sintatico.codigo_mepa))


if __name__ == '__main__':
    main()
