import sys
import os
import re
from PyPDF2 import PdfReader

def clean_line(line):
    """
    Clean a line by removing script formatting marks, page numbers, and copyright notices.
    """
    # Patterns to remove
    patterns = [
        r'SALMON #\d+\s+XX/XX/\d+\s+\d+\.?',  # Page headers
        r'© \d+ MARVEL STUDIOS, INC\.',  # Copyright notice
        r'NO DUPLICATION WITHOUT MARVEL’S WRITTEN CONSENT.',  # Copyright warning
        r'\(CONTINUED\)',  # Continued marks
        r'CONTINUED:',  # Continued marks at start of page
        r'\(MORE\)',  # More marks
        r'^\d+\s*$',  # Standalone page numbers
        r'\d+\s+\d+$',  # Page transition numbers (like "17 17")
        r'^\s*\d+\s+\d+\s*$',  # Page numbers on their own line
    ]
    
    # Apply each pattern
    cleaned_line = line
    for pattern in patterns:
        cleaned_line = re.sub(pattern, '', cleaned_line, flags=re.IGNORECASE)
    
    return cleaned_line.strip()

def is_valid_dialogue_line(line):
    """
    Check if a line is valid dialogue (not a scene heading or other script markup).
    """
    # Patterns that indicate non-dialogue lines
    non_dialogue_patterns = [
        r'^INT\.',
        r'^EXT\.',
        r'^ANGLE',
        r'^CUT TO:',
        r'^FLASH TO:',
        r'^\d+\s*$',  # Page numbers
        r'^\s*\d+\s+\d+\s*$',  # Page transition numbers
        r'^FADE IN:',
        r'^FADE OUT:',
        r'^DISSOLVE TO:',
        r'^SMASH CUT TO:',
        r'^SCENE \d+',
    ]
    
    # Check if line matches any non-dialogue pattern
    for pattern in non_dialogue_patterns:
        if re.match(pattern, line.strip(), re.IGNORECASE):
            return False
    
    return True

def extract_dialogues(pdf_path, characters):
    """
    Extract dialogues for specified characters from a Marvel script PDF.
    Returns a dictionary with character names as keys and their dialogues as values.
    """
    character_dialogues = {char.upper(): [] for char in characters}
    reader = PdfReader(pdf_path)
    
    current_character = None
    current_dialogue = []
    
    for page in reader.pages:
        text = page.extract_text()
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = clean_line(lines[i])
            
            if not line:  # Skip empty lines
                i += 1
                continue
                
            # Check for character name (in caps) followed by dialogue
            character_match = re.match(r'^([A-Z][A-Z\s]+)(?:\s*\([^)]+\))?\s*$', line)
            
            if character_match:
                # Save previous dialogue if exists
                if current_character and current_dialogue:
                    if current_character in character_dialogues:
                        cleaned_dialogue = ' '.join(current_dialogue).strip()
                        if cleaned_dialogue:  # Only add non-empty dialogues
                            character_dialogues[current_character].append(cleaned_dialogue)
                    current_dialogue = []
                
                # Get new character name
                current_character = character_match.group(1).strip()
                
                # Move to next line which should be dialogue
                i += 1
                if i < len(lines):
                    dialogue_line = clean_line(lines[i])
                    if dialogue_line and is_valid_dialogue_line(dialogue_line):
                        current_dialogue.append(dialogue_line)
            
            # Handle continued dialogue
            elif current_character and line.endswith("(cont'd)"):
                character_name = line.replace("(cont'd)", "").strip()
                if character_name.upper() == current_character:
                    i += 1
                    if i < len(lines):
                        dialogue_line = clean_line(lines[i])
                        if dialogue_line and is_valid_dialogue_line(dialogue_line):
                            current_dialogue.append(dialogue_line)
            
            # Add to current dialogue if we're in the middle of one
            elif current_character and current_dialogue and line:
                if is_valid_dialogue_line(line):
                    current_dialogue.append(line)
                    if line.strip().endswith('...'):  # If line ends with ..., end the dialogue block
                        if current_character in character_dialogues:
                            cleaned_dialogue = ' '.join(current_dialogue).strip()
                            if cleaned_dialogue:
                                character_dialogues[current_character].append(cleaned_dialogue)
                        current_dialogue = []
                        current_character = None
                else:
                    # This is a non-dialogue line, so save current dialogue
                    if current_character in character_dialogues:
                        cleaned_dialogue = ' '.join(current_dialogue).strip()
                        if cleaned_dialogue:
                            character_dialogues[current_character].append(cleaned_dialogue)
                    current_dialogue = []
                    current_character = None
            
            i += 1
    
    # Save any remaining dialogue
    if current_character and current_dialogue:
        if current_character in character_dialogues:
            cleaned_dialogue = ' '.join(current_dialogue).strip()
            if cleaned_dialogue:
                character_dialogues[current_character].append(cleaned_dialogue)
    
    return character_dialogues

def save_dialogues(character_dialogues, output_dir):
    """
    Save extracted dialogues to individual text files in the specified directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for character, dialogues in character_dialogues.items():
        if dialogues:  # Only create file if character has dialogues
            filename = os.path.join(output_dir, f"{character.lower()}_dialogues.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                for dialogue in dialogues:
                    f.write(f"{dialogue}\n\n")  # Just write the dialogue with double spacing

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py input.pdf character1 character2 ...")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    characters = sys.argv[2:]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
    
    try:
        # Extract dialogues
        character_dialogues = extract_dialogues(pdf_path, characters)
        
        # Create output directory based on PDF filename
        output_dir = os.path.splitext(pdf_path)[0] + "_dialogues"
        
        # Save dialogues to files
        save_dialogues(character_dialogues, output_dir)
        
        print(f"Dialogues extracted successfully to '{output_dir}' directory.")
        
        # Print summary
        for character in characters:
            char_upper = character.upper()
            count = len(character_dialogues.get(char_upper, []))
            print(f"{character}: {count} dialogues extracted")
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()