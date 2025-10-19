import random
from typing import List, Tuple, Dict, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

CROSSWORD_TITLE = 'CRUCIVERBONE STRAULLICO'
INPUT_FILE = 'input.txt'
INPUT_FILE_2 = 'input2.txt'

class Crossword:
    def __init__(self, width=40, height=25):
        self.width = width
        self.height = height
        self.grid = [[' ' for _ in range(width)] for _ in range(height)]
        self.words = []  # (word, row, col, direction, number)
        self.clues = []  # (number, clue, direction)
        self.word_count = 0
        
    def parse_input(self, text: str) -> List[Tuple[str, str]]:
        """Parsa l'input nel formato 'Risposta - Definizione'"""
        lines = text.strip().split('\n')
        result = []
        for line in lines:
            if ' - ' in line:
                answer, clue = line.split(' - ', 1)
                answer = answer.strip().upper().replace(' ', '')
                clue = clue.strip()
                result.append((answer, clue))
        return result
    
    def can_place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        """Verifica se una parola può essere posizionata"""
        if direction == 'H':  # Orizzontale
            if col + len(word) > self.width:
                return False
            # Controlla spazio prima e dopo
            if col > 0 and self.grid[row][col-1] != ' ':
                return False
            if col + len(word) < self.width and self.grid[row][col+len(word)] != ' ':
                return False
            # Controlla ogni lettera
            for i, char in enumerate(word):
                c = col + i
                if self.grid[row][c] not in (' ', char):
                    return False
                # Controlla celle sopra e sotto (tranne agli incroci)
                if self.grid[row][c] == ' ':
                    if row > 0 and self.grid[row-1][c] != ' ':
                        return False
                    if row < self.height-1 and self.grid[row+1][c] != ' ':
                        return False
        else:  # Verticale
            if row + len(word) > self.height:
                return False
            if row > 0 and self.grid[row-1][col] != ' ':
                return False
            if row + len(word) < self.height and self.grid[row+len(word)][col] != ' ':
                return False
            for i, char in enumerate(word):
                r = row + i
                if self.grid[r][col] not in (' ', char):
                    return False
                if self.grid[r][col] == ' ':
                    if col > 0 and self.grid[r][col-1] != ' ':
                        return False
                    if col < self.width-1 and self.grid[r][col+1] != ' ':
                        return False
        return True
    
    def place_word(self, word: str, row: int, col: int, direction: str, clue: str):
        """Posiziona una parola nella griglia"""
        self.word_count += 1
        if direction == 'H':
            for i, char in enumerate(word):
                self.grid[row][col+i] = char
        else:
            for i, char in enumerate(word):
                self.grid[row+i][col] = char
        
        self.words.append((word, row, col, direction, self.word_count))
        self.clues.append((self.word_count, clue, direction))
    
    def find_intersections(self, word: str, placed_words: List) -> List[Tuple]:
        """Trova possibili intersezioni con parole già posizionate"""
        intersections = []
        for placed_word, p_row, p_col, p_dir, _ in placed_words:
            for i, char in enumerate(word):
                for j, p_char in enumerate(placed_word):
                    if char == p_char:
                        if p_dir == 'H':  # parola esistente orizzontale, nuova verticale
                            new_row = p_row - i
                            new_col = p_col + j
                            intersections.append((new_row, new_col, 'V'))
                        else:  # parola esistente verticale, nuova orizzontale
                            new_row = p_row + j
                            new_col = p_col - i
                            intersections.append((new_row, new_col, 'H'))
        return intersections
    
    def generate(self, input_text: str):
        """Genera il cruciverba"""
        entries = self.parse_input(input_text)
        if not entries:
            return
        
        # Ordina per lunghezza (parole più lunghe prima)
        entries.sort(key=lambda x: len(x[0]), reverse=True)
        
        # Posiziona la prima parola al centro
        word, clue = entries[0]
        start_row = self.height // 2
        start_col = (self.width - len(word)) // 2
        self.place_word(word, start_row, start_col, 'H', clue)
        
        # Posiziona le altre parole
        for word, clue in entries[1:]:
            placed = False
            
            # Prova intersezioni con parole esistenti
            intersections = self.find_intersections(word, self.words)
            random.shuffle(intersections)
            
            for row, col, direction in intersections:
                if 0 <= row < self.height and 0 <= col < self.width:
                    if self.can_place_word(word, row, col, direction):
                        self.place_word(word, row, col, direction, clue)
                        placed = True
                        break
            
            # Se non trovato incrocio, prova posizionamenti casuali
            if not placed:
                attempts = 100
                for _ in range(attempts):
                    direction = random.choice(['H', 'V'])
                    if direction == 'H':
                        row = random.randint(0, self.height-1)
                        col = random.randint(0, max(0, self.width-len(word)))
                    else:
                        row = random.randint(0, max(0, self.height-len(word)))
                        col = random.randint(0, self.width-1)
                    
                    if self.can_place_word(word, row, col, direction):
                        self.place_word(word, row, col, direction, clue)
                        break
        
        # Rinumera le parole in ordine di lettura (riga per riga, sinistra a destra)
        self._renumber_words()
    
    def _renumber_words(self):
        """Rinumera le parole in ordine di lettura, condividendo numeri per celle comuni"""
        # Ordina per riga, poi per colonna
        sorted_words = sorted(self.words, key=lambda w: (w[1], w[2]))
        
        # Mappa (row, col) -> numero assegnato
        cell_number_map = {}
        current_number = 1
        
        # Ricrea le liste con nuova numerazione
        new_words = []
        new_clues = []
        
        for (word, row, col, direction, old_num) in sorted_words:
            cell_key = (row, col)
            
            # Se questa cella non ha ancora un numero, assegnane uno nuovo
            if cell_key not in cell_number_map:
                cell_number_map[cell_key] = current_number
                current_number += 1
            
            # Usa il numero della cella
            new_num = cell_number_map[cell_key]
            new_words.append((word, row, col, direction, new_num))
            
            # Trova la definizione corrispondente
            for num, clue, dir in self.clues:
                if num == old_num:
                    new_clues.append((new_num, clue, direction))
                    break
        
        self.words = new_words
        self.clues = new_clues
        self.word_count = len(self.words)
    
    def display(self):
        """Visualizza il cruciverba"""
        # Crea griglia con numeri
        display_grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        number_positions = {}
        
        for word, row, col, direction, number in self.words:
            display_grid[row][col] = str(number) if display_grid[row][col] == ' ' else display_grid[row][col]
            number_positions[(row, col)] = number
            
            if direction == 'H':
                for i in range(len(word)):
                    if display_grid[row][col+i] == ' ':
                        display_grid[row][col+i] = '.'
            else:
                for i in range(len(word)):
                    if display_grid[row+i][col] == ' ':
                        display_grid[row+i][col] = '.'
        
        # Stampa la griglia
        print("CRUCIVERBONE STRAULLICO:")
        print("=" * (self.width * 2 + 1))
        for row in display_grid:
            print('|' + '|'.join(cell if cell != ' ' else ' ' for cell in row) + '|')
        print("=" * (self.width * 2 + 1))
        
        # Stampa le definizioni
        print("\nORIZZONTALI:")
        for number, clue, direction in sorted(self.clues):
            if direction == 'H':
                print(f"{number}. {clue}")
        
        print("\nVERTICALI:")
        for number, clue, direction in sorted(self.clues):
            if direction == 'V':
                print(f"{number}. {clue}")
    
    def save_pdf(self, filename='crossword.pdf'):
        """Salva il cruciverba come PDF con 3 pagine: puzzle vuoto, soluzione, definizioni"""
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(filename, pagesize=landscape(A4))
        
        # Trova i bordi del cruciverba
        min_row, max_row = self.height, 0
        min_col, max_col = self.width, 0
        
        for word, row, col, direction, _ in self.words:
            min_row = min(min_row, row)
            max_row = max(max_row, row + (len(word) - 1 if direction == 'V' else 0))
            min_col = min(min_col, col)
            max_col = max(max_col, col + (len(word) - 1 if direction == 'H' else 0))
        
        # Dimensioni della griglia
        grid_rows = max_row - min_row + 1
        grid_cols = max_col - min_col + 1
        
        # Calcola dimensione celle per massimizzare l'uso dello spazio (senza titolo)
        margin = 15 * mm
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin
        
        # Usa tutto lo spazio disponibile
        cell_size = min(available_width / grid_cols, available_height / grid_rows)
        
        # Posizione griglia centrata
        grid_width = grid_cols * cell_size
        grid_height = grid_rows * cell_size
        x_offset = (page_width - grid_width) / 2
        y_offset = (page_height - grid_height) / 2
        
        # Crea un set di celle già disegnate e mappa di numeri per posizione
        drawn_cells = set()
        cell_numbers = {}  # (row, col) -> numero (unico per cella)
        
        # Raccogli il numero per ogni posizione (ora è unico grazie a _renumber_words)
        for word, row, col, direction, number in self.words:
            key = (row, col)
            if key not in cell_numbers:
                cell_numbers[key] = number
        
        # PAGINA 1: PUZZLE VUOTO (senza titolo)
        # Disegna la griglia vuota
        for word, row, col, direction, number in self.words:
            adj_row = row - min_row
            adj_col = col - min_col
            
            if direction == 'H':
                for i in range(len(word)):
                    cell_key = (adj_row, adj_col + i)
                    if cell_key not in drawn_cells:
                        x = x_offset + (adj_col + i) * cell_size
                        y = y_offset + (grid_rows - adj_row - 1) * cell_size
                        c.rect(x, y, cell_size, cell_size, fill=0)
                        drawn_cells.add(cell_key)
            else:
                for i in range(len(word)):
                    cell_key = (adj_row + i, adj_col)
                    if cell_key not in drawn_cells:
                        x = x_offset + adj_col * cell_size
                        y = y_offset + (grid_rows - adj_row - i - 1) * cell_size
                        c.rect(x, y, cell_size, cell_size, fill=0)
                        drawn_cells.add(cell_key)
        
        # Disegna i numeri (una sola volta per cella)
        number_font_size = max(7, min(12, int(cell_size / mm * 0.9)))
        c.setFont("Helvetica", number_font_size)
        drawn_numbers = set()
        
        for (row, col), number in cell_numbers.items():
            adj_row = row - min_row
            adj_col = col - min_col
            
            if (adj_row, adj_col) not in drawn_numbers:
                x = x_offset + adj_col * cell_size + 2
                y = y_offset + (grid_rows - adj_row - 1) * cell_size + cell_size - max(7, cell_size / 4)
                c.drawString(x, y, str(number))
                drawn_numbers.add((adj_row, adj_col))
        
        c.showPage()
        
        # PAGINA 2: SOLUZIONE (senza titolo)
        # Reset celle disegnate
        drawn_cells = set()
        
        # Disegna la griglia con le lettere
        letter_font_size = max(12, min(24, int(cell_size / mm * 1.3)))
        
        for word, row, col, direction, number in self.words:
            adj_row = row - min_row
            adj_col = col - min_col
            
            if direction == 'H':
                for i, letter in enumerate(word):
                    cell_key = (adj_row, adj_col + i)
                    if cell_key not in drawn_cells:
                        x = x_offset + (adj_col + i) * cell_size
                        y = y_offset + (grid_rows - adj_row - 1) * cell_size
                        c.rect(x, y, cell_size, cell_size, fill=0)
                        
                        # Disegna la lettera centrata
                        c.setFont("Helvetica-Bold", letter_font_size)
                        letter_x = x + cell_size / 2
                        letter_y = y + cell_size / 2 - letter_font_size / 3
                        c.drawCentredString(letter_x, letter_y, letter)
                        drawn_cells.add(cell_key)
            else:
                for i, letter in enumerate(word):
                    cell_key = (adj_row + i, adj_col)
                    if cell_key not in drawn_cells:
                        x = x_offset + adj_col * cell_size
                        y = y_offset + (grid_rows - adj_row - i - 1) * cell_size
                        c.rect(x, y, cell_size, cell_size, fill=0)
                        
                        c.setFont("Helvetica-Bold", letter_font_size)
                        letter_x = x + cell_size / 2
                        letter_y = y + cell_size / 2 - letter_font_size / 3
                        c.drawCentredString(letter_x, letter_y, letter)
                        drawn_cells.add(cell_key)
        
        # Disegna i numeri
        number_font_size = max(7, min(12, int(cell_size / mm * 0.9)))
        c.setFont("Helvetica", number_font_size)
        drawn_numbers = set()
        
        for (row, col), number in cell_numbers.items():
            adj_row = row - min_row
            adj_col = col - min_col
            
            if (adj_row, adj_col) not in drawn_numbers:
                x = x_offset + adj_col * cell_size + 2
                y = y_offset + (grid_rows - adj_row - 1) * cell_size + cell_size - max(7, cell_size / 4)
                c.drawString(x, y, str(number))
                drawn_numbers.add((adj_row, adj_col))
        
        c.showPage()
        
        # PAGINA 3: DEFINIZIONI
      #   c.setFont("Helvetica-Bold", 26)
      #   c.drawCentredString(page_width / 2, page_height - 15 * mm, "DEFINIZIONI")
        
        def_y = page_height - 30 * mm
        line_height = 22
        col1_x = margin
        col2_x = page_width / 2 + 10 * mm
        
        # ORIZZONTALI (colonna sinistra) - ordinati per numero
        c.setFont("Helvetica-Bold", 18)
        c.drawString(col1_x, def_y, "ORIZZONTALI:")
        def_y -= line_height + 5
        
        c.setFont("Helvetica", 16)
        max_width = page_width / 2 - margin - 10 * mm
        
        # Filtra e ordina solo orizzontali
        h_clues = [(num, clue) for num, clue, direction in self.clues if direction == 'H']
        h_clues.sort(key=lambda x: x[0])
        
        for number, clue in h_clues:
            # Dividi clue se troppo lunga
            if c.stringWidth(f"{number}. {clue}", "Helvetica", 16) > max_width:
                words = clue.split()
                lines = []
                current_line = f"{number}. "
                for word in words:
                    test_line = current_line + word + " "
                    if c.stringWidth(test_line, "Helvetica", 16) > max_width:
                        lines.append(current_line.strip())
                        current_line = "     " + word + " "
                    else:
                        current_line = test_line
                lines.append(current_line.strip())
                
                for line in lines:
                    c.drawString(col1_x, def_y, line)
                    def_y -= line_height
            else:
                c.drawString(col1_x, def_y, f"{number}. {clue}")
                def_y -= line_height
        
        # VERTICALI (colonna destra) - ordinati per numero
        def_y = page_height - 30 * mm
        c.setFont("Helvetica-Bold", 18)
        c.drawString(col2_x, def_y, "VERTICALI:")
        def_y -= line_height + 5
        
        c.setFont("Helvetica", 16)
        
        # Filtra e ordina solo verticali
        v_clues = [(num, clue) for num, clue, direction in self.clues if direction == 'V']
        v_clues.sort(key=lambda x: x[0])
        
        for number, clue in v_clues:
            if c.stringWidth(f"{number}. {clue}", "Helvetica", 16) > max_width:
                words = clue.split()
                lines = []
                current_line = f"{number}. "
                for word in words:
                    test_line = current_line + word + " "
                    if c.stringWidth(test_line, "Helvetica", 16) > max_width:
                        lines.append(current_line.strip())
                        current_line = "     " + word + " "
                    else:
                        current_line = test_line
                lines.append(current_line.strip())
                
                for line in lines:
                    c.drawString(col2_x, def_y, line)
                    def_y -= line_height
            else:
                c.drawString(col2_x, def_y, f"{number}. {clue}")
                def_y -= line_height
        
        c.save()
        print(f"\nPDF salvato come '{filename}' (3 pagine: puzzle, soluzione, definizioni)")


if __name__ == "__main__":
    with open(INPUT_FILE_2, 'r', encoding='utf-8') as f:
        input_text = f.read()
    
    crossword = Crossword(width=40, height=25)
    crossword.generate(input_text)
    crossword.display()
    crossword.save_pdf('crossword_big.pdf')
